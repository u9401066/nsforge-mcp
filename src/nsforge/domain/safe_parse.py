"""Allowlisted parsing for untrusted mathematical expressions.

NSForge accepts expression strings from MCP clients.  SymPy's convenient
``parse_expr``/``sympify`` helpers execute generated Python with ``eval`` and
therefore are not an acceptable trust boundary.  This module tokenises the
small mathematical language NSForge supports, asks SymPy only to perform its
*textual token transformations*, validates the resulting Python AST, and then
constructs SymPy objects by walking that AST.  Input text is never executed.

The cheap complexity checks remain a first line of defence against symbolic
denial of service.  Expensive symbolic operations still need a process-level
deadline/resource budget; parsing safely does not make arbitrary algebra cheap.
"""

from __future__ import annotations

import ast
import io
import keyword
import re
import token
import tokenize
from dataclasses import dataclass
from typing import Any

import sympy as sp
from sympy.parsing.sympy_parser import (
    auto_number,
    auto_symbol,
    convert_xor,
    factorial_notation,
    implicit_multiplication_application,
    repeated_decimals,
    stringify_expr,
)

MAX_LENGTH = 4000  # characters
MAX_DEPTH = 100  # bracket nesting depth
MAX_DIGITS = 15  # length of a single integer literal (physical constants are < 15)
MAX_POWERS = 50  # number of ** operators
MAX_AST_NODES = 4096
MAX_LITERAL_EXPONENT = 10_000
MAX_EAGER_INTEGER_ARGUMENT = 1_000
MAX_POLYGAMMA_INTEGER_ARGUMENT = 128

_EAGER_SPECIAL_FUNCTIONS = frozenset(
    {
        "factorial",
        "factorial2",
        "binomial",
        "gamma",
        "beta",
        "digamma",
        "polygamma",
        "lowergamma",
        "uppergamma",
    }
)

# a**b**c — chained exponentiation grows hyper-exponentially (e.g. 9**9**9).
_POWER_TOWER = re.compile(r"\*\*\s*[\w.]+\s*\*\*")
_BIG_INT = re.compile(rf"\d{{{MAX_DIGITS + 1},}}")
_BIG_FACTORIAL = re.compile(r"\d{4,}\s*!")
_BARE_EQUAL = re.compile(r"(?<![<>=!])=(?!=)")
_OPEN_TO_CLOSE = {"(": ")", "[": "]", "{": "}"}
_CLOSE_TO_OPEN = {value: key for key, value in _OPEN_TO_CLOSE.items()}

# ``lambda_notation`` is deliberately absent.  These transformations only
# rewrite token streams; unlike parse_expr they never compile/evaluate input.
ALLOWLIST_TRANSFORMATIONS = (
    auto_symbol,
    repeated_decimals,
    auto_number,
    factorial_notation,
    implicit_multiplication_application,
    convert_xor,
)

