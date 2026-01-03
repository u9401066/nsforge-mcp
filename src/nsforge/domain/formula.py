"""
Formula - 標準公式介面

支援多種格式輸入，統一轉換為內部表示。
錯誤時返回詳細說明。

The "Forge" in NSForge means we CREATE new formulas through derivation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import sympy as sp
from sympy.parsing.latex import parse_latex
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)


class FormulaSource(Enum):
    """公式來源標記 - 學術溯源的關鍵"""

    USER_INPUT = "user_input"  # 用戶直接輸入
    TEXTBOOK = "textbook"  # 教科書公式
    SYMPY_BUILTIN = "sympy_builtin"  # SymPy 內建
    DERIVED = "derived"  # NSForge 推導產生
    EXTERNAL_MCP = "external_mcp"  # 來自其他 MCP（如 sympy-mcp）


class FormulaFormat(Enum):
    """支援的輸入格式"""

    SYMPY = "sympy"  # SymPy 字串: "C_0 * exp(-k*t)"
    LATEX = "latex"  # LaTeX: "C_0 e^{-kt}"
    PYTHON = "python"  # Python 表達式: "C_0 * math.exp(-k*t)"
    NATURAL = "natural"  # 自然語言（未來支援）
    DICT = "dict"  # 字典格式


@dataclass
class ParseError:
    """解析錯誤的詳細資訊"""

    error_type: str  # "syntax", "latex", "variable", "dimension"
    message: str
    position: int | None = None
    suggestion: str | None = None
    original_input: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": False,
            "error_type": self.error_type,
            "message": self.message,
            "position": self.position,
            "suggestion": self.suggestion,
            "original_input": self.original_input,
        }


@dataclass
class Variable:
    """公式中的變數"""

    name: str
    description: str = ""
    unit: str | None = None
    constraints: str | None = None  # "positive", "real", "integer"
    value: Any = None  # 如果已知數值

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "unit": self.unit,
            "constraints": self.constraints,
            "value": self.value,
        }


@dataclass
class Formula:
    """
    標準公式介面

    統一表示來自任何格式的公式，包含完整元資料。
    """

    # 核心內容
    id: str
    expression: sp.Expr | sp.Equality  # SymPy 表達式
    variables: dict[str, Variable] = field(default_factory=dict)

    # 來源追蹤（學術價值）
    source: FormulaSource = FormulaSource.USER_INPUT
    source_detail: str = ""  # 詳細來源（如 "sympy-mcp.arrhenius"）
    original_input: str = ""  # 原始輸入字串
    input_format: FormulaFormat = FormulaFormat.SYMPY

    # 元資料
    name: str = ""
    description: str = ""
    category: str = ""
    tags: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)

    # 時間戳
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def sympy_str(self) -> str:
        """SymPy 字串表示"""
        return str(self.expression)

    @property
    def latex(self) -> str:
        """LaTeX 表示"""
        result = sp.latex(self.expression)
        return str(result) if result else ""

    @property
    def symbol_names(self) -> set[str]:
        """所有符號名稱"""
        return {str(s) for s in self.expression.free_symbols}

    def to_dict(self) -> dict[str, Any]:
        """序列化為字典"""
        return {
            "id": self.id,
            "expression": self.sympy_str,
            "latex": self.latex,
            "variables": {k: v.to_dict() for k, v in self.variables.items()},
            "source": self.source.value,
            "source_detail": self.source_detail,
            "original_input": self.original_input,
            "input_format": self.input_format.value,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "tags": self.tags,
            "references": self.references,
            "created_at": self.created_at,
        }


class FormulaParser:
    """
    公式解析器

    支援多種格式輸入，統一轉換為 Formula 物件。
    錯誤時返回詳細的 ParseError。
    """

    # SymPy 解析轉換
    TRANSFORMATIONS = standard_transformations + (
        implicit_multiplication_application,
        convert_xor,
    )

    # 常見替換
    SYMBOL_REPLACEMENTS = {
        "θ": "theta",
        "Θ": "Theta",
        "α": "alpha",
        "β": "beta",
        "γ": "gamma",
        "δ": "delta",
        "Δ": "Delta",
        "ε": "epsilon",
        "λ": "lambda_",
        "μ": "mu",
        "π": "pi",
        "σ": "sigma",
        "τ": "tau",
        "ω": "omega",
        "Ω": "Omega",
        "∞": "oo",
        "√": "sqrt",
        "²": "**2",
        "³": "**3",
        "₀": "_0",
        "₁": "_1",
        "₂": "_2",
        "₃": "_3",
        "ₐ": "_a",
        "ₑ": "_e",
        "ᵣ": "_r",
    }

    @classmethod
    def parse(
        cls,
        input_data: str | dict[str, Any],
        formula_id: str,
        source: FormulaSource = FormulaSource.USER_INPUT,
        source_detail: str = "",
        **metadata: Any,
    ) -> Formula | ParseError:
        """
        解析公式輸入

        Args:
            input_data: 公式輸入（字串或字典）
            formula_id: 公式 ID
            source: 來源標記
            source_detail: 詳細來源資訊
            **metadata: 額外元資料（name, description, category, tags）

        Returns:
            Formula 或 ParseError
        """
        # 判斷輸入格式
        if isinstance(input_data, dict):
            return cls._parse_dict(input_data, formula_id, source, source_detail, **metadata)

        # 字串輸入 - 自動檢測格式
        input_str = str(input_data).strip()

        # 檢測是否為 LaTeX
        if cls._is_latex(input_str):
            return cls._parse_latex(input_str, formula_id, source, source_detail, **metadata)

        # 預設為 SymPy 格式
        return cls._parse_sympy(input_str, formula_id, source, source_detail, **metadata)

    @classmethod
    def _is_latex(cls, s: str) -> bool:
        """檢測是否為 LaTeX 格式"""
        latex_indicators = ["\\frac", "\\cdot", "\\times", "\\sqrt", "^{", "_{", "\\exp", "\\ln", "\\log"]
        return any(ind in s for ind in latex_indicators)

    @classmethod
    def _parse_sympy(
        cls,
        input_str: str,
        formula_id: str,
        source: FormulaSource,
        source_detail: str,
        **metadata: Any,
    ) -> Formula | ParseError:
        """解析 SymPy 格式"""
        original = input_str

        # 應用符號替換
        for old, new in cls.SYMBOL_REPLACEMENTS.items():
            input_str = input_str.replace(old, new)

        # 處理方程式（含 =）
        is_equation = "=" in input_str and input_str.count("=") == 1

        try:
            if is_equation:
                lhs, rhs = input_str.split("=")
                lhs_expr = parse_expr(lhs.strip(), transformations=cls.TRANSFORMATIONS)
                rhs_expr = parse_expr(rhs.strip(), transformations=cls.TRANSFORMATIONS)
                expr = sp.Eq(lhs_expr, rhs_expr)
            else:
                expr = parse_expr(input_str, transformations=cls.TRANSFORMATIONS)

            # 提取變數
            variables = cls._extract_variables(expr)

            return Formula(
                id=formula_id,
                expression=expr,
                variables=variables,
                source=source,
                source_detail=source_detail,
                original_input=original,
                input_format=FormulaFormat.SYMPY,
                **metadata,
            )

        except SyntaxError as e:
            return ParseError(
                error_type="syntax",
                message=f"Syntax error: {e}",
                suggestion="Check operator usage. Use * for multiplication, ** for power.",
                original_input=original,
            )
        except Exception as e:
            return ParseError(
                error_type="parse",
                message=f"Parse error: {e}",
                suggestion="Verify expression syntax. Example: 'C_0 * exp(-k*t)'",
                original_input=original,
            )

    @classmethod
    def _parse_latex(
        cls,
        input_str: str,
        formula_id: str,
        source: FormulaSource,
        source_detail: str,
        **metadata: Any,
    ) -> Formula | ParseError:
        """解析 LaTeX 格式"""
        original = input_str

        # 檢查括號平衡
        if input_str.count("{") != input_str.count("}"):
            return ParseError(
                error_type="latex",
                message="Unmatched braces in LaTeX",
                suggestion="Check if all { have matching }",
                original_input=original,
            )

        # 處理方程式
        is_equation = "=" in input_str

        try:
            if is_equation:
                parts = input_str.split("=")
                if len(parts) != 2:
                    return ParseError(
                        error_type="latex",
                        message="Multiple '=' found in equation",
                        suggestion="Equation should have exactly one '='",
                        original_input=original,
                    )
                lhs_expr = parse_latex(parts[0].strip())
                rhs_expr = parse_latex(parts[1].strip())
                expr = sp.Eq(lhs_expr, rhs_expr)
            else:
                expr = parse_latex(input_str)

            # 提取變數
            variables = cls._extract_variables(expr)

            return Formula(
                id=formula_id,
                expression=expr,
                variables=variables,
                source=source,
                source_detail=source_detail,
                original_input=original,
                input_format=FormulaFormat.LATEX,
                **metadata,
            )

        except Exception as e:
            return ParseError(
                error_type="latex",
                message=f"LaTeX parse error: {e}",
                suggestion="Check LaTeX syntax. Use \\frac{a}{b}, e^{x}, etc.",
                original_input=original,
            )

    @classmethod
    def _parse_dict(
        cls,
        data: dict[str, Any],
        formula_id: str,
        source: FormulaSource,
        source_detail: str,
        **metadata: Any,
    ) -> Formula | ParseError:
        """解析字典格式"""
        # 必須有 expression
        if "expression" not in data and "latex" not in data and "sympy" not in data:
            return ParseError(
                error_type="format",
                message="Missing expression in dict",
                suggestion="Provide 'expression', 'latex', or 'sympy' key",
                original_input=str(data),
            )

        # 取得表達式字串
        expr_str = data.get("expression") or data.get("sympy") or data.get("latex")

        # 確保 expr_str 是 str 類型
        if not isinstance(expr_str, str):
            return ParseError(
                error_type="syntax",
                message="Expression must be a string",
                suggestion="Dict format requires 'expression', 'sympy', or 'latex' key with string value",
                original_input=str(data)
            )

        # 解析表達式
        if data.get("latex") or cls._is_latex(expr_str):
            result = cls._parse_latex(expr_str, formula_id, source, source_detail)
        else:
            result = cls._parse_sympy(expr_str, formula_id, source, source_detail)

        if isinstance(result, ParseError):
            return result

        # 補充字典中的元資料
        if "name" in data:
            result.name = data["name"]
        if "description" in data:
            result.description = data["description"]
        if "category" in data:
            result.category = data["category"]
        if "tags" in data:
            result.tags = data["tags"]
        if "references" in data:
            result.references = data["references"]

        # 補充變數資訊
        if "variables" in data:
            for var_name, var_info in data["variables"].items():
                if var_name in result.variables and isinstance(var_info, dict):
                    result.variables[var_name].description = var_info.get("description", "")
                    result.variables[var_name].unit = var_info.get("unit")
                    result.variables[var_name].constraints = var_info.get("constraints")

        # 應用額外 metadata
        for key, value in metadata.items():
            if hasattr(result, key):
                setattr(result, key, value)

        return result

    @classmethod
    def _extract_variables(cls, expr: sp.Expr | sp.Equality) -> dict[str, Variable]:
        """從表達式提取變數"""
        symbols = expr.free_symbols
        variables = {}

        for sym in symbols:
            name = str(sym)
            variables[name] = Variable(
                name=name,
                description="",  # 待用戶補充
                unit=None,
                constraints=cls._infer_constraints(name),
            )

        return variables

    @classmethod
    def _infer_constraints(cls, name: str) -> str | None:
        """根據命名慣例推斷約束"""
        # 通常為正的變數
        positive_patterns = ["m", "M", "k", "K", "T", "V", "C", "R", "t", "tau", "omega"]
        if name in positive_patterns or name.startswith(tuple(positive_patterns)):
            return "positive"

        # 角度
        angle_patterns = ["theta", "phi", "psi", "alpha", "beta", "gamma"]
        if name in angle_patterns:
            return "real"

        return "real"
