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
            "current_expression": str(session.current_expression)
            if session.current_expression
            else None,
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
        # 🆕 人類知識
        notes: str = "",
        assumptions: list[str] | None = None,
        limitations: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        代入操作（帶人類知識記錄）

        將公式中的變數替換為另一個表達式。
        這是組合公式的關鍵操作。

        ═══════════════════════════════════════════════════════════════════════
        ⚡ 每一步都可以加入人類知識！
        ═══════════════════════════════════════════════════════════════════════

        Args:
            variable: 要替換的變數名
            replacement: 替換的表達式
            in_formula: 在哪個公式中代入（預設為當前）
            description: 操作描述
            notes: 人類洞見（為什麼這樣做、觀察、警告）
            assumptions: 這步的假設條件
            limitations: 這步的限制

        Returns:
            代入結果（含記錄的知識）

        Example:
            derivation_substitute(
                variable="k",
                replacement="k_ref * exp(E_a/R * (1/T_ref - 1/T))",
                description="Apply Arrhenius equation for temperature dependence",
                notes="⚠️ 假設 V_max 遵循 Arrhenius，但酵素在 >42°C 會變性",
                assumptions=["Temperature range 32-42°C", "No enzyme denaturation"],
                limitations=["Not valid for high temperature"]
            )
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
            notes=notes,
            assumptions=assumptions,
            limitations=limitations,
        )

    @mcp.tool()
    def derivation_simplify(
        method: str = "auto",
        description: str = "",
        # 🆕 人類知識
        notes: str = "",
        assumptions: list[str] | None = None,
        limitations: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        簡化當前表達式（帶人類知識記錄）

        Args:
            method: 簡化方法
                - "auto": 自動選擇（預設）
                - "trig": 三角函數簡化
                - "radical": 根式簡化
                - "expand_then_simplify": 先展開再簡化
            description: 操作描述
            notes: 人類洞見
            assumptions: 這步的假設
            limitations: 這步的限制

        Returns:
            簡化結果
        """
        session = _get_current_session()
        if session is None:
            return {
                "success": False,
                "error": "No active session. Use derivation_start first.",
            }

        return session.simplify(
            method=method,
            description=description,
            notes=notes,
            assumptions=assumptions,
            limitations=limitations,
        )

    @mcp.tool()
    def derivation_solve_for(
        variable: str,
        description: str = "",
        # 🆕 人類知識
        notes: str = "",
        assumptions: list[str] | None = None,
        limitations: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        求解變數（帶人類知識記錄）

        將當前表達式求解為指定變數的函數。

        Args:
            variable: 要求解的變數
            description: 操作描述
            notes: 人類洞見
            assumptions: 這步的假設
            limitations: 這步的限制

        Returns:
            求解結果（可能有多個解）

        Example:
            derivation_load_formula("m*a - F", formula_id="newton")
            derivation_solve_for(
                variable="a",
                notes="假設質量不變",
                assumptions=["Constant mass"]
            )
            → a = F/m
        """
        session = _get_current_session()
        if session is None:
            return {
                "success": False,
                "error": "No active session. Use derivation_start first.",
            }

        return session.solve_for(
            variable=variable,
            description=description,
            notes=notes,
            assumptions=assumptions,
            limitations=limitations,
        )

    @mcp.tool()
    def derivation_differentiate(
        variable: str,
        order: int = 1,
        description: str = "",
        # 🆕 人類知識
        notes: str = "",
        assumptions: list[str] | None = None,
        limitations: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        對當前表達式微分（帶人類知識記錄）

        Args:
            variable: 微分變數
            order: 階數（預設 1）
            description: 操作描述
            notes: 人類洞見
            assumptions: 這步的假設
            limitations: 這步的限制

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
            notes=notes,
            assumptions=assumptions,
            limitations=limitations,
        )

    @mcp.tool()
    def derivation_integrate(
        variable: str,
        lower: str | None = None,
        upper: str | None = None,
        description: str = "",
        # 🆕 人類知識
        notes: str = "",
        assumptions: list[str] | None = None,
        limitations: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        對當前表達式積分（帶人類知識記錄）

        Args:
            variable: 積分變數
            lower: 下界（可選，定積分時需要）
            upper: 上界（可選，定積分時需要）
            description: 操作描述
            notes: 人類洞見
            assumptions: 這步的假設
            limitations: 這步的限制

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
            notes=notes,
            assumptions=assumptions,
            limitations=limitations,
        )

    # ═══════════════════════════════════════════════════════════════════════
    # 橋接工具：SymPy-MCP ↔ NSForge
    # ═══════════════════════════════════════════════════════════════════════

    @mcp.tool()
    def derivation_record_step(
        expression: str,
        description: str,
        latex: str | None = None,
        notes: str | None = None,
        source: str = "sympy_mcp",
        operation_type: str = "custom",
        set_as_current: bool = True,
    ) -> dict[str, Any]:
        """
        記錄一個推導步驟（從 SymPy-MCP 或手動）

        ═══════════════════════════════════════════════════════════════════════
        這是 SymPy-MCP 和 NSForge 之間的橋樑！
        ═══════════════════════════════════════════════════════════════════════

        用途：
        1. 在 SymPy-MCP 計算後，把結果記錄到 NSForge 會話
        2. 可以加入 notes 說明「為什麼這步要這樣做」
        3. 保持完整的推導歷史

        工作流程：
        1. SymPy-MCP: intro + introduce_expression + substitute...
        2. SymPy-MCP: print_latex_expression (確認結果)
        3. NSForge: derivation_record_step (記錄這步 + 加入說明)
        4. 重複 1-3
        5. NSForge: derivation_complete

        Args:
            expression: SymPy 格式的表達式（從 SymPy-MCP 結果複製）
            description: 這步做了什麼
            latex: LaTeX 格式（可選，會自動生成）
            notes: 額外說明（非計算性的人類知識！）
                   例如：「這裡假設線性，但酵素活性實際上是 S 型曲線」
            source: 來源 ("sympy_mcp", "manual", "literature")
            operation_type: 操作類型 ("substitute", "simplify", "solve", "custom")
            set_as_current: 是否設為當前表達式（預設 True）

        Returns:
            記錄結果

        Example:
            # 在 SymPy-MCP 計算完成後
            derivation_record_step(
                expression="C*V_max_ref*exp(E_a*(1/T_ref - 1/T)/R)/(C + K_m)",
                description="Substituted Arrhenius equation for Vmax",
                notes="假設 Vmax 的溫度依賴遵循 Arrhenius，但實際上酵素在高溫會變性",
                source="sympy_mcp"
            )
        """
        import sympy as sp

        session = _get_current_session()
        if session is None:
            return {
                "success": False,
                "error": "No active session. Use derivation_start first.",
            }

        # 解析表達式
        try:
            expr = sp.sympify(expression)
        except Exception as e:
            return {
                "success": False,
                "error": f"Cannot parse expression: {e}",
            }

        # 生成 LaTeX
        latex_str = latex or sp.latex(expr)

        # 映射操作類型
        op_map = {
            "substitute": "substitute",
            "simplify": "simplify",
            "solve": "solve",
            "differentiate": "differentiate",
            "integrate": "integrate",
            "custom": "custom",
        }
        from nsforge.domain.derivation_session import OperationType, StepStatus

        op_type = OperationType(op_map.get(operation_type, "custom"))

        # 建立步驟描述（包含 notes）
        full_description = description
        if notes:
            full_description = f"{description}\n\n📝 Notes: {notes}"

        # 新增步驟
        step = session._add_step(
            operation=op_type,
            description=full_description,
            input_expressions={"source": source, "notes": notes or ""},
            output_expr=expr,
            sympy_command=f"# From {source}: {expression[:50]}...",
            status=StepStatus.SUCCESS,
        )

        # 更新當前表達式
        if set_as_current:
            session.current_expression = expr

        return {
            "success": True,
            "step_number": step.step_number,
            "expression": str(expr),
            "latex": latex_str,
            "description": description,
            "notes": notes,
            "source": source,
            "message": "Step recorded. Continue with SymPy-MCP or add more notes.",
            # ⚠️ 重要提醒：必須顯示公式給用戶！
            "AGENT_INSTRUCTION": (
                "⚠️ IMPORTANT: You MUST display the formula to the user NOW! "
                "Use the LaTeX above to show the current result. "
                "The user needs to see and confirm the formula before discussing next steps. "
                "Example: '目前公式為：$" + latex_str.replace("\\", "\\\\") + "$'"
            ),
        }

    @mcp.tool()
    def derivation_add_note(
        note: str,
        note_type: str = "observation",
        related_variables: list[str] | None = None,
        related_step: int | None = None,
    ) -> dict[str, Any]:
        """
        在推導中加入說明（不是計算步驟）

        ═══════════════════════════════════════════════════════════════════════
        用於記錄「人類知識」- 不是計算，而是洞見、假設、警告、修正建議
        ═══════════════════════════════════════════════════════════════════════

        這很重要！數學推導不只是公式變換，還包含：
        - 為什麼選擇這個模型
        - 這個假設何時會失效
        - 臨床/物理意義是什麼
        - 需要注意什麼

        Args:
            note: 說明內容
            note_type: 說明類型
                - "assumption": 假設條件
                - "limitation": 限制/警告
                - "observation": 觀察/洞見
                - "correction": 修正建議
                - "clinical": 臨床意義
                - "physical": 物理意義
            related_variables: 相關的變數
            related_step: 相關的步驟編號（可選）

        Returns:
            記錄結果

        Example:
            # 在代入 Arrhenius 後加入說明
            derivation_add_note(
                note="酵素活性 vs 溫度不是線性的！在高溫 (>42°C) 酵素會變性，"
                     "此時 Arrhenius 方程不再適用。應考慮加入校正因子 γ(T)。",
                note_type="limitation",
                related_variables=["V_max", "T"]
            )

            # 加入修正建議
            derivation_add_note(
                note="建議加入 Hill-type 校正因子：γ(T) = 1 / (1 + (T/T_denat)^n)",
                note_type="correction",
                related_variables=["gamma", "T_denat"]
            )
        """
        import sympy as sp

        session = _get_current_session()
        if session is None:
            return {
                "success": False,
                "error": "No active session. Use derivation_start first.",
            }

        # 格式化 note
        type_emoji = {
            "assumption": "📋",
            "limitation": "⚠️",
            "observation": "💡",
            "correction": "🔧",
            "clinical": "🏥",
            "physical": "🔬",
        }
        emoji = type_emoji.get(note_type, "📝")

        formatted_note = f"{emoji} [{note_type.upper()}] {note}"
        if related_variables:
            formatted_note += f"\n   Related: {', '.join(related_variables)}"
        if related_step:
            formatted_note += f"\n   See step {related_step}"

        # 用 CUSTOM 操作類型記錄
        from nsforge.domain.derivation_session import OperationType, StepStatus

        # 建立一個虛擬表達式（用於記錄）
        note_expr = sp.Symbol(f"NOTE_{len(session.steps) + 1}")

        step = session._add_step(
            operation=OperationType.CUSTOM,
            description=formatted_note,
            input_expressions={
                "note_type": note_type,
                "related_variables": str(related_variables or []),
                "related_step": str(related_step or ""),
            },
            output_expr=session.current_expression or note_expr,  # 保持當前表達式
            sympy_command="# Note (no computation)",
            status=StepStatus.SUCCESS,
        )

        return {
            "success": True,
            "step_number": step.step_number,
            "note_type": note_type,
            "note": note,
            "related_variables": related_variables,
            "message": f"Note added as step {step.step_number}. This is recorded but does not change the expression.",
        }

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

    # ═══════════════════════════════════════════════════════════════════════
    # 步驟 CRUD 操作
    # ═══════════════════════════════════════════════════════════════════════

    @mcp.tool()
    def derivation_get_step(step_number: int) -> dict[str, Any]:
        """
        取得單一步驟的詳細資訊

        用於檢視特定步驟的完整記錄，包含：
        - 操作類型和描述
        - 輸入/輸出表達式
        - SymPy 指令
        - 人類知識（notes、assumptions、limitations）

        Args:
            step_number: 步驟編號（1-based）

        Returns:
            步驟詳情

        Example:
            derivation_get_step(11)
            → {"success": True, "step": {"step_number": 11, "operation": "substitute", ...}}
        """
        session = _get_current_session()
        if session is None:
            return {
                "success": False,
                "error": "No active session.",
            }

        return session.get_step(step_number)

    @mcp.tool()
    def derivation_update_step(
        step_number: int,
        description: str | None = None,
        notes: str | None = None,
        assumptions: list[str] | None = None,
        limitations: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        更新步驟的元資料

        ═══════════════════════════════════════════════════════════════════════
        ⚠️ 只能更新「說明性」欄位，不能改變計算結果！
        ═══════════════════════════════════════════════════════════════════════

        可更新的欄位：
        - description: 步驟描述
        - notes: 人類洞見、觀察、解釋
        - assumptions: 這步的假設條件
        - limitations: 這步的限制

        不可更新（需要用 rollback 重做）：
        - 表達式
        - 操作類型

        Args:
            step_number: 步驟編號（1-based）
            description: 新描述（None = 不更新）
            notes: 新註記（None = 不更新）
            assumptions: 新假設（None = 不更新）
            limitations: 新限制（None = 不更新）

        Returns:
            更新結果

        Example:
            derivation_update_step(
                step_number=11,
                notes="此假設在高溫時不成立",
                limitations=["Valid only for T < 42°C"]
            )
        """
        session = _get_current_session()
        if session is None:
            return {
                "success": False,
                "error": "No active session.",
            }

        return session.update_step(
            step_number=step_number,
            description=description,
            notes=notes,
            assumptions=assumptions,
            limitations=limitations,
        )

    @mcp.tool()
    def derivation_delete_step(step_number: int) -> dict[str, Any]:
        """
        刪除單一步驟

        ═══════════════════════════════════════════════════════════════════════
        ⚠️ 只能刪除最後一步！
        ═══════════════════════════════════════════════════════════════════════

        如需刪除中間步驟，請使用 derivation_rollback() 回滾到該步驟之前，
        然後重新執行推導。

        Args:
            step_number: 步驟編號（必須是最後一步）

        Returns:
            刪除結果

        Example:
            derivation_delete_step(16)  # 假設有 16 步，刪除最後一步
            → {"success": True, "deleted_step": {...}, "new_step_count": 15}
        """
        session = _get_current_session()
        if session is None:
            return {
                "success": False,
                "error": "No active session.",
            }

        return session.delete_step(step_number)

    @mcp.tool()
    def derivation_rollback(to_step: int) -> dict[str, Any]:
        """
        回滾到指定步驟

        ═══════════════════════════════════════════════════════════════════════
        ⚡ 這是「跳回某一步」的核心工具！
        ═══════════════════════════════════════════════════════════════════════

        保留指定步驟及之前的所有步驟，刪除之後的步驟。
        回滾後可以從該步驟繼續推導（走不同的路徑）。

        Args:
            to_step: 回滾到的步驟編號（1-based，該步驟會保留）
                     0 = 清空所有步驟，從頭開始

        Returns:
            回滾結果，包含：
            - 刪除了哪些步驟
            - 當前的表達式
            - 新的步驟數

        Example:
            # 假設有 16 步，發現第 11 步開始走錯方向
            derivation_rollback(to_step=10)
            → {
                "success": True,
                "rolled_back_to": 10,
                "deleted_count": 6,
                "deleted_steps": [11, 12, 13, 14, 15, 16],
                "current_expression": "CL_int*(1 - f_b)",
                "message": "Rolled back to step 10. Deleted 6 step(s)."
              }
            # 現在可以從步驟 10 的表達式繼續，走不同的推導路徑
        """
        session = _get_current_session()
        if session is None:
            return {
                "success": False,
                "error": "No active session.",
            }

        return session.rollback_to_step(to_step)

    @mcp.tool()
    def derivation_insert_note(
        after_step: int,
        note: str,
        note_type: str = "observation",
        related_variables: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        在指定位置插入說明

        ═══════════════════════════════════════════════════════════════════════
        📝 用於在推導中間補充說明，不改變計算流程
        ═══════════════════════════════════════════════════════════════════════

        插入後會自動重新編號後續步驟。

        Args:
            after_step: 在此步驟之後插入（0 = 最開頭）
            note: 說明內容
            note_type: 說明類型
                - "assumption": 📋 假設條件
                - "limitation": ⚠️ 限制/警告
                - "observation": 💡 觀察/洞見
                - "correction": 🔧 修正建議
                - "clinical": 🏥 臨床意義
                - "physical": 🔬 物理意義
            related_variables: 相關變數

        Returns:
            插入結果

        Example:
            # 在步驟 5 和 6 之間插入說明
            derivation_insert_note(
                after_step=5,
                note="此處假設達穩態，實際臨床可能需要 5 個半衰期",
                note_type="clinical",
                related_variables=["t_half"]
            )
            → {"success": True, "inserted_at": 6, "new_step_count": 17}
        """
        session = _get_current_session()
        if session is None:
            return {
                "success": False,
                "error": "No active session.",
            }

        return session.insert_note_after_step(
            after_step=after_step,
            note=note,
            note_type=note_type,
            related_variables=related_variables,
        )

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
                        for s in (
                            session.current_expression.free_symbols
                            if session.current_expression
                            else []
                        )
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

    # ═══════════════════════════════════════════════════════════════════════
    # Handoff 機制：NSForge ↔ SymPy-MCP 無縫轉換
    # ═══════════════════════════════════════════════════════════════════════

    @mcp.tool()
    def derivation_export_for_sympy(
        include_variables: bool = True,
        include_current_expression: bool = True,
    ) -> dict[str, Any]:
        """
        導出當前推導狀態給 SymPy-MCP

        ═══════════════════════════════════════════════════════════════════════
        🔄 HANDOFF 機制 - 當 NSForge 無法處理時，交給 SymPy-MCP！
        ═══════════════════════════════════════════════════════════════════════

        使用時機：
        - 需要解 ODE/PDE
        - 需要矩陣運算
        - 需要複雜的 SymPy 操作（如 limit, series, dsolve）
        - NSForge 工具返回錯誤時

        這個工具會輸出：
        1. 所有已定義的變數（可直接貼到 intro_many）
        2. 當前表達式（可直接貼到 introduce_expression）
        3. 建議的下一步操作

        Returns:
            包含可直接使用的 SymPy-MCP 指令

        Example:
            # NSForge 中遇到無法處理的操作
            derivation_export_for_sympy()
            → {
                "intro_many_command": "intro_many(['k', 'T', 'Ea', 'R'], 'real positive')",
                "current_expression": "k * exp(-Ea/(R*T))",
                "suggested_actions": [...]
              }

            # 然後在 SymPy-MCP 中執行
            intro_many(['k', 'T', 'Ea', 'R'], 'real positive')
            introduce_expression("k * exp(-Ea/(R*T))", "arrhenius")
        """
        import sympy as sp

        session = _get_current_session()
        if session is None:
            return {
                "success": False,
                "error": "No active session. Nothing to export.",
            }

        result: dict[str, Any] = {
            "success": True,
            "session_id": session.session_id,
            "session_name": session.name,
        }

        # 收集變數（從當前表達式的 free_symbols）
        if include_variables and session.current_expression is not None:
            vars_list = [str(s) for s in session.current_expression.free_symbols]
            # 假設是 real positive（常見情況）
            result["variables"] = vars_list
            result["intro_many_command"] = f"intro_many({vars_list!r}, 'real positive')"
            result["intro_many_note"] = (
                "Adjust assumptions as needed (e.g., 'real', 'positive', 'integer')"
            )

        # 當前表達式
        if include_current_expression and session.current_expression is not None:
            expr_str = str(session.current_expression)
            result["current_expression"] = expr_str
            result["current_expression_latex"] = sp.latex(session.current_expression)
            result["introduce_expression_command"] = (
                f'introduce_expression("{expr_str}", "current")'
            )

        # 建議的 SymPy-MCP 操作
        result["suggested_actions"] = [
            {
                "action": "intro_many",
                "description": "首先定義變數（帶假設）",
                "example": result.get("intro_many_command", "intro_many(['x', 'y'], 'real')"),
            },
            {
                "action": "introduce_expression",
                "description": "載入表達式",
                "example": result.get(
                    "introduce_expression_command", 'introduce_expression("expr", "name")'
                ),
            },
            {
                "action": "solve_equation / dsolve_ode / etc.",
                "description": "執行 NSForge 無法處理的操作",
                "example": "dsolve_ode('diff(y, t) - k*y', 'y', 't')",
            },
            {
                "action": "print_latex_expression",
                "description": "確認結果",
                "example": "print_latex_expression('result_key')",
            },
        ]

        # 返回指引
        result["next_step_instructions"] = """
╔═══════════════════════════════════════════════════════════════════════╗
║  🔄 HANDOFF TO SYMPY-MCP                                              ║
╠═══════════════════════════════════════════════════════════════════════╣
║  1. Use intro_many() to define variables with assumptions             ║
║  2. Use introduce_expression() to load the expression                 ║
║  3. Perform the complex operation (dsolve_ode, solve_linear_system...)║
║  4. Use print_latex_expression() to verify result                     ║
║  5. Call derivation_import_from_sympy() to continue in NSForge        ║
╚═══════════════════════════════════════════════════════════════════════╝
"""

        return result

    @mcp.tool()
    def derivation_import_from_sympy(
        expression: str,
        operation_performed: str,
        sympy_tool_used: str,
        latex: str | None = None,
        notes: str | None = None,
        assumptions_used: list[str] | None = None,
        limitations: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        從 SymPy-MCP 導入結果回 NSForge

        ═══════════════════════════════════════════════════════════════════════
        🔄 HANDOFF 機制 - 把 SymPy-MCP 的結果帶回 NSForge 繼續！
        ═══════════════════════════════════════════════════════════════════════

        使用時機：
        - 在 SymPy-MCP 完成複雜計算後
        - 想要繼續使用 NSForge 的步進式記錄
        - 需要為 SymPy-MCP 的結果加入人類知識

        這個工具會：
        1. 將 SymPy-MCP 的結果記錄為新步驟
        2. 更新當前表達式
        3. 記錄使用的假設和限制

        Args:
            expression: SymPy-MCP 返回的表達式（字串格式）
            operation_performed: 執行了什麼操作（如 "Solved ODE"）
            sympy_tool_used: 使用的 SymPy-MCP 工具名稱
            latex: LaTeX 格式（可選，會自動生成）
            notes: 額外說明
            assumptions_used: 使用的假設（從 SymPy-MCP 的 intro 來的）
            limitations: 這個結果的限制

        Returns:
            導入結果

        Example:
            # SymPy-MCP 解完 ODE 後
            derivation_import_from_sympy(
                expression="C*exp(k*t)",
                operation_performed="Solved first-order ODE",
                sympy_tool_used="dsolve_ode",
                notes="General solution with integration constant C",
                assumptions_used=["k is real positive", "t is real"],
                limitations=["Requires initial condition to determine C"]
            )
        """
        import sympy as sp

        session = _get_current_session()
        if session is None:
            return {
                "success": False,
                "error": "No active session. Use derivation_start first.",
            }

        # 解析表達式
        try:
            expr = sp.sympify(expression)
        except Exception as e:
            return {
                "success": False,
                "error": f"Cannot parse expression: {e}",
            }

        # 生成 LaTeX
        latex_str = latex or sp.latex(expr)

        # 建立完整描述
        description = f"[SymPy-MCP: {sympy_tool_used}] {operation_performed}"

        # 新增步驟（使用 custom 類型）
        from nsforge.domain.derivation_session import OperationType, StepStatus

        step = session._add_step(
            operation=OperationType.CUSTOM,
            description=description,
            input_expressions={
                "sympy_tool": sympy_tool_used,
                "operation": operation_performed,
                "assumptions": ", ".join(assumptions_used) if assumptions_used else "",
            },
            output_expr=expr,
            sympy_command=f"# Imported from SymPy-MCP ({sympy_tool_used})",
            status=StepStatus.SUCCESS,
            notes=notes or "",
            assumptions=assumptions_used or [],
            limitations=limitations or [],
        )

        # 更新當前表達式
        session.current_expression = expr

        return {
            "success": True,
            "step_number": step.step_number,
            "expression": str(expr),
            "latex": latex_str,
            "operation": operation_performed,
            "sympy_tool": sympy_tool_used,
            "notes": notes,
            "assumptions": assumptions_used,
            "limitations": limitations,
            "message": "✅ Imported from SymPy-MCP. Continue with NSForge derivation tools.",
            "next_steps": [
                "derivation_simplify() - 簡化表達式",
                "derivation_substitute() - 代入值或其他表達式",
                "derivation_solve_for() - 求解其他變數",
                "derivation_add_note() - 加入說明",
                "derivation_complete() - 完成並存檔",
            ],
        }

    @mcp.tool()
    def derivation_handoff_status() -> dict[str, Any]:
        """
        顯示 Handoff 狀態和可用選項

        這個工具幫助你了解：
        1. NSForge 能做什麼
        2. 什麼需要交給 SymPy-MCP
        3. 當前推導的狀態

        Returns:
            Handoff 狀態和建議
        """
        session = _get_current_session()

        nsforge_capabilities = {
            "can_do": [
                "substitute - 代入表達式或值",
                "simplify - 簡化（自動選擇方法）",
                "solve_for - 求解單一變數",
                "differentiate - 微分",
                "integrate - 積分（定積分或不定積分）",
                "record_step - 記錄外部計算結果",
                "add_note - 加入人類知識",
            ],
            "needs_sympy_mcp": [
                "dsolve_ode - 解常微分方程",
                "dsolve_pde - 解偏微分方程",
                "solve_linear_system - 解線性方程組",
                "matrix operations - 矩陣運算（行列式、特徵值等）",
                "vector calculus - 向量微積分（curl, divergence, gradient）",
                "tensor operations - 張量運算",
                "limit - 極限",
                "series - 泰勒/傅立葉級數",
                "expand/factor/collect - 展開/因式分解/收集同類項",
            ],
        }

        if session is None:
            return {
                "has_active_session": False,
                "message": "No active session. Use derivation_start() to begin.",
                "nsforge_capabilities": nsforge_capabilities,
            }

        return {
            "has_active_session": True,
            "session_id": session.session_id,
            "session_name": session.name,
            "current_step": len(session.steps),
            "has_current_expression": session.current_expression is not None,
            "current_expression": str(session.current_expression)
            if session.current_expression
            else None,
            "variables_defined": [str(s) for s in session.current_expression.free_symbols]
            if session.current_expression
            else [],
            "nsforge_capabilities": nsforge_capabilities,
            "handoff_tools": {
                "to_sympy": "derivation_export_for_sympy() - 導出給 SymPy-MCP",
                "from_sympy": "derivation_import_from_sympy() - 從 SymPy-MCP 導入",
            },
            "workflow_hint": """
┌─────────────────────────────────────────────────────────────┐
│  NSForge ←→ SymPy-MCP Handoff Workflow                      │
├─────────────────────────────────────────────────────────────┤
│  1. derivation_export_for_sympy()                           │
│     → 取得 intro_many 和 introduce_expression 指令          │
│                                                             │
│  2. [SymPy-MCP] intro_many([...], 'real positive')          │
│     [SymPy-MCP] introduce_expression("...")                 │
│     [SymPy-MCP] dsolve_ode(...) / solve_linear_system(...)  │
│     [SymPy-MCP] print_latex_expression(...)                 │
│                                                             │
│  3. derivation_import_from_sympy(                           │
│       expression="...",                                     │
│       operation_performed="...",                            │
│       sympy_tool_used="dsolve_ode"                          │
│     )                                                       │
│     → 結果回到 NSForge，繼續步進式記錄                       │
└─────────────────────────────────────────────────────────────┘
""",
        }

    @mcp.tool()
    def derivation_prepare_for_optimization() -> dict[str, Any]:
        """
        準備推導結果給優化求解器（如 USolver）

        將 NSForge 推導的符號公式轉換為優化求解器可用的格式。

        工作流程：
        1. NSForge 推導修正後的公式（考慮領域知識）
        2. 調用此工具取得優化器輸入格式
        3. 送給 USolver 等優化器找最優解

        Returns:
            優化器輸入資料

        Example:
            # 在 NSForge 完成推導後
            derivation_prepare_for_optimization()
            → {
                "function_str": "dose/15.875 * exp(-0.476*t/15.875)",
                "variables": ["dose", "t"],
                "parameters": {"CL": 0.476, "V1": 15.875},
                "suggested_constraints": [
                    "dose >= 0.01",
                    "dose <= 0.10",
                    "t >= 0"
                ],
                "usolver_template": "..."
              }
        """
        session = _get_current_session()

        if session is None:
            return {
                "success": False,
                "error": "No active derivation session",
                "message": "Use derivation_start() first",
            }

        if session.current_expression is None:
            return {
                "success": False,
                "error": "No expression in current session",
                "message": "Complete a derivation first before preparing for optimization",
            }

        from sympy import latex

        expr = session.current_expression
        free_vars = sorted(expr.free_symbols, key=lambda x: str(x))

        # 分類變數：可優化變數 vs 參數
        # 簡單啟發式：小寫單字母或包含 "dose", "time" 等關鍵字的是變數
        optimization_vars = []
        parameters = {}

        for sym in free_vars:
            sym_str = str(sym)
            # 判斷是否為優化變數
            if any(keyword in sym_str.lower() for keyword in ["dose", "time", "t", "x", "y"]):
                optimization_vars.append(sym_str)
            else:
                # 參數（數值已從步驟中確定）
                # 嘗試從推導步驟中提取數值
                param_value = "unknown"
                for step in session.steps:
                    # DerivationStep 是 dataclass，使用屬性存取
                    notes = getattr(step, "notes", "") or ""
                    if sym_str in notes:
                        # 嘗試提取數值
                        import re
                        match = re.search(rf"{sym_str}\s*[=:]\s*([\d.]+)", notes)
                        if match:
                            param_value = float(match.group(1))
                            break
                parameters[sym_str] = param_value

        # 生成函數字串
        function_str = str(expr)
        latex_str = latex(expr)

        # 建議的約束條件（基於變數類型）
        suggested_constraints = []
        for var in optimization_vars:
            if "dose" in var.lower():
                suggested_constraints.extend([
                    f"{var} >= 0.001",  # 最小劑量 1mg
                    f"{var} <= 0.100",  # 最大劑量 100mg
                ])
            elif var.lower() in ["t", "time"]:
                suggested_constraints.append(f"{var} >= 0")
            else:
                suggested_constraints.append(f"{var} >= 0")

        # USolver 模板
        usolver_template = f"""
# USolver Optimization Template

Use usolver to optimize the following problem:

**Objective**: Find optimal values for {', '.join(optimization_vars)}

**Function**:
  {function_str}

**LaTeX**:
  {latex_str}

**Suggested Constraints**:
{chr(10).join('  - ' + c for c in suggested_constraints)}

**Example Constraints** (customize based on your problem):
  - Therapeutic window: C(t=5) >= 2.0 AND C(t=5) <= 4.0
  - Safety margin: C(t=30) >= 1.5
  - Cost constraint: dose * unit_cost <= budget

**Optimization Type**:
  - If linear/convex: Use CVXPY or HiGHS
  - If integer variables: Use OR-Tools or Z3
  - If complex constraints: Use Z3 SMT solver
"""

        return {
            "success": True,
            "session_id": session.session_id,
            "session_name": session.name,
            "function_str": function_str,
            "function_latex": latex_str,
            "variables": optimization_vars,
            "parameters": parameters,
            "suggested_constraints": suggested_constraints,
            "usolver_template": usolver_template,
            "workflow_next_steps": [
                "1. Review and customize constraints based on your problem domain",
                "2. Copy the USolver template to USolver MCP",
                "3. USolver will find optimal values",
                "4. Use optimal values to calculate final results",
            ],
            "example_usolver_call": f"""
usolver.solve(
    problem_type="convex_optimization",
    objective="minimize (target - {function_str})**2",
    constraints={suggested_constraints},
)
""",
        }
