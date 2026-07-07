"""
Formula Search Tools - 公式檢索 MCP 工具

提供對外部公式來源的統一查詢介面：
- Wikidata: 跨領域物理/化學/工程公式
- BioModels: 藥學/PK-PD 模型
- SciPy: 物理常數

這是 NSForge 「科學運算 Agent 核心大腦」的關鍵組件。
直接精確檢索，不使用 RAG（避免公式錯誤）。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass


def register_formula_tools(mcp: Any) -> None:
    """註冊公式檢索工具"""

    # ═══════════════════════════════════════════════════════════════════════
    # 統一搜尋介面
    # ═══════════════════════════════════════════════════════════════════════

    @mcp.tool()
    def formula_search(
        query: str,
        source: str = "all",
        domain: str | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        """
        搜尋公式（跨多個來源）

        這是科學運算 Agent 的核心工具，可從多個權威來源檢索準確的公式。
        使用直接精確檢索（非 RAG），確保公式正確性。

        Args:
            query: 搜尋關鍵字
                   - 英文名稱: "Reynolds number", "Arrhenius equation"
                   - 領域術語: "pharmacokinetics", "Michaelis-Menten"
            source: 資料來源
                   - "all": 搜尋所有來源（預設）
                   - "wikidata": 僅 Wikidata（跨領域）
                   - "biomodels": 僅 BioModels（藥學/生物）
                   - "scipy": 僅 SciPy 常數
            domain: 限定領域（可選）
                   - "mechanics", "thermodynamics", "electromagnetism"
                   - "pharmacokinetics", "pharmacodynamics", "enzyme_kinetics"
            limit: 返回數量上限

        Returns:
            {
                "success": true,
                "results": [
                    {
                        "id": "Q179057",
                        "name": "Reynolds number",
                        "latex": "Re = \\frac{\\rho v L}{\\mu}",
                        "sympy_str": "rho * v * L / mu",
                        "source": "wikidata",
                        "url": "https://www.wikidata.org/wiki/Q179057"
                    }
                ],
                "total": 1,
                "sources_searched": ["wikidata"]
            }

        Example:
            # 搜尋雷諾數
            formula_search("Reynolds number")

            # 搜尋藥動學模型
            formula_search("one compartment", source="biomodels")

            # 按領域搜尋
            formula_search("diffusion", domain="thermodynamics")
        """
        results = []
        sources_searched = []

        # 根據 source 參數決定搜尋哪些來源
        search_wikidata = source in ["all", "wikidata"]
        search_biomodels = source in ["all", "biomodels"]
        search_scipy = source in ["all", "scipy"]

        # 如果指定了藥學領域，優先搜尋 BioModels
        if domain in ["pharmacokinetics", "pharmacodynamics", "enzyme_kinetics"]:
            search_biomodels = True
            search_wikidata = source == "all"  # 仍然搜尋 Wikidata 但降低優先級

        # 搜尋 Wikidata
        if search_wikidata:
            try:
                from nsforge.infrastructure.adapters.wikidata_formulas import WikidataFormulaAdapter

                wikidata_adapter = WikidataFormulaAdapter()
                try:
                    if domain:
                        wikidata_results = wikidata_adapter.search_by_category(domain, query, limit)
                    else:
                        wikidata_results = wikidata_adapter.search(query, limit)

                    for r in wikidata_results:
                        results.append(r.to_dict())
                    sources_searched.append("wikidata")
                finally:
                    wikidata_adapter.close()
            except Exception as e:
                print(f"Wikidata search failed: {e}")

        # 搜尋 BioModels
        if search_biomodels:
            try:
                from nsforge.infrastructure.adapters.biomodels import BioModelsAdapter

                biomodels_adapter = BioModelsAdapter()
                try:
                    if domain == "pharmacokinetics":
                        biomodels_results = biomodels_adapter.search_pk_models(query, limit)
                    elif domain == "pharmacodynamics":
                        biomodels_results = biomodels_adapter.search_pd_models(query, limit)
                    elif domain == "enzyme_kinetics":
                        biomodels_results = biomodels_adapter.search_enzyme_kinetics(query, limit)
                    else:
                        biomodels_results = biomodels_adapter.search(query, limit)

                    for r in biomodels_results:
                        results.append(r.to_dict())
                    sources_searched.append("biomodels")
                finally:
                    biomodels_adapter.close()
            except Exception as e:
                print(f"BioModels search failed: {e}")

        # 搜尋 SciPy 常數
        if search_scipy:
            try:
                from nsforge.infrastructure.adapters.scipy_constants import ScipyConstantsAdapter

                scipy_adapter = ScipyConstantsAdapter()
                scipy_results = scipy_adapter.search(query)

                for r in scipy_results[:limit]:
                    results.append(r.to_dict())
                sources_searched.append("scipy")
            except Exception as e:
                print(f"SciPy search failed: {e}")

        return {
            "success": True,
            "results": results[:limit],
            "total": len(results),
            "query": query,
            "sources_searched": sources_searched,
        }

    @mcp.tool()
    def formula_get(
        formula_id: str,
        source: str = "wikidata",
    ) -> dict[str, Any]:
        """
        獲取公式詳細資訊

        根據 ID 獲取完整的公式資訊，包括 LaTeX、SymPy 表達式、變數定義等。

        Args:
            formula_id: 公式識別碼
                       - Wikidata: Q 號（如 "Q179057"）
                       - BioModels: 模型 ID（如 "BIOMD0000000012"）
                       - SciPy: 常數名（如 "speed_of_light"）
            source: 資料來源
                   - "wikidata": Wikidata（預設）
                   - "biomodels": BioModels
                   - "scipy": SciPy 常數

        Returns:
            {
                "success": true,
                "formula": {
                    "id": "Q179057",
                    "name": "Reynolds number",
                    "latex": "Re = \\frac{\\rho v L}{\\mu}",
                    "sympy_str": "rho * v * L / mu",
                    "variables": {
                        "rho": {"description": "密度", "unit": "kg/m³"},
                        "v": {"description": "流速", "unit": "m/s"},
                        "L": {"description": "特徵長度", "unit": "m"},
                        "mu": {"description": "動力黏度", "unit": "Pa·s"}
                    },
                    "source": "wikidata",
                    "url": "https://www.wikidata.org/wiki/Q179057"
                }
            }

        Example:
            # 獲取 Wikidata 公式
            formula_get("Q179057", source="wikidata")

            # 獲取 BioModels 模型
            formula_get("BIOMD0000000012", source="biomodels")

            # 獲取物理常數
            formula_get("speed_of_light", source="scipy")
        """
        result = None

        if source == "wikidata":
            try:
                from nsforge.infrastructure.adapters.wikidata_formulas import WikidataFormulaAdapter

                wikidata_adapter = WikidataFormulaAdapter()
                try:
                    result = wikidata_adapter.get_formula(formula_id)
                finally:
                    wikidata_adapter.close()
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Wikidata error: {e}",
                    "formula_id": formula_id,
                }

        elif source == "biomodels":
            try:
                from nsforge.infrastructure.adapters.biomodels import BioModelsAdapter

                biomodels_adapter = BioModelsAdapter()
                try:
                    result = biomodels_adapter.get_formula(formula_id)
                finally:
                    biomodels_adapter.close()
            except Exception as e:
                return {
                    "success": False,
                    "error": f"BioModels error: {e}",
                    "formula_id": formula_id,
                }

        elif source == "scipy":
            try:
                from nsforge.infrastructure.adapters.scipy_constants import ScipyConstantsAdapter

                scipy_adapter = ScipyConstantsAdapter()
                result = scipy_adapter.get_formula(formula_id)
            except Exception as e:
                return {
                    "success": False,
                    "error": f"SciPy error: {e}",
                    "formula_id": formula_id,
                }

        else:
            return {
                "success": False,
                "error": f"Unknown source: {source}",
                "available_sources": ["wikidata", "biomodels", "scipy"],
            }

        if result is None:
            return {
                "success": False,
                "error": f"Formula not found: {formula_id}",
                "source": source,
            }

        return {
            "success": True,
            "formula": result.to_dict(),
        }

    @mcp.tool()
    def formula_categories(
        source: str = "all",
    ) -> dict[str, Any]:
        """
        列出可用的公式分類

        獲取各資料來源支援的分類，用於更精確的搜尋。

        Args:
            source: 資料來源
                   - "all": 所有來源（預設）
                   - "wikidata", "biomodels", "scipy"

        Returns:
            {
                "success": true,
                "categories": {
                    "wikidata": ["mechanics", "thermodynamics", ...],
                    "biomodels": ["pharmacokinetics", "enzyme_kinetics", ...],
                    "scipy": ["fundamental", "electromagnetic", ...]
                }
            }
        """
        categories: dict[str, list[str]] = {}

        if source in ["all", "wikidata"]:
            try:
                from nsforge.infrastructure.adapters.wikidata_formulas import WikidataFormulaAdapter

                wikidata_adapter = WikidataFormulaAdapter()
                categories["wikidata"] = wikidata_adapter.list_categories()
                wikidata_adapter.close()
            except Exception:
                categories["wikidata"] = []

        if source in ["all", "biomodels"]:
            try:
                from nsforge.infrastructure.adapters.biomodels import BioModelsAdapter

                biomodels_adapter = BioModelsAdapter()
                categories["biomodels"] = biomodels_adapter.list_categories()
                biomodels_adapter.close()
            except Exception:
                categories["biomodels"] = []

        if source in ["all", "scipy"]:
            try:
                from nsforge.infrastructure.adapters.scipy_constants import ScipyConstantsAdapter

                scipy_adapter = ScipyConstantsAdapter()
                categories["scipy"] = scipy_adapter.list_categories()
            except Exception:
                categories["scipy"] = []

        return {
            "success": True,
            "categories": categories,
        }

    # ═══════════════════════════════════════════════════════════════════════
    # 藥學專用工具（BioModels）
    # ═══════════════════════════════════════════════════════════════════════

    @mcp.tool()
    def formula_pk_models(
        query: str = "",
        drug: str = "",
        limit: int = 10,
    ) -> dict[str, Any]:
        """
        搜尋藥動學 (PK) 模型

        專門從 BioModels 搜尋藥動學相關模型。

        Args:
            query: 搜尋關鍵字（如 "absorption", "elimination"）
            drug: 藥物名稱（可選）
            limit: 返回數量上限

        Returns:
            藥動學模型列表

        Example:
            # 搜尋吸收模型
            formula_pk_models(query="absorption")

            # 搜尋特定藥物
            formula_pk_models(drug="warfarin")
        """
        try:
            from nsforge.infrastructure.adapters.biomodels import BioModelsAdapter

            pk_adapter = BioModelsAdapter()
            try:
                search_query = f"{query} {drug}".strip() if drug else query
                if not search_query:
                    search_query = "pharmacokinetics"

                results = pk_adapter.search_pk_models(search_query, limit)

                return {
                    "success": True,
                    "results": [r.to_dict() for r in results],
                    "total": len(results),
                    "source": "biomodels",
                }
            finally:
                pk_adapter.close()
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    @mcp.tool()
    def formula_kinetic_laws(
        model_id: str,
    ) -> dict[str, Any]:
        """
        獲取 BioModels 模型的動力學公式

        從 SBML 模型中提取所有動力學方程式。

        Args:
            model_id: BioModels 模型 ID（如 "BIOMD0000000012"）

        Returns:
            {
                "success": true,
                "model_id": "BIOMD0000000012",
                "kinetic_laws": [
                    {
                        "reaction_id": "v1",
                        "name": "Enzyme binding",
                        "math": "k1 * E * S",
                        "parameters": [
                            {"id": "k1", "value": "0.1", "units": "per_second"}
                        ]
                    }
                ]
            }

        Example:
            formula_kinetic_laws("BIOMD0000000012")
        """
        try:
            from nsforge.infrastructure.adapters.biomodels import BioModelsAdapter

            kinetic_adapter = BioModelsAdapter()
            try:
                kinetic_laws = kinetic_adapter.get_kinetic_laws(model_id)

                return {
                    "success": True,
                    "model_id": model_id,
                    "kinetic_laws": kinetic_laws,
                    "total": len(kinetic_laws),
                }
            finally:
                kinetic_adapter.close()
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "model_id": model_id,
            }

    # ═══════════════════════════════════════════════════════════════════════
    # 物理常數工具（SciPy）
    # ═══════════════════════════════════════════════════════════════════════

    @mcp.tool()
    def formula_constants(
        category: str | None = None,
        query: str = "",
    ) -> dict[str, Any]:
        """
        列出物理常數

        從 SciPy CODATA 2018 獲取物理常數。

        Args:
            category: 分類
                     - "fundamental": 基本常數（c, h, G）
                     - "electromagnetic": 電磁常數
                     - "atomic": 原子常數
                     - "conversion": 換算因子
            query: 搜尋關鍵字（可選）

        Returns:
            物理常數列表（含數值、單位、不確定度）

        Example:
            # 列出所有基本常數
            formula_constants(category="fundamental")

            # 搜尋電子相關常數
            formula_constants(query="electron")
        """
        try:
            from nsforge.infrastructure.adapters.scipy_constants import ScipyConstantsAdapter

            const_adapter = ScipyConstantsAdapter()

            if query:
                results = const_adapter.search(query)
            else:
                formula_ids = const_adapter.list_formulas(category)
                # Filter out None values
                results = [
                    formula
                    for fid in formula_ids
                    if (formula := const_adapter.get_formula(fid)) is not None
                ]

            return {
                "success": True,
                "results": [r.to_dict() for r in results],
                "total": len(results),
                "source": "scipy",
                "category": category,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
