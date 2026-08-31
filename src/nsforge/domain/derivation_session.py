"""
DerivationSession - 推導會話

有狀態的推導過程管理，支援：
- 多步驟追蹤
- 完整溯源記錄
- 持久化（防止中斷）
- 每步自動驗證

The "Forge" in NSForge means we CREATE new formulas through derivation.
"""

from __future__ import annotations

import contextlib
import copy
import json
import os
import tempfile
import threading
import uuid
from _thread import RLock
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import Any, Protocol, cast

import sympy as sp

from nsforge.domain.formula import Formula, FormulaParser, FormulaSource, ParseError
from nsforge.domain.safe_parse import parse_expression_allowlisted


class _Lockable(Protocol):
    """Structural type used by the synchronized-method decorator."""

    _lock: RLock


def _synchronized[Method: Callable[..., Any]](method: Method) -> Method:
    """Serialize one object's state access while allowing nested method calls."""

    @wraps(method)
    def locked(
        self: _Lockable,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        with self._lock:
            return method(self, *args, **kwargs)

    return cast(Method, locked)


class OperationType(Enum):
    """推導操作類型"""

    LOAD_FORMULA = "load_formula"  # 載入公式
    SUBSTITUTE = "substitute"  # 代入
    SIMPLIFY = "simplify"  # 簡化
    EXPAND = "expand"  # 展開
    FACTOR = "factor"  # 因式分解
    SOLVE = "solve"  # 求解
    DIFFERENTIATE = "differentiate"  # 微分
    INTEGRATE = "integrate"  # 積分
    COMBINE = "combine"  # 組合兩個公式
    CUSTOM = "custom"  # 自定義操作


class StepStatus(Enum):
    """步驟狀態"""

    SUCCESS = "success"
    FAILED = "failed"
    PENDING_VERIFICATION = "pending_verification"


@dataclass
class DerivationStep:
    """
    推導步驟記錄

    完整記錄每一步操作，這是學術價值的關鍵。
    包含人類知識（notes）和約束條件（assumptions/limitations）。
    """

    step_number: int
    operation: OperationType
    description: str

    # 輸入輸出
    input_expressions: dict[str, str]  # {"formula_id": "expression_str"}
    output_expression: str
    output_latex: str

    # SymPy 執行記錄
    sympy_command: str  # 實際執行的 SymPy 指令

    # 🆕 人類知識注入
    notes: str = ""  # 人類洞見、觀察、解釋
    assumptions: list[str] = field(default_factory=list)  # 這步的假設
    limitations: list[str] = field(default_factory=list)  # 這步的限制

    # 驗證
    status: StepStatus = StepStatus.SUCCESS
    verification_result: str = ""

    # 時間戳
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return copy.deepcopy(
            {
                "step_number": self.step_number,
                "operation": self.operation.value,
                "description": self.description,
                "input_expressions": self.input_expressions,
                "output_expression": self.output_expression,
                "output_latex": self.output_latex,
                "sympy_command": self.sympy_command,
                # 🆕 人類知識
                "notes": self.notes,
                "assumptions": self.assumptions,
                "limitations": self.limitations,
                # 驗證
                "status": self.status.value,
                "verification_result": self.verification_result,
                "timestamp": self.timestamp,
            }
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DerivationStep:
        return cls(
            step_number=data["step_number"],
            operation=OperationType(data["operation"]),
            description=data["description"],
            input_expressions=data["input_expressions"],
            output_expression=data["output_expression"],
            output_latex=data["output_latex"],
            sympy_command=data["sympy_command"],
            # 🆕 人類知識
            notes=data.get("notes", ""),
            assumptions=data.get("assumptions", []),
            limitations=data.get("limitations", []),
            # 驗證
            status=StepStatus(data["status"]),
            verification_result=data.get("verification_result", ""),
            timestamp=data.get("timestamp", ""),
        )


class SessionStatus(Enum):
    """會話狀態"""

    ACTIVE = "active"  # 進行中
    PAUSED = "paused"  # 暫停（已持久化）
    COMPLETED = "completed"  # 完成
    FAILED = "failed"  # 失敗


@dataclass
class DerivationSession:
    """
    推導會話

    管理一次完整的推導過程，支援持久化。
    """

    # 識別
    session_id: str
    name: str
    description: str = ""

    # 狀態
    status: SessionStatus = SessionStatus.ACTIVE
    formulas: dict[str, Formula] = field(default_factory=dict)
    current_expression: sp.Basic | None = None  # Basic 包含 Expr 和 Equality
    current_formula_id: str | None = None

    # 歷史記錄
    steps: list[DerivationStep] = field(default_factory=list)

    # 元資料
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    author: str = ""
    tags: list[str] = field(default_factory=list)

    # 持久化路徑
    _persist_path: Path | None = None
    _lock: RLock = field(default_factory=RLock, init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if not self.session_id:
            self.session_id = str(uuid.uuid4())[:8]

    @contextlib.contextmanager
    def transaction(self) -> Iterator[None]:
        """Hold this session lock across a multi-step tool-layer operation."""
        with self._lock:
            yield

    @property
    @_synchronized
    def step_count(self) -> int:
        return len(self.steps)

    @property
    @_synchronized
    def formula_ids(self) -> list[str]:
        return list(self.formulas.keys())

    @_synchronized
    def _update_timestamp(self) -> None:
        self.updated_at = datetime.now().isoformat()

    @_synchronized
    def _add_step(
        self,
        operation: OperationType,
        description: str,
        input_expressions: dict[str, str],
        output_expr: sp.Basic,  # Basic 包含 Expr 和 Equality
        sympy_command: str,
        status: StepStatus = StepStatus.SUCCESS,
        # 🆕 人類知識
        notes: str = "",
        assumptions: list[str] | None = None,
        limitations: list[str] | None = None,
        persist: bool = True,
    ) -> DerivationStep:
        """新增步驟記錄（含人類知識）"""
        step = DerivationStep(
            step_number=len(self.steps) + 1,
            operation=operation,
            description=description,
            input_expressions=input_expressions,
            output_expression=str(output_expr),
            output_latex=sp.latex(output_expr),
            sympy_command=sympy_command,
            notes=notes,
            assumptions=assumptions or [],
            limitations=limitations or [],
            status=status,
        )
        self.steps.append(step)
        self._update_timestamp()

        # 自動持久化
        if persist and self._persist_path:
            self.save()

        return step

    @_synchronized
    def record_external_step(
        self,
        *,
        operation: OperationType,
        description: str,
        input_expressions: dict[str, str],
        output_expr: sp.Basic,
        sympy_command: str,
        status: StepStatus = StepStatus.SUCCESS,
        notes: str = "",
        assumptions: list[str] | None = None,
        limitations: list[str] | None = None,
        set_as_current: bool = True,
    ) -> DerivationStep:
        """Append an externally computed step and persist one coherent snapshot.

        Tool-layer record/import calls used to let ``_add_step`` auto-save before
        updating ``current_expression``, then save a second time.  This operation
        makes append + current update + persistence one transaction and restores
        in-memory state if the atomic write fails.
        """
        previous_step_count = len(self.steps)
        previous_expression = self.current_expression
        previous_status = self.status
        previous_updated_at = self.updated_at
        try:
            step = self._add_step(
                operation=operation,
                description=description,
                input_expressions=input_expressions,
                output_expr=output_expr,
                sympy_command=sympy_command,
                status=status,
                notes=notes,
                assumptions=assumptions,
                limitations=limitations,
                persist=False,
            )
            if set_as_current:
                self.current_expression = output_expr
            if self._persist_path:
                self.save()
        except BaseException:
            del self.steps[previous_step_count:]
            self.current_expression = previous_expression
            self.status = previous_status
            self.updated_at = previous_updated_at
            raise
        return copy.deepcopy(step)

    # ═══════════════════════════════════════════════════════════════════════
    # 核心操作
    # ═══════════════════════════════════════════════════════════════════════

    @_synchronized
    def load_formula(
        self,
        formula_input: str | dict[str, Any],
        formula_id: str | None = None,
        source: FormulaSource = FormulaSource.USER_INPUT,
        source_detail: str = "",
        set_as_current: bool = True,
        **metadata: Any,
    ) -> dict[str, Any]:
        """
        載入公式

        Args:
            formula_input: 公式輸入（多種格式）
            formula_id: 公式 ID（可選，自動生成）
            source: 來源標記
            source_detail: 詳細來源
            set_as_current: 是否設為當前表達式
            **metadata: 額外元資料

        Returns:
            操作結果
        """
        # 生成 ID
        if formula_id is None:
            formula_id = f"f{len(self.formulas) + 1}"

        # 解析公式
        result = FormulaParser.parse(
            formula_input,
            formula_id,
            source=source,
            source_detail=source_detail,
            **metadata,
        )

        if isinstance(result, ParseError):
            return result.to_dict()

        # 儲存公式
        self.formulas[formula_id] = result

        if set_as_current:
            self.current_expression = result.expression
            self.current_formula_id = formula_id

        # 記錄步驟
        self._add_step(
            operation=OperationType.LOAD_FORMULA,
            description=f"Load formula '{formula_id}' from {source.value}",
            input_expressions={formula_id: result.original_input},
            output_expr=result.expression,
            sympy_command=f"parse('{result.original_input}')",
        )

        return {
            "success": True,
            "formula_id": formula_id,
            "expression": result.sympy_str,
            "latex": result.latex,
            "variables": list(result.symbol_names),
            "source": source.value,
            "step_number": self.step_count,
        }

    @_synchronized
    def substitute(
        self,
        target_var: str,
        replacement: str | sp.Expr,
        in_formula: str | None = None,
        description: str = "",
        # 🆕 人類知識
        notes: str = "",
        assumptions: list[str] | None = None,
        limitations: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        代入操作

        Args:
            target_var: 要替換的變數
            replacement: 替換的表達式
            in_formula: 在哪個公式中代入（預設為當前）
            description: 操作描述
            notes: 人類洞見、觀察、解釋
            assumptions: 這步的假設條件
            limitations: 這步的限制

        Returns:
            操作結果
        """
        # 確定目標表達式
        if in_formula:
            if in_formula not in self.formulas:
                return {
                    "success": False,
                    "error": f"Formula '{in_formula}' not found",
                    "available_formulas": self.formula_ids,
                }
            expr = self.formulas[in_formula].expression
        elif self.current_expression is not None:
            expr = self.current_expression
        else:
            return {
                "success": False,
                "error": "No current expression. Load a formula first.",
            }

        # 檢查變數是否存在
        symbol_names = {str(s) for s in expr.free_symbols}
        if target_var not in symbol_names:
            return {
                "success": False,
                "error": f"Variable '{target_var}' not found in expression",
                "available_variables": list(symbol_names),
            }

        # 解析替換表達式
        if isinstance(replacement, str):
            try:
                replacement_expr = parse_expression_allowlisted(replacement)
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Cannot parse replacement: {e}",
                }
        else:
            replacement_expr = replacement

        # 執行代入
        target_symbol = sp.Symbol(target_var)
        try:
            new_expr = expr.subs(target_symbol, replacement_expr)
        except Exception as e:
            return {
                "success": False,
                "error": f"Substitution failed: {e}",
            }

        # 更新當前表達式
        self.current_expression = new_expr

        # 記錄步驟
        desc = description or f"Substitute {target_var} = {replacement}"
        self._add_step(
            operation=OperationType.SUBSTITUTE,
            description=desc,
            input_expressions={
                "original": str(expr),
                "replacement": f"{target_var} = {replacement}",
            },
            output_expr=new_expr,
            sympy_command=f"expr.subs({target_var}, {replacement})",
            notes=notes,
            assumptions=assumptions,
            limitations=limitations,
        )

        return {
            "success": True,
            "expression": str(new_expr),
            "latex": sp.latex(new_expr),
            "step_number": self.step_count,
            "substituted": {target_var: str(replacement_expr)},
            "notes": notes,
            "assumptions": assumptions or [],
            "limitations": limitations or [],
        }

    @_synchronized
    def simplify(
        self,
        method: str = "auto",
        description: str = "",
        # 🆕 人類知識
        notes: str = "",
        assumptions: list[str] | None = None,
        limitations: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        簡化當前表達式

        Args:
            method: 簡化方法 ("auto", "trig", "radical", "expand_then_simplify")
            description: 操作描述
            notes: 人類洞見
            assumptions: 這步的假設
            limitations: 這步的限制

        Returns:
            操作結果
        """
        if self.current_expression is None:
            return {
                "success": False,
                "error": "No current expression to simplify",
            }

        original = self.current_expression

        try:
            if method == "trig":
                new_expr = sp.trigsimp(original)
                cmd = "trigsimp(expr)"
            elif method == "radical":
                new_expr = sp.radsimp(original)
                cmd = "radsimp(expr)"
            elif method == "expand_then_simplify":
                new_expr = sp.simplify(sp.expand(original))
                cmd = "simplify(expand(expr))"
            else:  # auto
                new_expr = sp.simplify(original)
                cmd = "simplify(expr)"
        except Exception as e:
            return {
                "success": False,
                "error": f"Simplification failed: {e}",
            }

        self.current_expression = new_expr

        # 記錄步驟
        desc = description or f"Simplify using {method} method"
        self._add_step(
            operation=OperationType.SIMPLIFY,
            description=desc,
            input_expressions={"original": str(original)},
            output_expr=new_expr,
            sympy_command=cmd,
            notes=notes,
            assumptions=assumptions,
            limitations=limitations,
        )

        return {
            "success": True,
            "expression": str(new_expr),
            "latex": sp.latex(new_expr),
            "step_number": self.step_count,
            "method": method,
            "changed": str(original) != str(new_expr),
            "notes": notes,
            "assumptions": assumptions or [],
            "limitations": limitations or [],
        }

    @_synchronized
    def solve_for(
        self,
        variable: str,
        description: str = "",
        # 🆕 人類知識
        notes: str = "",
        assumptions: list[str] | None = None,
        limitations: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        求解變數

        Args:
            variable: 要求解的變數
            description: 操作描述
            notes: 人類洞見
            assumptions: 這步的假設
            limitations: 這步的限制

        Returns:
            操作結果（可能有多個解）
        """
        if self.current_expression is None:
            return {
                "success": False,
                "error": "No current expression to solve",
            }

        expr = self.current_expression
        var_symbol = sp.Symbol(variable)

        # 檢查變數是否存在
        if var_symbol not in expr.free_symbols:
            return {
                "success": False,
                "error": f"Variable '{variable}' not in expression",
                "available_variables": [str(s) for s in expr.free_symbols],
            }

        try:
            solutions = sp.solve(expr, var_symbol)
        except Exception as e:
            return {
                "success": False,
                "error": f"Solve failed: {e}",
            }

        if not solutions:
            return {
                "success": False,
                "error": f"No solution found for {variable}",
            }

        # 取第一個解作為當前表達式
        first_solution = solutions[0]
        solution_eq = sp.Eq(var_symbol, first_solution)
        self.current_expression = solution_eq

        # 記錄步驟
        desc = description or f"Solve for {variable}"
        self._add_step(
            operation=OperationType.SOLVE,
            description=desc,
            input_expressions={"equation": str(expr)},
            output_expr=solution_eq,
            sympy_command=f"solve(expr, {variable})",
            notes=notes,
            assumptions=assumptions,
            limitations=limitations,
        )

        return {
            "success": True,
            "variable": variable,
            "solutions": [str(s) for s in solutions],
            "solutions_latex": [sp.latex(s) for s in solutions],
            "primary_solution": str(first_solution),
            "step_number": self.step_count,
            "notes": notes,
            "assumptions": assumptions or [],
            "limitations": limitations or [],
        }

    @_synchronized
    def differentiate(
        self,
        variable: str,
        order: int = 1,
        description: str = "",
        # 🆕 人類知識
        notes: str = "",
        assumptions: list[str] | None = None,
        limitations: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        微分

        Args:
            variable: 微分變數
            order: 階數
            description: 操作描述
            notes: 人類洞見
            assumptions: 這步的假設
            limitations: 這步的限制
        """
        if self.current_expression is None:
            return {"success": False, "error": "No current expression"}

        original = self.current_expression
        var_symbol = sp.Symbol(variable)

        try:
            new_expr = sp.diff(original, var_symbol, order)
        except Exception as e:
            return {"success": False, "error": f"Differentiation failed: {e}"}

        self.current_expression = new_expr

        desc = description or f"Differentiate w.r.t. {variable} (order {order})"
        self._add_step(
            operation=OperationType.DIFFERENTIATE,
            description=desc,
            input_expressions={"original": str(original)},
            output_expr=new_expr,
            sympy_command=f"diff(expr, {variable}, {order})",
            notes=notes,
            assumptions=assumptions,
            limitations=limitations,
        )

        return {
            "success": True,
            "expression": str(new_expr),
            "latex": sp.latex(new_expr),
            "step_number": self.step_count,
            "notes": notes,
            "assumptions": assumptions or [],
            "limitations": limitations or [],
        }

    @_synchronized
    def integrate(
        self,
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
        積分

        Args:
            variable: 積分變數
            lower: 下界
            upper: 上界
            description: 操作描述
            notes: 人類洞見
            assumptions: 這步的假設
            limitations: 這步的限制
        """
        if self.current_expression is None:
            return {"success": False, "error": "No current expression"}

        original = self.current_expression
        var_symbol = sp.Symbol(variable)

        try:
            if lower is not None and upper is not None:
                lower_val = parse_expression_allowlisted(lower)
                upper_val = parse_expression_allowlisted(upper)
                new_expr = sp.integrate(original, (var_symbol, lower_val, upper_val))
                cmd = f"integrate(expr, ({variable}, {lower}, {upper}))"
            else:
                new_expr = sp.integrate(original, var_symbol)
                cmd = f"integrate(expr, {variable})"
        except Exception as e:
            return {"success": False, "error": f"Integration failed: {e}"}

        self.current_expression = new_expr

        desc = description or f"Integrate w.r.t. {variable}"
        self._add_step(
            operation=OperationType.INTEGRATE,
            description=desc,
            input_expressions={"original": str(original)},
            output_expr=new_expr,
            sympy_command=cmd,
            notes=notes,
            assumptions=assumptions,
            limitations=limitations,
        )

        return {
            "success": True,
            "expression": str(new_expr),
            "latex": sp.latex(new_expr),
            "step_number": self.step_count,
            "notes": notes,
            "assumptions": assumptions or [],
            "limitations": limitations or [],
        }

    # ═══════════════════════════════════════════════════════════════════════
    # 會話管理
    # ═══════════════════════════════════════════════════════════════════════

    @_synchronized
    def get_steps(self) -> list[dict[str, Any]]:
        """取得所有步驟"""
        return [s.to_dict() for s in self.steps]

    # ═══════════════════════════════════════════════════════════════════════
    # 步驟 CRUD 操作
    # ═══════════════════════════════════════════════════════════════════════

    @_synchronized
    def get_step(self, step_number: int) -> dict[str, Any]:
        """
        取得單一步驟詳情

        Args:
            step_number: 步驟編號（1-based）

        Returns:
            步驟詳情
        """
        if step_number < 1 or step_number > len(self.steps):
            return {
                "success": False,
                "error": f"Step {step_number} not found. Valid range: 1-{len(self.steps)}",
            }

        step = self.steps[step_number - 1]
        return {
            "success": True,
            "step": step.to_dict(),
        }

    @_synchronized
    def update_step(
        self,
        step_number: int,
        description: str | None = None,
        notes: str | None = None,
        assumptions: list[str] | None = None,
        limitations: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        更新步驟的元資料（不改變計算結果）

        Args:
            step_number: 步驟編號（1-based）
            description: 新描述（None 表示不更新）
            notes: 新註記（None 表示不更新）
            assumptions: 新假設（None 表示不更新）
            limitations: 新限制（None 表示不更新）

        Returns:
            更新結果
        """
        if step_number < 1 or step_number > len(self.steps):
            return {
                "success": False,
                "error": f"Step {step_number} not found. Valid range: 1-{len(self.steps)}",
            }

        step = self.steps[step_number - 1]
        updated_fields = []

        if description is not None:
            step.description = description
            updated_fields.append("description")

        if notes is not None:
            step.notes = notes
            updated_fields.append("notes")

        if assumptions is not None:
            step.assumptions = assumptions
            updated_fields.append("assumptions")

        if limitations is not None:
            step.limitations = limitations
            updated_fields.append("limitations")

        self._update_timestamp()

        # 自動持久化
        if self._persist_path:
            self.save()

        return {
            "success": True,
            "step_number": step_number,
            "updated_fields": updated_fields,
            "step": step.to_dict(),
            "message": f"Step {step_number} updated: {', '.join(updated_fields)}",
        }

    @_synchronized
    def delete_step(self, step_number: int) -> dict[str, Any]:
        """
        刪除單一步驟（只能刪除最後一步，否則會破壞連續性）

        Args:
            step_number: 步驟編號（1-based）

        Returns:
            刪除結果
        """
        if step_number < 1 or step_number > len(self.steps):
            return {
                "success": False,
                "error": f"Step {step_number} not found. Valid range: 1-{len(self.steps)}",
            }

        if step_number != len(self.steps):
            return {
                "success": False,
                "error": f"Can only delete the last step ({len(self.steps)}). Use rollback_to_step() to delete multiple steps.",
            }

        deleted_step = self.steps.pop()
        self._update_timestamp()

        # 恢復前一步的表達式
        if self.steps:
            last_step = self.steps[-1]
            self.current_expression = parse_expression_allowlisted(last_step.output_expression)
        else:
            self.current_expression = None

        # 自動持久化
        if self._persist_path:
            self.save()

        return {
            "success": True,
            "deleted_step": deleted_step.to_dict(),
            "new_step_count": len(self.steps),
            "current_expression": str(self.current_expression) if self.current_expression else None,
            "message": f"Step {step_number} deleted.",
        }

    @_synchronized
    def rollback_to_step(self, step_number: int) -> dict[str, Any]:
        """
        回滾到指定步驟（刪除該步驟之後的所有步驟）

        Args:
            step_number: 回滾到的步驟編號（1-based，該步驟會保留）

        Returns:
            回滾結果
        """
        if step_number < 0 or step_number > len(self.steps):
            return {
                "success": False,
                "error": f"Invalid step number. Valid range: 0-{len(self.steps)} (0 = reset all)",
            }

        if step_number == len(self.steps):
            return {
                "success": True,
                "message": "Already at this step, nothing to rollback.",
                "step_count": len(self.steps),
            }

        # 記錄將被刪除的步驟
        deleted_steps = self.steps[step_number:]
        deleted_count = len(deleted_steps)

        # 執行回滾
        self.steps = self.steps[:step_number]

        # 恢復當前表達式
        if self.steps:
            last_step = self.steps[-1]
            self.current_expression = parse_expression_allowlisted(last_step.output_expression)
        else:
            # 回滾到 0，清空所有
            self.current_expression = None

        self._update_timestamp()

        # 自動持久化
        if self._persist_path:
            self.save()

        return {
            "success": True,
            "rolled_back_to": step_number,
            "deleted_count": deleted_count,
            "deleted_steps": [s.step_number for s in deleted_steps],
            "new_step_count": len(self.steps),
            "current_expression": str(self.current_expression) if self.current_expression else None,
            "current_latex": sp.latex(self.current_expression) if self.current_expression else None,
            "message": f"Rolled back to step {step_number}. Deleted {deleted_count} step(s).",
        }

    @_synchronized
    def insert_note_after_step(
        self,
        after_step: int,
        note: str,
        note_type: str = "observation",
        related_variables: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        在指定步驟之後插入說明（會重新編號後續步驟）

        Args:
            after_step: 在此步驟之後插入（0 = 最開頭）
            note: 說明內容
            note_type: 說明類型
            related_variables: 相關變數

        Returns:
            插入結果
        """
        if after_step < 0 or after_step > len(self.steps):
            return {
                "success": False,
                "error": f"Invalid position. Valid range: 0-{len(self.steps)}",
            }

        # 取得插入位置的表達式
        if after_step == 0:
            output_expr = self.current_expression or sp.Integer(0)
        else:
            output_expr = parse_expression_allowlisted(self.steps[after_step - 1].output_expression)

        # 建立新步驟
        note_emoji = {
            "assumption": "📋",
            "limitation": "⚠️",
            "observation": "💡",
            "correction": "🔧",
            "clinical": "🏥",
            "physical": "🔬",
        }.get(note_type, "📝")

        new_step = DerivationStep(
            step_number=after_step + 1,  # 暫時編號，之後會重新編號
            operation=OperationType.CUSTOM,
            description=f"{note_emoji} [{note_type.upper()}] {note}"
            + (f"\n   Related: {', '.join(related_variables)}" if related_variables else ""),
            input_expressions={
                "note_type": note_type,
                "related_variables": str(related_variables or []),
            },
            output_expression=str(output_expr),
            output_latex=sp.latex(output_expr),
            sympy_command="# Note (no computation)",
        )

        # 插入步驟
        self.steps.insert(after_step, new_step)

        # 重新編號
        for i, step in enumerate(self.steps):
            step.step_number = i + 1

        self._update_timestamp()

        # 自動持久化
        if self._persist_path:
            self.save()

        return {
            "success": True,
            "inserted_at": after_step + 1,
            "new_step_count": len(self.steps),
            "message": f"Note inserted at step {after_step + 1}. Steps renumbered.",
        }

    @_synchronized
    def get_current(self) -> dict[str, Any]:
        """取得當前狀態"""
        return {
            "session_id": self.session_id,
            "name": self.name,
            "status": self.status.value,
            "step_count": self.step_count,
            "current_expression": str(self.current_expression) if self.current_expression else None,
            "current_latex": sp.latex(self.current_expression) if self.current_expression else None,
            "formulas_loaded": self.formula_ids,
        }

    @_synchronized
    def complete(self) -> dict[str, Any]:
        """完成推導"""
        if self.current_expression is None:
            return {
                "success": False,
                "error": "No result expression. Perform some derivation steps first.",
            }

        self.status = SessionStatus.COMPLETED
        self._update_timestamp()

        # 建立完整的推導記錄
        result = {
            "success": True,
            "session_id": self.session_id,
            "name": self.name,
            "status": self.status.value,
            "final_expression": str(self.current_expression),
            "final_latex": sp.latex(self.current_expression),
            "total_steps": self.step_count,
            "steps": self.get_steps(),
            "formulas_used": {fid: f.to_dict() for fid, f in self.formulas.items()},
            "provenance": {
                "created_at": self.created_at,
                "completed_at": self.updated_at,
                "author": self.author,
            },
        }

        if self._persist_path:
            self.save()

        return copy.deepcopy(result)

    # ═══════════════════════════════════════════════════════════════════════
    # 持久化
    # ═══════════════════════════════════════════════════════════════════════

    @_synchronized
    def to_dict(self) -> dict[str, Any]:
        """序列化為字典"""
        return copy.deepcopy(
            {
                "session_id": self.session_id,
                "name": self.name,
                "description": self.description,
                "status": self.status.value,
                "formulas": {fid: f.to_dict() for fid, f in self.formulas.items()},
                "current_expression": (
                    str(self.current_expression) if self.current_expression else None
                ),
                "current_formula_id": self.current_formula_id,
                "steps": [s.to_dict() for s in self.steps],
                "created_at": self.created_at,
                "updated_at": self.updated_at,
                "author": self.author,
                "tags": self.tags,
            }
        )

    @_synchronized
    def save(self, path: Path | None = None) -> Path:
        """
        保存會話到檔案

        Args:
            path: 保存路徑（可選）

        Returns:
            保存的檔案路徑
        """
        save_path = path or self._persist_path
        if save_path is None:
            save_path = Path(f"session_{self.session_id}.json")

        save_path.parent.mkdir(parents=True, exist_ok=True)

        # Atomic write: temp file in the same dir + os.replace, so a concurrent
        # reader or a crash never sees a half-written session file.
        tmp_fd, tmp_name = tempfile.mkstemp(
            dir=str(save_path.parent), prefix=f".{save_path.stem}_", suffix=".tmp"
        )
        previous_status = self.status
        if self.status == SessionStatus.ACTIVE:
            # Preserve the historical "save pauses an active session" behavior,
            # but serialize the post-save status instead of writing ACTIVE and
            # then leaving memory PAUSED.  Do this only after mkstemp succeeds so
            # an allocation failure cannot mutate the session.
            self.status = SessionStatus.PAUSED
        try:
            with open(tmp_fd, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
            os.replace(tmp_name, save_path)
        except BaseException:
            self.status = previous_status
            with contextlib.suppress(OSError):
                os.unlink(tmp_name)
            raise

        self._persist_path = save_path

        return save_path

    @classmethod
    def load(cls, path: Path) -> DerivationSession:
        """
        從檔案載入會話

        Args:
            path: 檔案路徑

        Returns:
            DerivationSession 實例
        """
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        session = cls(
            session_id=data["session_id"],
            name=data["name"],
            description=data.get("description", ""),
            status=SessionStatus(data["status"]),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            author=data.get("author", ""),
            tags=data.get("tags", []),
        )

        # 恢復公式（簡化版，只恢復表達式）
        for fid, fdata in data.get("formulas", {}).items():
            result = FormulaParser.parse(
                fdata["expression"],
                fid,
                source=FormulaSource(fdata.get("source", "user_input")),
            )
            if isinstance(result, Formula):
                session.formulas[fid] = result

        # 恢復當前表達式
        if data.get("current_expression"):
            session.current_expression = parse_expression_allowlisted(data["current_expression"])
        session.current_formula_id = data.get("current_formula_id")

        # 恢復步驟
        session.steps = [DerivationStep.from_dict(s) for s in data.get("steps", [])]

        # 設定持久化路徑
        session._persist_path = path

        # 恢復為 ACTIVE
        if session.status == SessionStatus.PAUSED:
            session.status = SessionStatus.ACTIVE

        return session


# ═══════════════════════════════════════════════════════════════════════════
# 會話管理器
# ═══════════════════════════════════════════════════════════════════════════


class SessionManager:
    """
    會話管理器

    管理多個推導會話，支援持久化。
    """

    def __init__(self, sessions_dir: Path | None = None):
        self.sessions: dict[str, DerivationSession] = {}
        self._lock = threading.RLock()
        self.sessions_dir = sessions_dir or Path("derivation_sessions")
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

        # 載入已存在的會話
        self._load_existing_sessions()

    def _load_existing_sessions(self) -> None:
        """載入已存在的會話"""
        for session_file in self.sessions_dir.glob("session_*.json"):
            try:
                session = DerivationSession.load(session_file)
                self.sessions[session.session_id] = session
            except Exception:
                pass  # 跳過損壞的檔案

    def create(
        self,
        name: str,
        description: str = "",
        author: str = "",
        auto_persist: bool = True,
    ) -> DerivationSession:
        """建立新會話"""
        session = DerivationSession(
            session_id="",  # 會自動生成
            name=name,
            description=description,
            author=author,
        )

        if auto_persist:
            session._persist_path = self.sessions_dir / f"session_{session.session_id}.json"
            session.save()

        with self._lock:
            self.sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> DerivationSession | None:
        """取得會話"""
        with self._lock:
            return self.sessions.get(session_id)

    def list_sessions(self) -> list[dict[str, Any]]:
        """列出所有會話"""
        with self._lock:
            sessions = list(self.sessions.values())
        summaries = []
        for session in sessions:
            with session._lock:
                summaries.append(
                    {
                        "session_id": session.session_id,
                        "name": session.name,
                        "status": session.status.value,
                        "step_count": session.step_count,
                        "created_at": session.created_at,
                        "updated_at": session.updated_at,
                    }
                )
        return summaries

    def delete(self, session_id: str) -> bool:
        """刪除會話"""
        with self._lock:
            session = self.sessions.pop(session_id, None)
        if session is None:
            return False
        with session._lock:
            if session._persist_path and session._persist_path.exists():
                session._persist_path.unlink()

        return True


# 全域會話管理器（雙重檢查鎖，避免並發初始化競態）
_manager: SessionManager | None = None
_manager_lock = threading.Lock()


def get_session_manager(sessions_dir: Path | None = None) -> SessionManager:
    """取得全域會話管理器"""
    global _manager
    if _manager is None:
        with _manager_lock:
            if _manager is None:
                _manager = SessionManager(sessions_dir)
    return _manager