# Deterministic mathematical constructors/functions accepted at the expression
# boundary.  There is intentionally no Function/Symbol constructor, dynamic
# lookup, callable from local_dict, or attribute access.
_SAFE_CALLABLES: dict[str, Any] = {
    # Numeric constructors are also emitted by SymPy's textual transformations.
    "Integer": sp.Integer,
    "Float": sp.Float,
    "Rational": sp.Rational,
    # Elementary functions.
    "Abs": sp.Abs,
    "sign": sp.sign,
    "sqrt": sp.sqrt,
    "root": sp.root,
    "exp": sp.exp,
    "log": sp.log,
    "ln": sp.log,
    "floor": sp.floor,
    "ceiling": sp.ceiling,
    "Min": sp.Min,
    "Max": sp.Max,
    "Mod": sp.Mod,
    # Trigonometric and hyperbolic functions.
    "sin": sp.sin,
    "cos": sp.cos,
    "tan": sp.tan,
    "cot": sp.cot,
    "sec": sp.sec,
    "csc": sp.csc,
    "asin": sp.asin,
    "acos": sp.acos,
    "atan": sp.atan,
    "acot": sp.acot,
    "asec": sp.asec,
    "acsc": sp.acsc,
    "sinh": sp.sinh,
    "cosh": sp.cosh,
    "tanh": sp.tanh,
    "coth": sp.coth,
    "sech": sp.sech,
    "csch": sp.csch,
    "asinh": sp.asinh,
    "acosh": sp.acosh,
    "atanh": sp.atanh,
    "acoth": sp.acoth,
    "asech": sp.asech,
    "acsch": sp.acsch,
    # Combinatorial and special functions used by NSForge's scientific tools.
    "factorial": sp.factorial,
    "factorial2": sp.factorial2,
    "binomial": sp.binomial,
    "gamma": sp.gamma,
    "beta": sp.beta,
    "digamma": sp.digamma,
    "polygamma": sp.polygamma,
    "lowergamma": sp.lowergamma,
    "uppergamma": sp.uppergamma,
    "erf": sp.erf,
    "erfc": sp.erfc,
    "erfi": sp.erfi,
    "sinc": sp.sinc,
    "Heaviside": sp.Heaviside,
    "DiracDelta": sp.DiracDelta,
    # Declarative symbolic forms.  These construct expressions; they do not run
    # arbitrary user-selected functions.
    "Eq": sp.Eq,
    "Ne": sp.Ne,
    "Lt": sp.Lt,
    "Le": sp.Le,
    "Gt": sp.Gt,
    "Ge": sp.Ge,
    "Piecewise": sp.Piecewise,
    "Integral": sp.Integral,
    "Derivative": sp.Derivative,
    "Sum": sp.Sum,
    "Product": sp.Product,
    "Limit": sp.Limit,
    "Matrix": sp.ImmutableMatrix,
    "ImmutableMatrix": sp.ImmutableMatrix,
}

_SAFE_CONSTANTS: dict[str, Any] = {
    "pi": sp.pi,
    "E": sp.E,
    "I": sp.I,
    "oo": sp.oo,
    "zoo": sp.zoo,
    "nan": sp.nan,
    "EulerGamma": sp.EulerGamma,
    "GoldenRatio": sp.GoldenRatio,
    "True": True,
    "False": False,
}

# Existing public behavior includes f(x).  These few conventional symbolic
# functions are server-defined and constructed without dynamic name lookup.
_SAFE_SYMBOLIC_FUNCTIONS: dict[str, Any] = {name: sp.Function(name) for name in ("f", "g", "h")}

ALLOWED_FUNCTION_NAMES = frozenset(_SAFE_CALLABLES) | frozenset(_SAFE_SYMBOLIC_FUNCTIONS)
ALLOWED_CONSTANT_NAMES = frozenset(_SAFE_CONSTANTS)

# Function / constant names that must not be treated as free symbols when
# scanning expression strings in the orchestrator and suggester.  Keep the
# historical set stable for ambiguous scientific symbols such as gamma/beta.
SYMPY_RESERVED_NAMES = frozenset(
    {
        "exp",
        "log",
        "ln",
        "sqrt",
        "Abs",
        "sin",
        "cos",
        "tan",
        "cot",
        "sec",
        "csc",
        "asin",
        "acos",
        "atan",
        "sinh",
        "cosh",
        "tanh",
        "pi",
        "E",
        "I",
        "oo",
    }
)


class UnsafeExpressionError(ValueError):
    """Raised when input is outside NSForge's mathematical expression grammar."""


def check_expression_safety(text: str) -> str | None:
    """Return a rejection reason for unsafe/over-budget input, otherwise ``None``."""

    return _rejection_reason(text, check_complexity=True)


