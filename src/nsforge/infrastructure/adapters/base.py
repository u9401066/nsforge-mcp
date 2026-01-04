"""
Base Adapter - 公式適配器基類

定義所有公式來源適配器的統一介面。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from sympy import Expr


@dataclass
class FormulaInfo:
    """
    公式資訊的統一格式

    所有適配器都應返回此格式，確保上層可統一處理。
    """

    # 識別
    id: str                          # 唯一識別碼（如 Wikidata Q 號）
    name: str                        # 公式名稱

    # 數學表示
    expression: Expr | str           # SymPy 表達式或字串
    latex: str = ""                  # LaTeX 表示
    sympy_str: str = ""              # SymPy 字串表示

    # 變數定義
    variables: dict[str, dict[str, Any]] = field(default_factory=dict)
    # 格式: {"rho": {"description": "密度", "unit": "kg/m³", "type": "variable"}}

    # 元資料
    source: str = ""                 # 來源（"wikidata", "biomodels", "scipy"）
    category: str = ""               # 分類
    description: str = ""            # 描述
    tags: list[str] = field(default_factory=list)

    # 連結
    url: str = ""                    # 原始來源 URL
    references: list[str] = field(default_factory=list)

    # 額外資料（來源特定）
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """序列化為字典"""
        return {
            "id": self.id,
            "name": self.name,
            "expression": str(self.expression),
            "latex": self.latex,
            "sympy_str": self.sympy_str,
            "variables": self.variables,
            "source": self.source,
            "category": self.category,
            "description": self.description,
            "tags": self.tags,
            "url": self.url,
            "references": self.references,
            "extra": self.extra,
        }


class BaseAdapter(ABC):
    """
    公式適配器基類

    所有公式來源（Wikidata、BioModels、SciPy 等）都應繼承此類。
    """

    @property
    @abstractmethod
    def source_name(self) -> str:
        """適配器來源名稱"""
        ...

    @abstractmethod
    def search(self, query: str, limit: int = 10) -> list[FormulaInfo]:
        """
        搜尋公式

        Args:
            query: 搜尋關鍵字
            limit: 返回數量上限

        Returns:
            匹配的公式列表
        """
        ...

    @abstractmethod
    def get_formula(self, formula_id: str) -> FormulaInfo | None:
        """
        獲取單個公式詳情

        Args:
            formula_id: 公式識別碼

        Returns:
            公式資訊或 None
        """
        ...

    def list_categories(self) -> list[str]:
        """列出所有分類（可選實作）"""
        return []

    def list_formulas(self, category: str | None = None) -> list[str]:  # noqa: ARG002
        """列出公式 ID（可選實作）"""
        return []
