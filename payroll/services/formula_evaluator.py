"""
payroll/services/formula_evaluator.py

Evaluates SalaryComponent.formula strings like "BASIC * 0.08" or
"BASIC + HOUSING" safely.

This deliberately does NOT use Python's eval() or exec() — a formula
is user-editable text sitting in the database, and eval()-ing
arbitrary text from a database field is a code-execution
vulnerability waiting to happen (someone with SalaryComponent edit
access could otherwise write a formula that reads secrets, hits the
filesystem, or worse). Instead this walks a parsed AST and only
allows: numbers, named component-code lookups, +, -, *, /, unary
minus, and parentheses. Anything else raises FormulaError.
"""
import ast
import operator
from decimal import Decimal
from typing import Mapping


class FormulaError(Exception):
    """Raised when a formula is invalid or references an unknown component."""


_ALLOWED_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}
_ALLOWED_UNARYOPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def evaluate_formula(formula: str, values: Mapping[str, Decimal]) -> Decimal:
    """
    Evaluates `formula` using `values` as the available named
    component amounts (keyed by SalaryComponent.code, e.g. "BASIC").

    Raises FormulaError on any syntax outside the allowed grammar, or
    a reference to a component code not present in `values` (e.g. a
    component that hasn't been calculated yet in this payroll run —
    formulas may only reference components with a lower display_order).
    """
    try:
        tree = ast.parse(formula, mode="eval")
    except SyntaxError as exc:
        raise FormulaError(f"Invalid formula syntax: {formula!r}") from exc

    return Decimal(str(_eval_node(tree.body, values)))


def _eval_node(node, values: Mapping[str, Decimal]):
    if isinstance(node, ast.Expression):
        return _eval_node(node.body, values)

    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return Decimal(str(node.value))
        raise FormulaError(f"Unsupported constant in formula: {node.value!r}")

    if isinstance(node, ast.Name):
        code = node.id.upper()
        if code not in values:
            raise FormulaError(f"Formula references unknown or not-yet-calculated component: {code}")
        return values[code]

    if isinstance(node, ast.BinOp):
        op_func = _ALLOWED_BINOPS.get(type(node.op))
        if op_func is None:
            raise FormulaError(f"Operator not allowed in formulas: {type(node.op).__name__}")
        left = _eval_node(node.left, values)
        right = _eval_node(node.right, values)
        return op_func(left, right)

    if isinstance(node, ast.UnaryOp):
        op_func = _ALLOWED_UNARYOPS.get(type(node.op))
        if op_func is None:
            raise FormulaError(f"Unary operator not allowed: {type(node.op).__name__}")
        return op_func(_eval_node(node.operand, values))

    raise FormulaError(f"Unsupported expression in formula: {type(node).__name__}")
