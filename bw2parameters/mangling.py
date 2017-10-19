import ast
from asteval.astutils import FROM_MATH, FROM_PY, FROM_NUMPY, NUMPY_RENAMES, NameFinder
from astunparse import unparse

BUILTINS = FROM_MATH + FROM_NUMPY + FROM_PY + tuple(NUMPY_RENAMES.keys())


class SubstituteName(NameFinder):
    """find all symbol names used by a parsed node"""

    def __init__(self, prefix, context=None):
        self.prefix = prefix + "__"
        self.builtins = BUILTINS
        if context:
            self.builtins += tuple(context)
        ast.NodeVisitor.__init__(self)

    def generic_visit(self, node):
        if node.__class__.__name__ == 'Name':
            if node.ctx.__class__ == ast.Load and node.id not in self.builtins:
                node.id = self.prefix + node.id
        ast.NodeVisitor.generic_visit(self, node)


def mangle_formula(string, prefix, context=None):
    """Add ``prefix`` to all variable names in formula ``string``, except those in ``context`` or builtin to Python, ``math``, or ``numpy``.

    Uses `asteval <https://newville.github.io/asteval/>`__ and `astunparse <http://astunparse.readthedocs.io/>`__.

    Returns the formula as a string.

    Example usage:

    ... code-block:: python

        >>> mangle_formula("log(foo * bar) + 7 / baz", "pre", ['bar'])
        '(log((pre__foo * bar)) + (7 / pre__baz))'

    """
    parsed = ast.parse(string)
    SubstituteName(prefix, context).visit(parsed)
    return unparse(parsed).strip()
