"""
測試步驟 CRUD 功能
"""

from nsforge.domain.derivation_session import DerivationSession


def test_step_crud():
    """測試步驟的 CRUD 操作"""
    # 建立測試會話
    session = DerivationSession(session_id="test", name="CRUD Test")

    # ═══════════════════════════════════════════════════════════════════════
    # Create: 建立步驟
    # ═══════════════════════════════════════════════════════════════════════
    session.load_formula("x**2 + y**2", formula_id="f1")
    session.load_formula("a*b + x", formula_id="f2")  # 確保有 x 變數
    session.substitute("x", "a+b")

    assert session.step_count == 3, f"Expected 3 steps, got {session.step_count}"
    print(f"✅ Create: {session.step_count} steps created")

    # ═══════════════════════════════════════════════════════════════════════
    # Read: 讀取步驟
    # ═══════════════════════════════════════════════════════════════════════
    result = session.get_step(2)
    assert result["success"], f"Get step failed: {result}"
    assert result["step"]["step_number"] == 2
    print("✅ Read: Step 2 retrieved successfully")

    # 測試邊界情況
    result = session.get_step(0)
    assert not result["success"], "Step 0 should fail"

    result = session.get_step(100)
    assert not result["success"], "Step 100 should fail"
    print("✅ Read: Edge cases handled correctly")

    # ═══════════════════════════════════════════════════════════════════════
    # Update: 更新步驟
    # ═══════════════════════════════════════════════════════════════════════
    result = session.update_step(
        step_number=2,
        notes="這是測試註記",
        assumptions=["假設 a > 0"],
        limitations=["僅適用於正數"],
    )
    assert result["success"], f"Update failed: {result}"
    assert "notes" in result["updated_fields"]
    assert "assumptions" in result["updated_fields"]
    assert "limitations" in result["updated_fields"]
    print(f"✅ Update: Step 2 updated - {result['updated_fields']}")

    # 驗證更新成功
    result = session.get_step(2)
    assert result["step"]["notes"] == "這是測試註記"
    assert result["step"]["assumptions"] == ["假設 a > 0"]
    print("✅ Update: Verified update persisted")

    # ═══════════════════════════════════════════════════════════════════════
    # Delete: 刪除步驟（只能刪最後一步）
    # ═══════════════════════════════════════════════════════════════════════
    # 嘗試刪除非最後一步（應該失敗）
    result = session.delete_step(1)
    assert not result["success"], "Should not be able to delete step 1"
    print("✅ Delete: Correctly rejected deletion of non-last step")

    # 刪除最後一步
    result = session.delete_step(3)
    assert result["success"], f"Delete last step failed: {result}"
    assert session.step_count == 2
    print(f"✅ Delete: Last step deleted, now {session.step_count} steps")

    # ═══════════════════════════════════════════════════════════════════════
    # Rollback: 回滾到指定步驟
    # ═══════════════════════════════════════════════════════════════════════
    # 先加回一些步驟
    session.load_formula("z**3", formula_id="f3")
    session.substitute("z", "x+1")
    assert session.step_count == 4

    # 回滾到步驟 1
    result = session.rollback_to_step(1)
    assert result["success"], f"Rollback failed: {result}"
    assert result["deleted_count"] == 3
    assert session.step_count == 1
    print(f"✅ Rollback: Rolled back to step 1, deleted {result['deleted_count']} steps")

    # 回滾到 0（清空所有）
    result = session.rollback_to_step(0)
    assert result["success"]
    assert session.step_count == 0
    assert session.current_expression is None
    print("✅ Rollback: Rolled back to 0, cleared all steps")

    # ═══════════════════════════════════════════════════════════════════════
    # Insert: 插入說明
    # ═══════════════════════════════════════════════════════════════════════
    session.load_formula("a + b + c", formula_id="f1")
    session.load_formula("c * d + a", formula_id="f2")  # 確保有 a 變數
    session.substitute("a", "c")

    assert session.step_count == 3, f"Expected 3 steps, got {session.step_count}"

    # 在步驟 1 之後插入說明
    result = session.insert_note_after_step(
        after_step=1,
        note="這是在步驟 1 和 2 之間插入的說明",
        note_type="observation",
        related_variables=["a", "b"],
    )
    assert result["success"], f"Insert failed: {result}"
    assert result["inserted_at"] == 2
    assert session.step_count == 4
    print(f"✅ Insert: Note inserted at position {result['inserted_at']}")

    # 驗證步驟編號正確
    for i, step in enumerate(session.steps):
        assert step.step_number == i + 1, f"Step {i + 1} has wrong number: {step.step_number}"
    print("✅ Insert: Steps correctly renumbered")

    print("\n🎉 All CRUD tests passed!")


if __name__ == "__main__":
    test_step_crud()
