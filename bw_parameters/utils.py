# -*- coding: utf-8 -*-
import ast

import asteval


def _get_existing_symbols():
    interpreter = asteval.Interpreter()
    return set(interpreter.symtable)


EXISTING_SYMBOLS = _get_existing_symbols()


def get_symbols(expression):
    interpreter = asteval.Interpreter()
    nf = asteval.NameFinder()
    nf.generic_visit(interpreter.parse(expression))
    return set(nf.names).difference(EXISTING_SYMBOLS)


def isidentifier(ident):
    """ Determines if given string is valid Python identifier.

    Stolen from http://stackoverflow.com/questions/12700893/how-to-check-if-a-string-is-a-valid-python-identifier-including-keyword-check
    """

    if not isinstance(ident, str):
        raise TypeError('expected str, but got {!r}'.format(type(ident)))

    # Resulting AST of simple identifier is <Module [<Expr <Name "foo">>]>
    try:
        root = ast.parse(ident)
    except SyntaxError:
        return False

    if (not isinstance(root, ast.Module)
        or len(root.body) != 1
        or not isinstance(root.body[0], ast.Expr)
        or not isinstance(root.body[0].value, ast.Name)
        or root.body[0].value.id != ident):
        return False
    return True