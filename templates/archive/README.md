# Archive - Templates

## 歸檔原因

此目錄存放已過時或不再使用的模板檔案。

### rc_lowpass.yaml

**歸檔日期**: 2026-01-02

**原因**:
- NSForge 定位為「公式推導引擎」，專注於數學推導和學術溯源
- 電路分析模板屬於應用層面，不符合 NSForge 核心定位
- 這類領域特定模板應由其他專門 MCP server 處理（如 circuit-analysis-mcp）

**NSForge 專注於**:
- ✅ 公式推導（derivation）
- ✅ 符號運算（symbolic computation）
- ✅ 學術溯源（provenance tracking）
- ❌ 領域特定應用模板（circuit analysis, pharmacokinetics, etc.）

如需電路分析功能，建議：
1. 使用 Python lcapy 庫直接分析
2. 使用 sympy-mcp 進行符號計算
3. 用 NSForge 推導通用公式後，寫成 Python 程式

**保留原因**:
- 作為模板系統設計的參考範例
- 展示如何結構化領域知識
- 可能對未來的「應用層 MCP」有參考價值
