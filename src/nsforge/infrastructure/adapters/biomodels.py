"""
BioModels Adapter - 藥學/PK-PD 模型公式來源

BioModels 是 EMBL-EBI 維護的生物數學模型資料庫：
- 數千個已發表的 PK/PD、代謝、信號傳導模型
- SBML (Systems Biology Markup Language) 格式
- 包含動力學方程式、參數、單位

API 文檔: https://www.ebi.ac.uk/biomodels/docs/

重點提取：
- Kinetic Laws (反應速率公式)
- Rate Constants (速率常數)
- Species (物質濃度)

直接精確檢索，不使用 RAG。
"""

import re
from typing import Any
from xml.etree import ElementTree as ET

import httpx

from .base import BaseAdapter, FormulaInfo

# BioModels API 端點
BIOMODELS_API = "https://www.ebi.ac.uk/biomodels"


class BioModelsAdapter(BaseAdapter):
    """
    BioModels SBML 公式適配器

    專注於藥動學 (PK) 和藥效學 (PD) 模型。

    Example:
        adapter = BioModelsAdapter()
        results = adapter.search("pharmacokinetics")
        model = adapter.get_formula("BIOMD0000000012")
    """

    def __init__(self, timeout: float = 30.0):
        self._timeout = timeout
        self._client: httpx.Client | None = None

    @property
    def source_name(self) -> str:
        return "biomodels"

    def _get_client(self) -> httpx.Client:
        """獲取 HTTP 客戶端"""
        if self._client is None:
            self._client = httpx.Client(
                timeout=self._timeout,
                headers={
                    "User-Agent": "NSForge/1.0",
                    "Accept": "application/json",
                }
            )
        return self._client

    def search(self, query: str, limit: int = 10) -> list[FormulaInfo]:
        """
        搜尋 BioModels 模型

        Args:
            query: 搜尋關鍵字（如 "pharmacokinetics", "Michaelis-Menten"）
            limit: 返回數量上限

        Returns:
            匹配的模型列表
        """
        client = self._get_client()

        try:
            # 使用 BioModels search API
            response = client.get(
                f"{BIOMODELS_API}/search",
                params={
                    "query": query,
                    "numResults": limit,
                    "format": "json",
                }
            )
            response.raise_for_status()
            data = response.json()

            return self._parse_search_results(data)
        except Exception as e:
            print(f"BioModels search error: {e}")
            return []

    def search_pk_models(self, drug: str = "", limit: int = 10) -> list[FormulaInfo]:
        """
        專門搜尋藥動學模型

        Args:
            drug: 藥物名稱（可選）
            limit: 返回數量上限
        """
        query = f"pharmacokinetics {drug}".strip()
        return self.search(query, limit)

    def search_pd_models(self, effect: str = "", limit: int = 10) -> list[FormulaInfo]:
        """
        專門搜尋藥效學模型

        Args:
            effect: 藥效類型（可選）
            limit: 返回數量上限
        """
        query = f"pharmacodynamics {effect}".strip()
        return self.search(query, limit)

    def search_enzyme_kinetics(self, enzyme: str = "", limit: int = 10) -> list[FormulaInfo]:
        """
        搜尋酵素動力學模型（Michaelis-Menten 等）

        Args:
            enzyme: 酵素名稱（可選）
            limit: 返回數量上限
        """
        query = f"enzyme kinetics {enzyme}".strip()
        return self.search(query, limit)

    def get_formula(self, formula_id: str) -> FormulaInfo | None:
        """
        獲取模型詳情並提取公式

        Args:
            formula_id: BioModels ID（如 "BIOMD0000000012"）

        Returns:
            模型資訊（包含提取的動力學公式）
        """
        client = self._get_client()

        try:
            # 獲取模型資訊
            info_response = client.get(
                f"{BIOMODELS_API}/model/{formula_id}",
                params={"format": "json"}
            )
            info_response.raise_for_status()
            model_info = info_response.json()

            # 下載 SBML 檔案
            sbml_response = client.get(
                f"{BIOMODELS_API}/model/download/{formula_id}",
                params={"filename": f"{formula_id}_url.xml"}
            )
            sbml_response.raise_for_status()
            sbml_content = sbml_response.text

            # 解析 SBML 並提取公式
            kinetic_laws = self._extract_kinetic_laws(sbml_content)

            # 組合所有動力學公式為一個字串
            formulas_text = "\n".join([
                f"{kl['reaction_id']}: {kl['math']}"
                for kl in kinetic_laws
            ])

            return FormulaInfo(
                id=formula_id,
                name=model_info.get("name", formula_id),
                expression=formulas_text,
                latex="",  # SBML 公式不是 LaTeX 格式
                sympy_str=formulas_text,
                variables=self._extract_variables(kinetic_laws),
                source="biomodels",
                category="pharmacokinetics" if "pharmacokinetic" in model_info.get("name", "").lower() else "biology",
                description=model_info.get("description", ""),
                url=f"https://www.ebi.ac.uk/biomodels/{formula_id}",
                tags=self._extract_tags(model_info),
                extra={
                    "kinetic_laws": kinetic_laws,
                    "publication": model_info.get("publication", {}),
                    "authors": model_info.get("authors", []),
                }
            )
        except Exception as e:
            print(f"BioModels get_formula error: {e}")
            return None

    def get_kinetic_laws(self, model_id: str) -> list[dict[str, Any]]:
        """
        直接獲取模型中的動力學公式列表

        Args:
            model_id: BioModels ID

        Returns:
            動力學公式列表，每個包含:
            - reaction_id: 反應 ID
            - name: 反應名稱
            - math: 數學表達式（MathML 轉字串）
            - parameters: 參數列表
        """
        client = self._get_client()

        try:
            response = client.get(
                f"{BIOMODELS_API}/model/download/{model_id}",
                params={"filename": f"{model_id}_url.xml"}
            )
            response.raise_for_status()
            return self._extract_kinetic_laws(response.text)
        except Exception as e:
            print(f"BioModels get_kinetic_laws error: {e}")
            return []

    def list_categories(self) -> list[str]:
        """列出 BioModels 常用分類"""
        return [
            "pharmacokinetics",
            "pharmacodynamics",
            "enzyme_kinetics",
            "metabolism",
            "signaling",
            "cell_cycle",
            "immunology",
        ]

    def _parse_search_results(self, data: dict[str, Any]) -> list[FormulaInfo]:
        """解析搜尋結果"""
        results = []
        models = data.get("models", [])

        for model in models:
            model_id = model.get("id", "")
            results.append(FormulaInfo(
                id=model_id,
                name=model.get("name", model_id),
                expression="",  # 搜尋結果不含完整公式
                latex="",
                sympy_str="",
                source="biomodels",
                description=model.get("description", "")[:200],  # 截斷
                url=f"https://www.ebi.ac.uk/biomodels/{model_id}",
                tags=self._extract_tags(model),
            ))

        return results

    def _extract_kinetic_laws(self, sbml_content: str) -> list[dict[str, Any]]:
        """從 SBML 提取動力學公式"""
        kinetic_laws = []

        try:
            # 解析 XML
            root = ET.fromstring(sbml_content)

            # SBML 命名空間
            namespaces = {
                'sbml': 'http://www.sbml.org/sbml/level2/version4',
                'sbml3': 'http://www.sbml.org/sbml/level3/version1/core',
                'mathml': 'http://www.w3.org/1998/Math/MathML',
            }

            # 嘗試不同的 SBML 版本
            for ns_prefix in ['sbml', 'sbml3', '']:
                ns = namespaces.get(ns_prefix, '')
                ns_str = f'{{{ns}}}' if ns else ''

                # 查找所有反應
                reactions = root.findall(f'.//{ns_str}reaction')
                if not reactions:
                    reactions = root.findall('.//reaction')

                for reaction in reactions:
                    reaction_id = reaction.get('id', '')
                    reaction_name = reaction.get('name', reaction_id)

                    # 查找 kineticLaw
                    kinetic_law = reaction.find(f'{ns_str}kineticLaw') or reaction.find('kineticLaw')

                    if kinetic_law is not None:
                        # 提取 MathML 並轉換為字串
                        math_elem = kinetic_law.find('.//{http://www.w3.org/1998/Math/MathML}math')
                        if math_elem is None:
                            math_elem = kinetic_law.find('.//math')

                        math_str = self._mathml_to_string(math_elem) if math_elem is not None else ""

                        # 提取參數
                        params = self._extract_parameters(kinetic_law, ns_str)

                        kinetic_laws.append({
                            "reaction_id": reaction_id,
                            "name": reaction_name,
                            "math": math_str,
                            "parameters": params,
                        })

                if kinetic_laws:
                    break

        except Exception as e:
            print(f"SBML parsing error: {e}")

        return kinetic_laws

    def _mathml_to_string(self, math_elem: ET.Element) -> str:
        """將 MathML 轉換為可讀字串"""
        if math_elem is None:
            return ""

        def process_node(node):
            tag = node.tag.split('}')[-1]  # 移除命名空間

            if tag == 'ci':
                return node.text.strip() if node.text else ""
            elif tag == 'cn':
                return node.text.strip() if node.text else "0"
            elif tag == 'apply':
                children = list(node)
                if not children:
                    return ""
                op = children[0].tag.split('}')[-1]
                args = [process_node(c) for c in children[1:]]

                if op == 'times':
                    return ' * '.join(args)
                elif op == 'divide':
                    return f"({args[0]}) / ({args[1]})" if len(args) >= 2 else ""
                elif op == 'plus':
                    return ' + '.join(args)
                elif op == 'minus':
                    if len(args) == 1:
                        return f"-{args[0]}"
                    return f"({args[0]}) - ({args[1]})"
                elif op == 'power':
                    return f"({args[0]})**({args[1]})" if len(args) >= 2 else ""
                elif op == 'exp':
                    return f"exp({args[0]})" if args else "exp(0)"
                elif op == 'ln':
                    return f"ln({args[0]})" if args else "ln(1)"
                else:
                    return f"{op}({', '.join(args)})"
            else:
                # 遞歸處理子節點
                return ''.join(process_node(c) for c in node)

        try:
            return process_node(math_elem)
        except Exception:
            return ET.tostring(math_elem, encoding='unicode')

    def _extract_parameters(self, kinetic_law: ET.Element, ns_str: str) -> list[dict[str, Any]]:
        """提取動力學公式的參數"""
        params = []

        param_elems = kinetic_law.findall(f'{ns_str}listOfParameters/{ns_str}parameter')
        if not param_elems:
            param_elems = kinetic_law.findall('.//parameter')

        for param in param_elems:
            params.append({
                "id": param.get('id', ''),
                "name": param.get('name', ''),
                "value": param.get('value', ''),
                "units": param.get('units', ''),
            })

        return params

    def _extract_variables(self, kinetic_laws: list[dict]) -> dict[str, dict[str, Any]]:
        """從動力學公式提取變數"""
        variables = {}

        for kl in kinetic_laws:
            # 從參數中提取
            for param in kl.get("parameters", []):
                param_id = param.get("id", "")
                if param_id:
                    variables[param_id] = {
                        "type": "parameter",
                        "value": param.get("value"),
                        "unit": param.get("units"),
                    }

            # 從公式字串中提取變數名
            math_str = kl.get("math", "")
            # 簡單的變數提取（字母開頭的標識符）
            var_matches = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', math_str)
            for var in var_matches:
                if var not in variables and var not in ['exp', 'ln', 'log', 'sin', 'cos']:
                    variables[var] = {"type": "variable"}

        return variables

    def _extract_tags(self, model_info: dict) -> list[str]:
        """提取模型標籤"""
        tags = []

        name = model_info.get("name", "").lower()
        desc = model_info.get("description", "").lower()

        # 基於名稱和描述推斷標籤
        if "pharmacokinetic" in name or "pharmacokinetic" in desc:
            tags.append("pharmacokinetics")
        if "pharmacodynamic" in name or "pharmacodynamic" in desc:
            tags.append("pharmacodynamics")
        if "michaelis" in name or "michaelis" in desc:
            tags.append("enzyme_kinetics")
        if "metabolism" in name or "metabolism" in desc:
            tags.append("metabolism")
        if "absorption" in desc:
            tags.append("absorption")
        if "elimination" in desc or "clearance" in desc:
            tags.append("elimination")
        if "compartment" in desc:
            tags.append("compartmental")

        return tags

    def close(self):
        """關閉 HTTP 客戶端"""
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
