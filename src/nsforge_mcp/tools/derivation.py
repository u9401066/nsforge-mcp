"""
Derivation Tools - 推導引擎 MCP 工具

這是 NSForge 的核心！
提供有狀態的推導會話，支援：
- 多格式公式輸入
- 完整步驟記錄
- 溯源追蹤
- 持久化（防止中斷）

The "Forge" in NSForge means we CREATE new formulas through derivation.
"""

from pathlib import Path
from typing import Any

from nsforge.domain.derivation_session import (
    DerivationSession,
    SessionManager,
    get_session_manager,
)
from nsforge.domain.formula import FormulaSource
from nsforge.infrastructure.derivation_repository import (
    DerivationResult,
    get_repository,
)

# 全域會話管理器（延遲初始化）
_manager: SessionManager | None = None


def _get_manager() -> SessionManager:
    global _manager
    if _manager is None:
        # 預設存在專案目錄下
        _manager = get_session_manager(Path("derivation_sessions"))
    return _manager


# 當前活躍會話
_current_session: DerivationSession | None = None


def _get_current_session() -> DerivationSession | None:
    return _current_session


def _set_current_session(session: DerivationSession | None) -> None:
    global _current_session
    _current_session = session


def register_derivation_tools(mcp: Any) -> None:
    """註冊推導引擎工具"""

    # ═══════════════════════════════════════════════════════════════════════
    # 會話管理
    # ═══════════════════════════════════════════════════════════════════════

    @mcp.tool()
    def derivation_start(
        name: str,
        description: str = "",
        author: str = "",
    ) -> dict[str, Any]:
        """
        開始新的推導會話

        這是所有推導的起點。會話會自動持久化，防止中斷。

        Args:
            name: 推導名稱（如 "溫度修正消除率"）
            description: 推導描述
            author: 作者

        Returns:
            會話資訊

        Example:
            derivation_start("temp_corrected_elimination", "Temperature-corrected drug elimination rate")
            → {"session_id": "a1b2c3d4", "name": "temp_corrected_elimination", ...}
        """
        manager = _get_manager()
        session = manager.create(
            name=name,
            description=description,
            author=author,
            auto_persist=True,
        )
        _set_current_session(session)

        return {
            "success": True,
            "session_id": session.session_id,
            "name": session.name,
            "status": session.status.value,
            "message": f"Derivation session '{name}' started. Use derivation_load_formula to add formulas.",
            "persist_path": str(session._persist_path) if session._persist_path else None,
        }

    @mcp.tool()
    def derivation_resume(session_id: str) -> dict[str, Any]:
        """
        恢復暫停的推導會話

        如果推導過程中斷，可以用這個工具恢復。

        Args:
            session_id: 會話 ID

        Returns:
            會話狀態
        """
        manager = _get_manager()
        session = manager.get(session_id)

        if session is None:
            return {
                "success": False,
                "error": f"Session '{session_id}' not found",
                "available_sessions": [s["session_id"] for s in manager.list_sessions()],
            }

        _set_current_session(session)

        return {
            "success": True,
            "session_id": session.session_id,
            "name": session.name,
            "status": session.status.value,
            "step_count": session.step_count,
            "formulas_loaded": session.formula_ids,
            "current_expression": str(session.current_expression) if session.current_expression else None,
            "message": "Session resumed. Continue with derivation operations.",
        }

    @mcp.tool()
    def derivation_list_sessions() -> dict[str, Any]:
        """
        列出所有推導會話

        Returns:
            所有會話列表
        """
        manager = _get_manager()
        sessions = manager.list_sessions()

        return {
            "success": True,
            "sessions": sessions,
            "count": len(sessions),
        }

    @mcp.tool()
    def derivation_status() -> dict[str, Any]:
        """
        取得當前會話狀態

        Returns:
            當前會話詳細狀態
        """
        session = _get_current_session()
        if session is None:
            return {
                "success": False,
                "error": "No active session. Use derivation_start or derivation_resume first.",
            }

        return {
            "success": True,
            **session.get_current(),
        }

    # ═══════════════════════════════════════════════════════════════════════
    # 公式載入
    # ═══════════════════════════════════════════════════════════════════════

    @mcp.tool()
    def derivation_load_formula(
        formula: str | dict[str, Any],
        formula_id: str | None = None,
        source: str = "user_input",
        source_detail: str = "",
        name: str = "",
        description: str = "",
    ) -> dict[str, Any]:
        """
        載入公式到當前會話

        支援多種格式輸入：
        - SymPy 字串: "C_0 * exp(-k*t)"
        - LaTeX: "C_0 e^{-kt}" 或 "\\frac{dC}{dt} = -kC"
        - 字典: {"expression": "...", "variables": {...}}

        Args:
            formula: 公式（多種格式）
            formula_id: 公式 ID（可選，自動生成）
            source: 來源標記 ("user_input", "textbook", "sympy_builtin", "derived", "external_mcp")
            source_detail: 詳細來源（如 "Goodman & Gilman Ch.2"）
            name: 公式名稱
            description: 公式描述

        Returns:
            載入結果

        Examples:
            # SymPy 格式
            derivation_load_formula("C_0 * exp(-k*t)", formula_id="one_compartment")

            # LaTeX 格式
            derivation_load_formula("\\frac{dC}{dt} = -k \\cdot C")

            # 字典格式（含變數資訊）
            derivation_load_formula({
                "expression": "k_ref * exp(E_a/R * (1/T_ref - 1/T))",
                "name": "Arrhenius temperature correction",
                "variables": {
                    "k_ref": {"description": "Reference rate constant", "unit": "1/h"},
                    "E_a": {"description": "Activation energy", "unit": "J/mol"},
                    "T": {"description": "Temperature", "unit": "K"},
                }
            })
        """
        session = _get_current_session()
        if session is None:
            return {
                "success": False,
                "error": "No active session. Use derivation_start first.",
            }

        # 解析來源
        try:
            formula_source = FormulaSource(source)
        except ValueError:
            formula_source = FormulaSource.USER_INPUT

        return session.load_formula(
            formula_input=formula,
            formula_id=formula_id,
            source=formula_source,
            source_detail=source_detail,
            name=name,
            description=description,
        )

    # ═══════════════════════════════════════════════════════════════════════
    # 推導操作
    # ═══════════════════════════════════════════════════════════════════════

    @mcp.tool()
    def derivation_substitute(
        variable: str,
        replacement: str,
        in_formula: str | None = None,
        description: str = "",
    ) -> dict[str, Any]:
        """
        代入操作

        將公式中的變數替換為另一個表達式。
        這是組合公式的關鍵操作。

        Args:
            variable: 要替換的變數名
            replacement: 替換的表達式
            in_formula: 在哪個公式中代入（預設為當前）
            description: 操作描述

        Returns:
            代入結果

        Example:
            # 先載入兩個公式
            derivation_load_formula("C_0 * exp(-k*t)", formula_id="pk")
            derivation_load_formula("k_ref * exp(E_a/R * (1/T_ref - 1/T))", formula_id="arrhenius")

            # 將 arrhenius 代入 pk 的 k
            derivation_substitute("k", "k_ref * exp(E_a/R * (1/T_ref - 1/T))", in_formula="pk")
        """
        session = _get_current_session()
        if session is None:
            return {
                "success": False,
                "error": "No active session. Use derivation_start first.",
            }

        return session.substitute(
            target_var=variable,
            replacement=replacement,
            in_formula=in_formula,
            description=description,
        )

    @mcp.tool()
    def derivation_simplify(
        method: str = "auto",
        description: str = "",
    ) -> dict[str, Any]:
        """
        簡化當前表達式

        Args:
            method: 簡化方法
                - "auto": 自動選擇（預設）
                - "trig": 三角函數簡化
                - "radical": 根式簡化
                - "expand_then_simplify": 先展開再簡化
            description: 操作描述

        Returns:
            簡化結果
        """
        session = _get_current_session()
        if session is None:
            return {
                "success": False,
                "error": "No active session. Use derivation_start first.",
            }

        return session.simplify(method=method, description=description)

    @mcp.tool()
    def derivation_solve_for(
        variable: str,
        description: str = "",
    ) -> dict[str, Any]:
        """
        求解變數

        將當前表達式求解為指定變數的函數。

        Args:
            variable: 要求解的變數
            description: 操作描述

        Returns:
            求解結果（可能有多個解）

        Example:
            derivation_load_formula("m*a - F", formula_id="newton")
            derivation_solve_for("a")
            → a = F/m
        """
        session = _get_current_session()
        if session is None:
            return {
                "success": False,
                "error": "No active session. Use derivation_start first.",
            }

        return session.solve_for(variable=variable, description=description)

    @mcp.tool()
    def derivation_differentiate(
        variable: str,
        order: int = 1,
        description: str = "",
    ) -> dict[str, Any]:
        """
        對當前表達式微分

        Args:
            variable: 微分變數
            order: 階數（預設 1）
            description: 操作描述

        Returns:
            微分結果
        """
        session = _get_current_session()
        if session is None:
            return {
                "success": False,
                "error": "No active session. Use derivation_start first.",
            }

        return session.differentiate(
            variable=variable,
            order=order,
            description=description,
        )

    @mcp.tool()
    def derivation_integrate(
        variable: str,
        lower: str | None = None,
        upper: str | None = None,
        description: str = "",
    ) -> dict[str, Any]:
        """
        對當前表達式積分

        Args:
            variable: 積分變數
            lower: 下界（可選，定積分時需要）
            upper: 上界（可選，定積分時需要）
            description: 操作描述

        Returns:
            積分結果
        """
        session = _get_current_session()
        if session is None:
            return {
                "success": False,
                "error": "No active session. Use derivation_start first.",
            }

        return session.integrate(
            variable=variable,
            lower=lower,
            upper=upper,
            description=description,
        )

    # ═══════════════════════════════════════════════════════════════════════
    # 結果與歷史
    # ═══════════════════════════════════════════════════════════════════════

    @mcp.tool()
    def derivation_get_steps() -> dict[str, Any]:
        """
        取得所有推導步驟

        返回完整的步驟歷史，包含：
        - 每步的操作類型
        - 輸入輸出表達式
        - SymPy 指令
        - 時間戳

        Returns:
            步驟列表
        """
        session = _get_current_session()
        if session is None:
            return {
                "success": False,
                "error": "No active session.",
            }

        return {
            "success": True,
            "session_id": session.session_id,
            "name": session.name,
            "step_count": session.step_count,
            "steps": session.get_steps(),
        }

    @mcp.tool()
    def derivation_complete(
        description: str = "",
        clinical_context: str = "",
        assumptions: list[str] | None = None,
        limitations: list[str] | None = None,
        references: list[str] | None = None,
        tags: list[str] | None = None,
        auto_save: bool = True,
    ) -> dict[str, Any]:
        """
        完成推導並自動存檔

        標記推導為完成，返回完整的推導記錄。
        Agent 應該提供描述性知識（公式的物理/臨床意義、使用時機等）。

        Args:
            description: 公式描述（物理/化學/臨床意義）
            clinical_context: 臨床應用場景（何時使用這個公式）
            assumptions: 推導假設條件
            limitations: 使用限制
            references: 參考文獻
            tags: 標籤（用於分類和搜尋）
            auto_save: 是否自動存檔（預設 True）

        Returns:
            完整推導記錄，包含：
            - 最終表達式
            - 所有步驟
            - 使用的公式及其來源
            - 溯源資訊
            - 存檔路徑（如果 auto_save=True）

        Example:
            derivation_complete(
                description="Temperature-corrected drug elimination rate combining first-order kinetics with Arrhenius equation",
                clinical_context="Use when adjusting drug dosing for febrile patients or hypothermia protocols",
                assumptions=["First-order elimination kinetics", "Arrhenius temperature dependence"],
                limitations=["Valid only for temperature range 32-42°C", "Assumes linear protein binding"],
                references=["Goodman & Gilman Ch.2", "Atkins Physical Chemistry Ch.22"],
                tags=["pharmacokinetics", "temperature", "elimination"]
            )
        """
        session = _get_current_session()
        if session is None:
            return {
                "success": False,
                "error": "No active session.",
            }

        result = session.complete()

        if not result.get("success"):
            return result

        # 自動存檔到 DerivationRepository
        saved_path = None
        if auto_save:
            try:
                repo = get_repository(Path("formulas"))

                # 建立 DerivationResult
                derivation_result = DerivationResult(
                    id=session.session_id,
                    name=session.name,
                    expression=str(session.current_expression),
                    variables={
                        str(s): {"description": "", "unit": ""}
                        for s in (session.current_expression.free_symbols if session.current_expression else [])
                    },
                    derived_from=list(session.formulas.keys()),
                    derivation_steps=[step["description"] for step in result["steps"]],
                    assumptions=assumptions or [],
                    verified=False,  # 需要手動驗證
                    description=description,
                    clinical_context=clinical_context,
                    limitations=limitations or [],
                    references=references or [],
                    tags=tags or [],
                    author=session.author,
                    category="derived",
                )

                # 註冊並存檔
                repo.register(derivation_result)
                saved_path = repo.save(session.session_id)

            except Exception as e:
                result["save_warning"] = f"Completed but save failed: {e}"

        # 清除當前會話
        _set_current_session(None)

        if saved_path:
            result["saved_to"] = str(saved_path)
            result["message"] = f"Derivation completed and saved to {saved_path}"

        return result

    @mcp.tool()
    def derivation_abort() -> dict[str, Any]:
        """
        放棄當前推導

        會話仍然保存在磁碟上，可以之後用 derivation_resume 恢復。

        Returns:
            操作結果
        """
        session = _get_current_session()
        if session is None:
            return {
                "success": False,
                "error": "No active session.",
            }

        session_id = session.session_id
        session.save()  # 確保保存
        _set_current_session(None)

        return {
            "success": True,
            "message": f"Session '{session_id}' saved and deactivated. Use derivation_resume('{session_id}') to continue later.",
            "session_id": session_id,
        }

    # ═══════════════════════════════════════════════════════════════════════
    # 已存檔推導管理
    # ═══════════════════════════════════════════════════════════════════════

    @mcp.tool()
    def derivation_list_saved(
        category: str | None = None,
    ) -> dict[str, Any]:
        """
        列出所有已存檔的推導結果

        Args:
            category: 類別篩選（可選）

        Returns:
            已存檔的推導列表

        Example:
            derivation_list_saved()
            → {"success": True, "results": ["temp_corrected_elimination", ...], "count": 5}
        """
        try:
            repo = get_repository(Path("formulas"))
            result_ids = repo.list_all(category=category)

            return {
                "success": True,
                "results": result_ids,
                "count": len(result_ids),
                "category": category or "all",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    @mcp.tool()
    def derivation_get_saved(result_id: str) -> dict[str, Any]:
        """
        取得已存檔的推導結果詳情

        Args:
            result_id: 推導結果 ID

        Returns:
            完整的推導結果，包含：
            - 公式表達式
            - 推導步驟
            - 來源公式
            - 臨床/物理意義
            - 使用限制
            - 參考文獻

        Example:
            derivation_get_saved("temp_corrected_elimination")
            → {"success": True, "name": "...", "expression": "...", ...}
        """
        try:
            repo = get_repository(Path("formulas"))
            result = repo.get(result_id)

            if result is None:
                return {
                    "success": False,
                    "error": f"Derivation result '{result_id}' not found",
                    "available_results": repo.list_all(),
                }

            return {
                "success": True,
                **result.to_dict(),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    @mcp.tool()
    def derivation_search_saved(
        query: str,
    ) -> dict[str, Any]:
        """
        搜尋已存檔的推導結果

        在公式名稱、描述、標籤中搜尋關鍵字。

        Args:
            query: 搜尋關鍵字

        Returns:
            符合的推導結果列表

        Example:
            derivation_search_saved("temperature")
            → {"success": True, "results": [{"id": "...", "name": "...", ...}], "count": 2}
        """
        try:
            repo = get_repository(Path("formulas"))
            results = repo.search(query)

            return {
                "success": True,
                "results": [r.to_dict() for r in results],
                "count": len(results),
                "query": query,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    @mcp.tool()
    def derivation_repository_stats() -> dict[str, Any]:
        """
        取得推導庫統計資訊

        Returns:
            統計資訊：
            - 總數
            - 已驗證數量
            - 未驗證數量
            - 分類統計

        Example:
            derivation_repository_stats()
            → {"total": 10, "verified": 5, "categories": {"pk": 3, "pd": 2, ...}}
        """
        try:
            repo = get_repository(Path("formulas"))
            stats = repo.stats()

            return {
                "success": True,
                **stats,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    @mcp.tool()
    def derivation_update_saved(
        result_id: str,
        name: str | None = None,
        description: str | None = None,
        clinical_context: str | None = None,
        assumptions: list[str] | None = None,
        limitations: list[str] | None = None,
        references: list[str] | None = None,
        tags: list[str] | None = None,
        category: str | None = None,
        verified: bool | None = None,
        verification_method: str | None = None,
    ) -> dict[str, Any]:
        """
        更新已存檔推導的元資料

        允許 Agent 更新推導的描述性知識、分類、驗證狀態等。
        不能修改推導表達式本身（那需要重新推導）。

        Args:
            result_id: 推導結果 ID
            name: 新名稱
            description: 新描述
            clinical_context: 新臨床情境
            assumptions: 新假設清單
            limitations: 新限制清單
            references: 新參考文獻
            tags: 新標籤
            category: 新分類
            verified: 驗證狀態
            verification_method: 驗證方法

        Returns:
            更新結果

        Example:
            derivation_update_saved(
                "temp_corrected_elimination",
                description="Updated description with more details",
                tags=["pharmacokinetics", "temperature", "elimination", "fever"],
                verified=True,
                verification_method="dimensional_analysis + clinical_validation"
            )
        """
        try:
            repo = get_repository(Path("formulas"))

            # 準備更新資料
            updates: dict[str, Any] = {}
            if name is not None:
                updates["name"] = name
            if description is not None:
                updates["description"] = description
            if clinical_context is not None:
                updates["clinical_context"] = clinical_context
            if assumptions is not None:
                updates["assumptions"] = assumptions
            if limitations is not None:
                updates["limitations"] = limitations
            if references is not None:
                updates["references"] = references
            if tags is not None:
                updates["tags"] = tags
            if category is not None:
                updates["category"] = category
            if verified is not None:
                updates["verified"] = verified
                if verified and verification_method:
                    updates["verification_method"] = verification_method
                    from datetime import datetime
                    updates["verified_at"] = datetime.now().isoformat()

            if not updates:
                return {
                    "success": False,
                    "error": "No updates provided",
                }

            # 執行更新
            repo.update(result_id, **updates)

            # 重新存檔
            saved_path = repo.save(result_id)

            return {
                "success": True,
                "result_id": result_id,
                "updates": list(updates.keys()),
                "saved_to": str(saved_path),
                "message": f"Updated {len(updates)} fields and saved to {saved_path}",
            }

        except ValueError as e:
            return {
                "success": False,
                "error": str(e),
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Update failed: {e}",
            }

    @mcp.tool()
    def derivation_delete_saved(
        result_id: str,
        confirm: bool = False,
    ) -> dict[str, Any]:
        """
        刪除已存檔的推導結果

        ⚠️ 警告：此操作不可逆！推導記錄和 YAML 檔案都會被刪除。

        Args:
            result_id: 推導結果 ID
            confirm: 必須設為 True 才會執行刪除（安全機制）

        Returns:
            刪除結果

        Example:
            # 必須明確確認才能刪除
            derivation_delete_saved("temp_corrected_elimination", confirm=True)
        """
        if not confirm:
            return {
                "success": False,
                "error": "Deletion not confirmed. Set confirm=True to proceed.",
                "warning": "⚠️ This operation is irreversible!",
            }

        try:
            repo = get_repository(Path("formulas"))

            # 先取得詳情（用於確認訊息）
            result = repo.get(result_id)
            if result is None:
                return {
                    "success": False,
                    "error": f"Derivation result '{result_id}' not found",
                    "available_results": repo.list_all(),
                }

            result_name = result.name

            # 執行刪除
            deleted = repo.delete(result_id, delete_file=True)

            if deleted:
                return {
                    "success": True,
                    "result_id": result_id,
                    "result_name": result_name,
                    "message": f"Deleted derivation '{result_name}' (ID: {result_id})",
                }
            else:
                return {
                    "success": False,
                    "error": "Deletion failed (unknown reason)",
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Deletion failed: {e}",
            }