def parse_expression_allowlisted(
    text: str,
    *,
    local_dict: dict[str, Any] | None = None,
    evaluate: bool = True,
    check_complexity: bool = True,
) -> Any:
    """Construct a SymPy expression from the allowlisted grammar without ``eval``.

    A single bare ``=`` is accepted as equation shorthand and becomes ``Eq``.
    ``local_dict`` may provide pre-constructed SymPy symbols (for assumptions),
    but callables and arbitrary Python values are rejected.
    """

    reason = _rejection_reason(text, check_complexity=check_complexity)
    if reason is not None:
        raise UnsafeExpressionError(reason)

    equation_parts = _BARE_EQUAL.split(text)
    if len(equation_parts) > 2:
        raise UnsafeExpressionError("equation must contain at most one '='")
    if len(equation_parts) == 2:
        left_text, right_text = (part.strip() for part in equation_parts)
        if not left_text or not right_text:
            raise UnsafeExpressionError("both sides of an equation are required")
        left = _parse_one(left_text, local_dict=local_dict, evaluate=evaluate)
        right = _parse_one(right_text, local_dict=local_dict, evaluate=evaluate)
        return sp.Eq(left, right, evaluate=evaluate)

    return _parse_one(text, local_dict=local_dict, evaluate=evaluate)


def _rejection_reason(text: str, *, check_complexity: bool) -> str | None:
    if not isinstance(text, str):
        return "expression must be a string"
    if not text.strip():
        return "expression must not be empty"
    if check_complexity and len(text) > MAX_LENGTH:
        return f"expression too long ({len(text)} > {MAX_LENGTH} chars)"

    stack: list[str] = []
    max_depth = 0
    for char in text:
        if char in _OPEN_TO_CLOSE:
            stack.append(char)
            max_depth = max(max_depth, len(stack))
        elif char in _CLOSE_TO_OPEN:
            if not stack or stack.pop() != _CLOSE_TO_OPEN[char]:
                return "expression has unmatched or misordered brackets"
    if stack:
        return "expression has unmatched or misordered brackets"
    if check_complexity and max_depth > MAX_DEPTH:
        return f"expression nesting too deep ({max_depth} > {MAX_DEPTH})"

    if check_complexity and _POWER_TOWER.search(text):
        return "chained exponentiation (power tower) is not allowed"
    if check_complexity and text.count("**") > MAX_POWERS:
        return f"too many exponentiations ({text.count('**')} > {MAX_POWERS})"
    if check_complexity and _BIG_INT.search(text):
        return f"integer literal too large (> {MAX_DIGITS} digits)"
    if check_complexity and _BIG_FACTORIAL.search(text):
        return "factorial of a large literal is not allowed"

    try:
        tokens = _meaningful_tokens(text)
    except (IndentationError, tokenize.TokenError) as exc:
        return f"invalid expression tokens: {exc}"

    for index, item in enumerate(tokens):
        value = item.string
        if item.type == token.STRING:
            return "string literals are not allowed in mathematical expressions"
        if item.type == token.ERRORTOKEN:
            return f"unsupported token {value!r}"
        if item.type == token.NAME:
            if "__" in value:
                return "dunder names are not allowed"
            if keyword.iskeyword(value) and value not in {"True", "False"}:
                return f"Python keyword {value!r} is not allowed"
            next_value = tokens[index + 1].string if index + 1 < len(tokens) else ""
            if next_value == "(" and value not in ALLOWED_FUNCTION_NAMES:
                return f"function {value!r} is not allowlisted"
        if item.type == token.OP and value in {".", ";", ":", "@", ":=", "->"}:
            return f"operator {value!r} is not allowed"
    return None


def _meaningful_tokens(text: str) -> list[tokenize.TokenInfo]:
    ignored = {
        token.ENDMARKER,
        token.NEWLINE,
        tokenize.NL,
        token.INDENT,
        token.DEDENT,
        tokenize.ENCODING,
    }
    tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
    return [item for item in tokens if item.type not in ignored]


