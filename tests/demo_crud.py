"""展示步驟 CRUD 功能"""

from pathlib import Path

from nsforge.domain.derivation_session import get_session_manager


def demo_crud():
    # 載入現有會話
    mgr = get_session_manager(Path("derivation_sessions"))
    session = mgr.get("d6ae10b2")

    if not session:
        print("Session not found")
        return

    print(f"Session: {session.name}")
    print(f"Steps: {session.step_count}")

    # Read 單一步驟
    print("\n--- 📖 Read: Get Step 3 ---")
    result = session.get_step(3)
    print(f"Step 3: {result['step']['description']}")
    print(f"Expression: {result['step']['output_latex']}")

    # Update 步驟
    print("\n--- ✏️ Update: Step 3 ---")
    result = session.update_step(
        step_number=3,
        notes="Arrhenius 方程只在 32-42°C 有效",
        limitations=["溫度超過 42°C 時酵素會變性"],
    )
    print(f"Updated fields: {result['updated_fields']}")

    # 驗證更新
    result = session.get_step(3)
    print(f"New notes: {result['step']['notes']}")
    print(f"New limitations: {result['step']['limitations']}")

    # Rollback 測試
    print("\n--- ⏪ Rollback: To Step 2 ---")
    print(f"Before: {session.step_count} steps")
    result = session.rollback_to_step(2)
    print(f"After rollback: {result['new_step_count']} steps")
    print(f"Deleted steps: {result['deleted_steps']}")
    print(f"Current expression: {result['current_latex']}")


if __name__ == "__main__":
    demo_crud()
