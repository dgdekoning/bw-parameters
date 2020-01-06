# -*- coding: utf-8 -*-
from numbers import Number
from pprint import pformat

from asteval import Interpreter
import numpy as np
from stats_arrays import uncertainty_choices

from .errors import *
from .utils import get_symbols, EXISTING_SYMBOLS, isidentifier


MC_ERROR_TEXT = """Formula returned array of wrong shape:
Name: {}
Formula: {}
Expected shape: {}
Returned shape: {}"""


class ParameterSet(object):
    def __init__(self, params: dict, global_params: dict = None):
        self.params = params
        self.global_params = global_params or {}
        self.basic_validation()
        self.references = self.get_references()
        for name, references in self.references.items():
            if name in references:
                raise SelfReference(
                    "Formula for parameter {} references itself".format(name)
                )

        self.order = self.get_order()

    def get_order(self):
        """ Get a list of parameter name in an order that they can be safely evaluated.
        """
        order = []
        seen = set()
        refs = self.references.copy()

        while refs:
            last_iteration = set(refs.keys())
            for k, v in refs.items():
                if not v.difference(seen):
                    seen.add(k)
                    order.append(k)
                    refs.pop(k)
                    break
            if not last_iteration.difference(set(refs.keys())):
                seen_lower_case = {x.lower() for x in seen}
                # Iterate over all remaining references,
                # and see if references would match if lower cased
                wrong_case = [
                    (k, v)
                    for k, v in refs.items()
                    if not {x.lower() for x in v}.difference(seen_lower_case)
                ]
                if wrong_case:
                    raise CapitalizationError((
                        "Possible errors in upper/lower case letters for some parameters.\n"
                        "Unmatched references:\n{}\nMatched references:\n{}"
                        ).format(pformat(refs, indent=2), pformat(sorted(seen), indent=2))
                    )
                raise ParameterError(("Undefined or circular references for the following:"
                                      "\n{}\nExisting references:\n{}").format(
                                      pformat(refs, indent=2),
                                      pformat(sorted(order), indent=2)
                ))

        return order

    def get_references(self) -> dict:
        """ Create dictionary of parameter references.
        """
        refs = {
            key: get_symbols(value["formula"]) if "formula" in value else set()
            for key, value in self.params.items()
        }
        refs.update(dict.fromkeys(self.global_params, set()))
        return refs

    def basic_validation(self):
        """ Basic validation needed to build ``references`` and ``order``.
        """
        if not isinstance(self.params, dict):
            raise ValueError("Parameters are not a dictionary")
        if not isinstance(self.global_params, dict):
            raise ValueError("Global parameters are not a dictionary")
        for key, value in self.params.items():
            if not isinstance(value, dict):
                raise ValueError("Parameter value {} is not a dictionary".format(key))
            elif not (isinstance(value.get("amount"), (Number, np.ndarray)) or
                      isinstance(value.get("formula"), str)):
                raise ValueError(("Parameter {} must have either ``amount`` "
                                  "or ``formula`` field").format(key))
            elif not isidentifier(key):
                raise ValueError(
                    "Parameter label {} not a valid Python name".format(key)
                )
            elif key in EXISTING_SYMBOLS:
                raise DuplicateName(
                    "Parameter name {} is a built-in symbol".format(key)
                )
        for key, value in self.global_params.items():
            if not isinstance(value, (Number, np.ndarray)):
                raise ValueError(("Global parameter {} does not have a "
                                  "numeric value: {}").format(key, value))
            elif not isidentifier(key):
                raise ValueError(("Global parameter label {} not a valid "
                                  "Python name").format(key))

    def evaluate(self) -> dict:
        """ Evaluate each formula. Returns dictionary of parameter names and values.
        """
        interpreter = Interpreter()
        result = {}
        for key in self.order:
            if key in self.global_params:
                interpreter.symtable[key] = result[key] = self.global_params[key]
            elif self.params[key].get("formula"):
                value = interpreter(self.params[key]["formula"])
                interpreter.symtable[key] = result[key] = value
            elif "amount" in self.params[key]:
                interpreter.symtable[key] = result[key] = self.params[key]["amount"]
            else:
                raise ValueError("No suitable formula or static amount found "
                                 "in {}".format(key))
        return result

    def evaluate_and_set_amount_field(self) -> dict:
        """ Evaluate each formula. Updates the ``amount`` field of each parameter.
        """
        result = self.evaluate()
        for key, value in self.params.items():
            value["amount"] = result[key]
        return result

    def evaluate_monte_carlo(self, iterations=1000) -> dict:
        """ Evaluate each formula using Monte Carlo and variable uncertainty data, if present.

        Formulas **must** return a one-dimensional array, or ``BroadcastingError`` is raised.

        Returns dictionary of ``{parameter name: numpy array}``.
        """
        interpreter = Interpreter()
        result = {}

        def get_rng_sample(obj):
            if isinstance(obj, np.ndarray):
                # Already a Monte Carlo sample
                return obj
            if "uncertainty_type" not in obj:
                if "uncertainty type" not in obj:
                    obj = obj.copy()
                    obj["uncertainty_type"] = 0
                    obj["loc"] = obj["amount"]
                else:
                    obj["uncertainty_type"] = obj["uncertainty type"]
            kls = uncertainty_choices[obj["uncertainty_type"]]
            return kls.bounded_random_variables(kls.from_dicts(obj), iterations).ravel()

        def fix_shape(array):
            if array.shape in {(1, iterations), (iterations, 1)}:
                return array.reshape((iterations,))
            else:
                return array

        for key in self.order:
            if key in self.global_params:
                interpreter.symtable[key] = result[key] = get_rng_sample(self.global_params[key])
            elif "formula" in self.params[key]:
                sample = fix_shape(interpreter(self.params[key]["formula"]))
                if sample.shape != (iterations,):
                    raise BroadcastingError(MC_ERROR_TEXT.format(
                        key, self.params[key]["formula"], (iterations,), sample.shape)
                    )
                interpreter.symtable[key] = result[key] = sample
            else:
                interpreter.symtable[key] = result[key] = get_rng_sample(self.params[key])
        return result

    def __call__(self, ds=None):
        """ Evaluate each formula, and update ``exchanges`` if they reference a ``parameter`` name.
        """
        if ds is None:
            return self.evaluate_and_set_amount_field()

        self.evaluate_and_set_amount_field()

        # Evaluate formulas in exchanges
        interpreter = self.get_interpreter()
        for obj in ds:
            if "formula" in obj and "amount" not in obj:
                obj["amount"] = interpreter(obj["formula"])

        # Changes in-place, but return anyway
        return ds

    def get_interpreter(self, evaluate_first=True):
        """ Get a prepopulated instance of ``asteval.Interpreter``

        Global and local symbol names and values have been included.
        """
        if evaluate_first:
            self.evaluate_and_set_amount_field()

        interpreter = Interpreter()
        for key, value in self.global_params.items():
            interpreter.symtable[key] = value
        for key, value in self.params.items():
            interpreter.symtable[key] = value["amount"]

        return interpreter
