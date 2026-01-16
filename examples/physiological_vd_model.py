"""
生理學分布容積公式 - 體組成調整模型
Physiological Vd Model with Body Composition Adjustment

基於 PBPK 方法，考慮體組成對藥物分布的影響。

推導來源: NSForge Session 881df03b (2026-01-16)

適用範圍：
- logP > 2 的脂溶性中性藥物
- 被動分配為主的藥物
- 例: Propofol, Thiopental, Ketamine, Etomidate

限制：
- 不適用於高蛋白結合藥物 (Warfarin)
- 不適用於主動轉運藥物 (Morphine, Digoxin)

重要：此模型定位為「體組成調整公式」，不是「通用 Vd 預測公式」
"""

import math
from dataclasses import dataclass
from typing import Tuple, Optional


@dataclass
class PatientProfile:
    """患者基本資料"""
    weight: float      # 體重 (kg)
    age: int           # 年齡 (years)
    sex: int           # 性別 (1=男, 0=女)
    bmi: float         # BMI (kg/m²)


@dataclass
class DrugProperties:
    """藥物性質"""
    name: str
    log_p: float       # 脂水分配係數
    vd_reference: Optional[float] = None  # 文獻參考 Vd (L/kg)


class PhysiologicalVdModel:
    """
    生理學分布容積模型
    
    公式架構 (PBPK):
        Vd,ss = V_plasma + Kp_lean × V_lean + Kp_fat × V_fat
    
    其中：
        V_plasma = 0.045 × BW
        f_fat = (1.2×BMI + 0.23×age - 10.8×sex - 5.4) / 100  [Deurenberg]
        V_fat = f_fat × 0.916 × BW
        V_lean = (1 - f_fat) × 0.73 × BW
        Kp = P_max × 10^logP / (10^logP + 100)  [Michaelis-Menten]
    """
    
    # 模型參數（由多藥物校準）
    P_FAT_MAX = 20.0    # 脂肪組織最大分配係數
    P_LEAN_MAX = 1.0    # 瘦組織最大分配係數
    
    def __init__(self, patient: PatientProfile):
        self.patient = patient
        self._calculate_compartments()
    
    def _calculate_compartments(self):
        """計算各組織區室體積"""
        p = self.patient
        
        # 體脂率 (Deurenberg formula, 1991)
        self.f_fat = (1.2 * p.bmi + 0.23 * p.age - 10.8 * p.sex - 5.4) / 100
        self.f_fat = max(0.05, min(0.50, self.f_fat))  # 限制在合理範圍
        
        # 組織體積
        self.v_plasma = 0.045 * p.weight
        self.v_fat = self.f_fat * 0.916 * p.weight
        self.v_lean = (1 - self.f_fat) * 0.73 * p.weight
    
    def calculate_kp(self, log_p: float) -> Tuple[float, float]:
        """
        計算組織分配係數 (Michaelis-Menten 飽和模型)
        
        Args:
            log_p: 藥物的脂水分配係數
            
        Returns:
            (Kp_fat, Kp_lean) 元組
        """
        p_ratio = 10 ** log_p
        kp_fat = self.P_FAT_MAX * p_ratio / (p_ratio + 100)
        kp_lean = self.P_LEAN_MAX * p_ratio / (p_ratio + 100)
        return kp_fat, kp_lean
    
    def calculate_vd(self, drug: DrugProperties) -> dict:
        """
        計算分布容積（直接預測）
        
        ⚠️ 注意：直接預測可能有 30-80% 誤差
        建議使用 adjust_for_body_composition() 進行體組成調整
        
        Args:
            drug: 藥物性質
            
        Returns:
            包含所有計算結果的字典
        """
        kp_fat, kp_lean = self.calculate_kp(drug.log_p)
        
        # PBPK 公式
        vd_total = (self.v_plasma + 
                    kp_lean * self.v_lean + 
                    kp_fat * self.v_fat)
        
        vd_per_kg = vd_total / self.patient.weight
        
        return {
            'drug': drug.name,
            'patient_weight': self.patient.weight,
            'f_fat': self.f_fat,
            'v_plasma': self.v_plasma,
            'v_fat': self.v_fat,
            'v_lean': self.v_lean,
            'kp_fat': kp_fat,
            'kp_lean': kp_lean,
            'vd_total': vd_total,
            'vd_per_kg': vd_per_kg,
        }
    
    def adjust_for_body_composition(
        self, 
        drug: DrugProperties,
        reference_f_fat: float = 0.22
    ) -> dict:
        """
        體組成調整（推薦用法）✅
        
        使用文獻 Vd 作為基準，調整不同體組成的患者。
        這是此模型的正確使用方式！
        
        Args:
            drug: 藥物性質（需包含 vd_reference）
            reference_f_fat: 參考體脂率（默認 0.22 = 標準男性）
            
        Returns:
            調整後的 Vd 資訊
        """
        if drug.vd_reference is None:
            raise ValueError("需要提供文獻參考 Vd (vd_reference)")
        
        kp_fat, kp_lean = self.calculate_kp(drug.log_p)
        
        # 計算相對於參考的脂肪貢獻變化
        delta_f_fat = self.f_fat - reference_f_fat
        
        # 脂溶性越高，體脂變化影響越大
        alpha = kp_fat / (kp_fat + kp_lean + 1)  # 脂肪權重因子
        
        # 調整公式
        adjustment_factor = 1 + alpha * delta_f_fat / reference_f_fat
        vd_adjusted = drug.vd_reference * adjustment_factor
        
        return {
            'drug': drug.name,
            'vd_reference': drug.vd_reference,
            'f_fat': self.f_fat,
            'reference_f_fat': reference_f_fat,
            'delta_f_fat': delta_f_fat,
            'alpha': alpha,
            'adjustment_factor': adjustment_factor,
            'vd_adjusted': vd_adjusted,
            'vd_adjusted_total': vd_adjusted * self.patient.weight,
        }


