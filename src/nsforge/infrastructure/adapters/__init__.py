"""
Formula Adapters - 外部公式來源適配器

提供對多種公式來源的統一介面：
- Wikidata: 跨領域公式 (SPARQL) - 精確檢索
- BioModels: 藥學/PK-PD 模型 (SBML) - 精確檢索
- SciPy: 物理常數 (CODATA)

設計原則：
- 直接精確檢索，不使用 RAG（避免公式錯誤）
- 統一的 FormulaInfo 返回格式
- 延遲導入網路適配器
"""

from .base import BaseAdapter, FormulaInfo
from .scipy_constants import ScipyConstantsAdapter

__all__ = [
    "BaseAdapter",
    "FormulaInfo",
    "ScipyConstantsAdapter",
    "get_wikidata_adapter",
    "get_biomodels_adapter",
]


def get_wikidata_adapter():
    """獲取 Wikidata 適配器（延遲導入，需要網路）"""
    from .wikidata_formulas import WikidataFormulaAdapter
    return WikidataFormulaAdapter()


def get_biomodels_adapter():
    """獲取 BioModels 適配器（延遲導入，需要網路）"""
    from .biomodels import BioModelsAdapter
    return BioModelsAdapter()
