"""
Wikidata Formula Adapter - 從 Wikidata 查詢公式

Wikidata 是最強大的公開結構化公式來源：
- P2534: 定義公式 (Defining Formula) - LaTeX 格式
- P4020: 量綱公式 (Dimension)
- P7235: 變數說明

使用 SPARQL 查詢 Wikidata Query Service。
直接精確檢索，不使用 RAG。
"""

import re
from typing import Any

import httpx
from sympy.parsing.latex import parse_latex

from .base import BaseAdapter, FormulaInfo

# Wikidata SPARQL 端點
WIKIDATA_SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"

# 常用 Wikidata 屬性
WD_PROPS = {
    "defining_formula": "P2534",  # 定義公式
    "dimension": "P4020",  # 量綱
    "quantity_symbol": "P7235",  # 符號
    "instance_of": "P31",  # 實例類型
    "subclass_of": "P279",  # 子類
    "described_by_source": "P1343",  # 來源
}


class WikidataFormulaAdapter(BaseAdapter):
    """
    Wikidata 公式查詢適配器

    提供對 Wikidata 物理量和公式的查詢功能。

    Example:
        adapter = WikidataFormulaAdapter()
        results = adapter.search("Reynolds number")
        formula = adapter.get_formula("Q179057")
    """

    def __init__(self, timeout: float = 30.0):
        self._timeout = timeout
        self._client: httpx.Client | None = None

    @property
    def source_name(self) -> str:
        return "wikidata"

    def _get_client(self) -> httpx.Client:
        """獲取 HTTP 客戶端（懶加載）"""
        if self._client is None:
            self._client = httpx.Client(
                timeout=self._timeout,
                headers={
                    "User-Agent": "NSForge/1.0 (https://github.com/nsforge; formula-mcp)",
                    "Accept": "application/sparql-results+json",
                },
            )
        return self._client

    def _execute_sparql(self, query: str) -> dict[str, Any]:
        """執行 SPARQL 查詢"""
        client = self._get_client()
        response = client.get(WIKIDATA_SPARQL_ENDPOINT, params={"query": query, "format": "json"})
        response.raise_for_status()
        result: dict[str, Any] = response.json()
        return result

    def search(self, query: str, limit: int = 10) -> list[FormulaInfo]:
        """
        搜尋公式

        Args:
            query: 搜尋關鍵字（如 "Reynolds number", "Arrhenius"）
            limit: 返回數量上限

        Returns:
            匹配的公式列表
        """
        # 構建 SPARQL 查詢
        # 搜尋具有定義公式 (P2534) 的項目
        sparql = f'''
        SELECT DISTINCT ?item ?itemLabel ?formula ?description WHERE {{
          ?item wdt:P2534 ?formula.
          ?item rdfs:label ?itemLabel.
          FILTER(LANG(?itemLabel) = "en")
          FILTER(CONTAINS(LCASE(?itemLabel), "{query.lower()}"))
          OPTIONAL {{
            ?item schema:description ?description.
            FILTER(LANG(?description) = "en")
          }}
        }}
        LIMIT {limit}
        '''

        try:
            data = self._execute_sparql(sparql)
            return self._parse_search_results(data)
        except Exception as e:
            # 記錄錯誤但不中斷
            print(f"Wikidata search error: {e}")
            return []

    def search_by_category(
        self, category: str, query: str = "", limit: int = 20
    ) -> list[FormulaInfo]:
        """
        按分類搜尋公式

        Args:
            category: 分類（如 "mechanics", "thermodynamics"）
            query: 額外關鍵字過濾
            limit: 返回數量上限
        """
        # 分類到 Wikidata 類別的映射
        category_mapping = {
            "mechanics": "Q11397",  # 力學
            "thermodynamics": "Q11473",  # 熱力學
            "electromagnetism": "Q12453",  # 電磁學
            "optics": "Q11413",  # 光學
            "quantum": "Q11424",  # 量子力學
            "fluid": "Q4323994",  # 流體力學
            "chemistry": "Q2329",  # 化學
            "pharmacokinetics": "Q899794",  # 藥動學
        }

        wikidata_category = category_mapping.get(category.lower())

        if wikidata_category:
            # 按分類查詢
            sparql = f"""
            SELECT DISTINCT ?item ?itemLabel ?formula ?description WHERE {{
              ?item wdt:P2534 ?formula.
              ?item wdt:P31/wdt:P279* wd:{wikidata_category}.
              ?item rdfs:label ?itemLabel.
              FILTER(LANG(?itemLabel) = "en")
              {f'FILTER(CONTAINS(LCASE(?itemLabel), "{query.lower()}"))' if query else ""}
              OPTIONAL {{
                ?item schema:description ?description.
                FILTER(LANG(?description) = "en")
              }}
            }}
            LIMIT {limit}
            """
        else:
            # 回退到關鍵字搜尋
            return self.search(f"{category} {query}".strip(), limit)

        try:
            data = self._execute_sparql(sparql)
            return self._parse_search_results(data)
        except Exception as e:
            print(f"Wikidata category search error: {e}")
            return []

    def get_formula(self, formula_id: str) -> FormulaInfo | None:
        """
        獲取單個公式詳情

        Args:
            formula_id: Wikidata Q 號（如 "Q179057"）

        Returns:
            公式詳細資訊
        """
        # 移除可能的前綴
        qid = formula_id.upper()
        if not qid.startswith("Q"):
            qid = f"Q{qid}"

        sparql = f"""
        SELECT ?itemLabel ?formula ?description ?dimension ?symbol WHERE {{
          BIND(wd:{qid} AS ?item)
          ?item wdt:P2534 ?formula.
          ?item rdfs:label ?itemLabel.
          FILTER(LANG(?itemLabel) = "en")
          OPTIONAL {{
            ?item schema:description ?description.
            FILTER(LANG(?description) = "en")
          }}
          OPTIONAL {{ ?item wdt:P4020 ?dimension. }}
          OPTIONAL {{ ?item wdt:P7235 ?symbol. }}
        }}
        LIMIT 1
        """

        try:
            data = self._execute_sparql(sparql)
            bindings = data.get("results", {}).get("bindings", [])

            if not bindings:
                return None

            binding = bindings[0]
            latex_formula = binding.get("formula", {}).get("value", "")

            # 嘗試解析 LaTeX 為 SymPy
            sympy_expr = None
            sympy_str = ""
            try:
                sympy_expr = parse_latex(latex_formula)
                sympy_str = str(sympy_expr)
            except Exception:
                sympy_str = latex_formula  # 降級為原始字串

            # 提取變數
            variables = self._extract_variables_from_latex(latex_formula)

            return FormulaInfo(
                id=qid,
                name=binding.get("itemLabel", {}).get("value", ""),
                expression=sympy_expr if sympy_expr else latex_formula,
                latex=latex_formula,
                sympy_str=sympy_str,
                variables=variables,
                source="wikidata",
                description=binding.get("description", {}).get("value", ""),
                url=f"https://www.wikidata.org/wiki/{qid}",
                extra={
                    "dimension": binding.get("dimension", {}).get("value", ""),
                    "symbol": binding.get("symbol", {}).get("value", ""),
                },
            )
        except Exception as e:
            print(f"Wikidata get_formula error: {e}")
            return None

    def list_categories(self) -> list[str]:
        """列出可用的公式分類"""
        return [
            "mechanics",
            "thermodynamics",
            "electromagnetism",
            "optics",
            "quantum",
            "fluid",
            "chemistry",
            "pharmacokinetics",
        ]

    def _parse_search_results(self, data: dict[str, Any]) -> list[FormulaInfo]:
        """解析 SPARQL 搜尋結果"""
        results = []
        bindings = data.get("results", {}).get("bindings", [])

        for binding in bindings:
            item_uri = binding.get("item", {}).get("value", "")
            qid = item_uri.split("/")[-1] if item_uri else ""
            latex_formula = binding.get("formula", {}).get("value", "")

            # 嘗試轉換 LaTeX 為 SymPy
            sympy_str = ""
            try:
                sympy_expr = parse_latex(latex_formula)
                sympy_str = str(sympy_expr)
            except Exception:
                sympy_str = latex_formula

            results.append(
                FormulaInfo(
                    id=qid,
                    name=binding.get("itemLabel", {}).get("value", ""),
                    expression=latex_formula,
                    latex=latex_formula,
                    sympy_str=sympy_str,
                    source="wikidata",
                    description=binding.get("description", {}).get("value", ""),
                    url=f"https://www.wikidata.org/wiki/{qid}" if qid else "",
                )
            )

        return results

    def _extract_variables_from_latex(self, latex_str: str) -> dict[str, dict[str, Any]]:
        """從 LaTeX 公式中提取變數"""
        variables: dict[str, dict[str, Any]] = {}

        # 常見的單字母變數
        single_vars = re.findall(r"(?<![a-zA-Z])([a-zA-Z])(?![a-zA-Z])", latex_str)

        # 帶下標的變數 (如 v_0, T_c)
        subscript_vars = re.findall(r"([a-zA-Z])_\{?([a-zA-Z0-9]+)\}?", latex_str)

        # 希臘字母
        greek_vars = re.findall(
            r"\\(alpha|beta|gamma|delta|epsilon|theta|lambda|mu|nu|rho|sigma|tau|omega|Omega)",
            latex_str,
        )

        for var in single_vars:
            if var not in ["d", "e", "i"]:  # 排除微分符號、自然對數、虛數
                variables[var] = {"type": "variable"}

        for base, sub in subscript_vars:
            var_name = f"{base}_{sub}"
            variables[var_name] = {"type": "variable", "subscript": sub}

        for greek in greek_vars:
            variables[greek] = {"type": "variable", "greek": "True"}

        return variables

    def close(self) -> None:
        """關閉 HTTP 客戶端"""
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self) -> "WikidataFormulaAdapter":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        self.close()