def _parse_one(
    text: str,
    *,
    local_dict: dict[str, Any] | None,
    evaluate: bool,
) -> Any:
    parser_locals = _safe_locals(text, local_dict)
    transform_globals = {**_SAFE_CALLABLES, **_SAFE_CONSTANTS}
    transformed = stringify_expr(
        text.strip(), parser_locals.copy(), transform_globals, ALLOWLIST_TRANSFORMATIONS
    )
    try:
        tree = ast.parse(transformed, mode="eval")
    except SyntaxError as exc:
        raise UnsafeExpressionError(f"invalid mathematical syntax: {exc.msg}") from exc

    node_count = sum(1 for _ in ast.walk(tree))
    if node_count > MAX_AST_NODES:
        raise UnsafeExpressionError(
            f"expression syntax tree too large ({node_count} > {MAX_AST_NODES} nodes)"
        )
    evaluator = _AllowlistAstEvaluator(parser_locals, evaluate=evaluate)
    return evaluator.visit(tree.body)


def _safe_locals(text: str, supplied: dict[str, Any] | None) -> dict[str, Any]:
    result: dict[str, Any] = {}
    if supplied:
        for name, value in supplied.items():
            if not name.isidentifier() or "__" in name:
                raise UnsafeExpressionError(f"invalid local symbol name {name!r}")
            if callable(value) or not isinstance(value, (sp.Basic, sp.MatrixBase)):
                raise UnsafeExpressionError(
                    f"local {name!r} must be a pre-constructed SymPy value, not executable code"
                )
            result[name] = value

    tokens = _meaningful_tokens(text)
    direct_calls = {
        item.string
        for index, item in enumerate(tokens[:-1])
        if item.type == token.NAME and tokens[index + 1].string == "("
    }
    for item in tokens:
        if item.type != token.NAME:
            continue
        name = item.string
        if name in result or name in _SAFE_CONSTANTS:
            continue
        if name in _SAFE_SYMBOLIC_FUNCTIONS and name in direct_calls:
            result[name] = _SAFE_SYMBOLIC_FUNCTIONS[name]
        elif name in _SAFE_CALLABLES and name in direct_calls:
            continue
        elif name in _SAFE_CALLABLES and name not in {"gamma", "beta"}:
            # Preserve familiar implicit function application, e.g. ``sin x``.
            continue
        elif not keyword.iskeyword(name):
            result[name] = sp.Symbol(name)
    return result