# ============================================================
# 預定義藥物庫
# ============================================================

DRUGS = {
    'propofol': DrugProperties("Propofol", 3.8, 6.0),
    'thiopental': DrugProperties("Thiopental", 2.9, 2.25),
    'ketamine': DrugProperties("Ketamine", 2.2, 3.0),
    'etomidate': DrugProperties("Etomidate", 2.5, 3.5),
    'midazolam': DrugProperties("Midazolam", 3.9, 1.25),
    'fentanyl': DrugProperties("Fentanyl", 4.1, 4.5),
}


# ============================================================
# 便捷函數
# ============================================================

def quick_vd_calculation(
    weight: float,
    age: int,
    sex: int,
    bmi: float,
    drug_name: str
) -> dict:
    """
    快速計算 Vd（直接預測）
    
    Args:
        weight: 體重 (kg)
        age: 年齡
        sex: 性別 (1=男, 0=女)
        bmi: BMI
        drug_name: 藥物名稱（小寫）
        
    Returns:
        計算結果字典
    """
    if drug_name.lower() not in DRUGS:
        raise ValueError(f"未知藥物: {drug_name}. 可用: {list(DRUGS.keys())}")
    
    patient = PatientProfile(weight, age, sex, bmi)
    model = PhysiologicalVdModel(patient)
    drug = DRUGS[drug_name.lower()]
    
    return model.calculate_vd(drug)


def quick_vd_adjustment(
    weight: float,
    age: int,
    sex: int,
    bmi: float,
    drug_name: str
) -> dict:
    """
    快速體組成調整（推薦用法）
    
    Args:
        weight: 體重 (kg)
        age: 年齡
        sex: 性別 (1=男, 0=女)
        bmi: BMI
        drug_name: 藥物名稱（小寫）
        
    Returns:
        調整結果字典
    """
    if drug_name.lower() not in DRUGS:
        raise ValueError(f"未知藥物: {drug_name}. 可用: {list(DRUGS.keys())}")
    
    patient = PatientProfile(weight, age, sex, bmi)
    model = PhysiologicalVdModel(patient)
    drug = DRUGS[drug_name.lower()]
    
    return model.adjust_for_body_composition(drug)


# ============================================================
# 示範
# ============================================================

def demo():
    """完整示範"""
    
    print("=" * 70)
    print("生理學分布容積模型 - 完整示範")
    print("=" * 70)
    
    # --------------------------------------------------------
    # 範例 1: 直接計算
    # --------------------------------------------------------
    print("\n" + "=" * 70)
    print("【範例 1】直接計算 Propofol Vd")
    print("=" * 70)
    
    result = quick_vd_calculation(
        weight=85,
        age=50,
        sex=1,
        bmi=27,
        drug_name='propofol'
    )
    
    print(f"""
患者資料:
  體重: {result['patient_weight']} kg
  體脂率: {result['f_fat']*100:.1f}%

組織體積:
  V_plasma = {result['v_plasma']:.1f} L
  V_fat    = {result['v_fat']:.1f} L
  V_lean   = {result['v_lean']:.1f} L

分配係數:
  Kp_fat  = {result['kp_fat']:.2f}
  Kp_lean = {result['kp_lean']:.2f}

計算結果:
  Vd = {result['vd_total']:.1f} L ({result['vd_per_kg']:.2f} L/kg)
  文獻範圍: 140-850 L (2-10 L/kg)
""")

    # --------------------------------------------------------
    # 範例 2: 體組成調整（推薦）
    # --------------------------------------------------------
    print("=" * 70)
    print("【範例 2】體組成調整 - 標準 vs 肥胖患者")
    print("=" * 70)
    
    patients = [
        ("標準", 70, 40, 1, 24),
        ("肥胖", 100, 40, 1, 35),
        ("瘦弱", 55, 40, 1, 18),
    ]
    
    print("\nPropofol 劑量調整建議:\n")
    print(f"{'患者類型':<8} {'體重':>6} {'BMI':>5} {'體脂率':>7} {'Vd調整':>10} {'Vd總量':>10}")
    print("-" * 60)
    
    for label, weight, age, sex, bmi in patients:
        result = quick_vd_adjustment(weight, age, sex, bmi, 'propofol')
        print(f"{label:<8} {weight:>5}kg {bmi:>5} {result['f_fat']*100:>6.1f}% "
              f"{result['vd_adjusted']:>9.2f} {result['vd_adjusted_total']:>9.0f} L")
    
    # --------------------------------------------------------
    # 範例 3: 多藥物比較
    # --------------------------------------------------------
    print("\n" + "=" * 70)
    print("【範例 3】多藥物比較 (標準 70kg 男性)")
    print("=" * 70)
    
    patient = PatientProfile(70, 40, 1, 24)
    model = PhysiologicalVdModel(patient)
    
    print(f"\n體脂率: {model.f_fat*100:.1f}%\n")
    print(f"{'藥物':<12} {'logP':>5} {'Kp_fat':>7} {'Kp_lean':>7} {'計算Vd':>8} {'文獻Vd':>8}")
    print("-" * 55)
    
    for drug in DRUGS.values():
        result = model.calculate_vd(drug)
        ref = drug.vd_reference if drug.vd_reference else "N/A"
        print(f"{drug.name:<12} {drug.log_p:>5.1f} {result['kp_fat']:>7.2f} "
              f"{result['kp_lean']:>7.2f} {result['vd_per_kg']:>7.2f}  {ref:>7}")
    
    # --------------------------------------------------------
    # 適用範圍提醒
    # --------------------------------------------------------
    print("\n" + "=" * 70)
    print("【重要提醒】模型適用範圍")
    print("=" * 70)
    print("""
✅ 適用藥物:
   - 高脂溶性 (logP > 2)
   - 中性分子
   - 被動分配為主
   - 例: Propofol, Thiopental, Ketamine, Etomidate

❌ 不適用藥物:
   - 高蛋白結合: Warfarin (99%), Phenytoin
   - 主動轉運: Morphine, Digoxin
   - 親水性: Aminoglycosides, Theophylline

⚠️  正確用法:
   此模型是「體組成調整公式」，不是「通用 Vd 預測公式」
   
   推薦: 使用 adjust_for_body_composition() 或 quick_vd_adjustment()
   基於文獻 Vd 進行體組成調整，而非直接預測絕對值
""")


if __name__ == "__main__":
    demo()