@dataclass(slots=True)
class _AllowlistAstEvaluator:
    locals: dict[str, Any]
    evaluate: bool

    def visit(self, node: ast.AST) -> Any:
        method = getattr(self, f"_visit_{type(node).__name__}", None)
        if method is None:
            raise UnsafeExpressionError(
                f"syntax {type(node).__name__} is not allowed in mathematical expressions"
            )
        return method(node)

    def _visit_Constant(self, node: ast.Constant) -> Any:
        value = node.value
        if isinstance(value, (bool, int, float, str)):
            return value
        raise UnsafeExpressionError(f"literal {type(value).__name__} is not allowed")

    def _visit_Name(self, node: ast.Name) -> Any:
        if node.id in self.locals:
            return self.locals[node.id]
        if node.id in _SAFE_CONSTANTS:
            return _SAFE_CONSTANTS[node.id]
        # A callable is only meaningful as the callee of an approved Call node.
        if node.id in _SAFE_CALLABLES or node.id in _SAFE_SYMBOLIC_FUNCTIONS:
            return (_SAFE_CALLABLES | _SAFE_SYMBOLIC_FUNCTIONS)[node.id]
        raise UnsafeExpressionError(f"name {node.id!r} is not allowlisted")

    def _visit_List(self, node: ast.List) -> list[Any]:
        return [self.visit(item) for item in node.elts]

    def _visit_Tuple(self, node: ast.Tuple) -> tuple[Any, ...]:
        return tuple(self.visit(item) for item in node.elts)

    def _visit_UnaryOp(self, node: ast.UnaryOp) -> Any:
        operand = self.visit(node.operand)
        if isinstance(node.op, ast.UAdd):
            return operand
        if isinstance(node.op, ast.USub):
            return sp.Mul(sp.Integer(-1), operand, evaluate=self.evaluate)
        if isinstance(node.op, ast.Invert):
            return sp.Not(operand)
        raise UnsafeExpressionError(f"unary operator {type(node.op).__name__} is not allowed")

    def _visit_BinOp(self, node: ast.BinOp) -> Any:
        left = self.visit(node.left)
        right = self.visit(node.right)
        if isinstance(node.op, ast.Add):
            return sp.Add(left, right, evaluate=self.evaluate)
        if isinstance(node.op, ast.Sub):
            negative = sp.Mul(sp.Integer(-1), right, evaluate=self.evaluate)
            return sp.Add(left, negative, evaluate=self.evaluate)
        if isinstance(node.op, ast.Mult):
            return sp.Mul(left, right, evaluate=self.evaluate)
        if isinstance(node.op, ast.Div):
            reciprocal = sp.Pow(right, sp.Integer(-1), evaluate=self.evaluate)
            return sp.Mul(left, reciprocal, evaluate=self.evaluate)
        if isinstance(node.op, ast.Pow):
            if isinstance(right, int | sp.Integer) and abs(int(right)) > MAX_LITERAL_EXPONENT:
                raise UnsafeExpressionError(
                    "literal exponent exceeds the eager-construction budget "
                    f"({abs(int(right))} > {MAX_LITERAL_EXPONENT})"
                )
            return sp.Pow(left, right, evaluate=self.evaluate)
        if isinstance(node.op, ast.Mod):
            return sp.Mod(left, right, evaluate=self.evaluate)
        if isinstance(node.op, ast.BitAnd):
            return sp.And(left, right)
        if isinstance(node.op, ast.BitOr):
            return sp.Or(left, right)
        raise UnsafeExpressionError(f"binary operator {type(node.op).__name__} is not allowed")

    def _visit_Compare(self, node: ast.Compare) -> Any:
        if len(node.ops) != 1 or len(node.comparators) != 1:
            raise UnsafeExpressionError("chained comparisons are not allowed")
        left = self.visit(node.left)
        right = self.visit(node.comparators[0])
        operation = node.ops[0]
        if isinstance(operation, ast.Eq):
            return sp.Eq(left, right, evaluate=self.evaluate)
        if isinstance(operation, ast.NotEq):
            return sp.Ne(left, right, evaluate=self.evaluate)
        if isinstance(operation, ast.Lt):
            return sp.Lt(left, right, evaluate=self.evaluate)
        if isinstance(operation, ast.LtE):
            return sp.Le(left, right, evaluate=self.evaluate)
        if isinstance(operation, ast.Gt):
            return sp.Gt(left, right, evaluate=self.evaluate)
        if isinstance(operation, ast.GtE):
            return sp.Ge(left, right, evaluate=self.evaluate)
        raise UnsafeExpressionError(f"comparison {type(operation).__name__} is not allowed")

    def _visit_Call(self, node: ast.Call) -> Any:
        if not isinstance(node.func, ast.Name):
            raise UnsafeExpressionError(
                "only direct calls to allowlisted math functions are allowed"
            )
        if node.keywords:
            raise UnsafeExpressionError("keyword arguments are not allowed in expressions")
        name = node.func.id
        callable_value = (_SAFE_CALLABLES | _SAFE_SYMBOLIC_FUNCTIONS).get(name)
        if callable_value is None:
            raise UnsafeExpressionError(f"function {name!r} is not allowlisted")
        arguments = [self.visit(argument) for argument in node.args]
        if name in _EAGER_SPECIAL_FUNCTIONS:
            integers = [
                abs(int(argument))
                for argument in arguments
                if isinstance(argument, int | sp.Integer)
            ]
            limit = (
                MAX_POLYGAMMA_INTEGER_ARGUMENT
                if name == "polygamma"
                else MAX_EAGER_INTEGER_ARGUMENT
            )
            if integers and max(integers) > limit:
                raise UnsafeExpressionError(
                    f"integer argument for {name} exceeds the eager-construction budget "
                    f"({max(integers)} > {limit})"
                )
        try:
            return callable_value(*arguments)
        except (TypeError, ValueError, IndexError) as exc:
            raise UnsafeExpressionError(f"invalid arguments for {name}: {exc}") from exc
