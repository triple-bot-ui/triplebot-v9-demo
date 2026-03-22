# ============================================
# TRIPLE BOT V9.6
# BOQ ENGINE (แก้ไขเพื่อให้ depth เป็น parameter + แสดงชัดเจน)
# ============================================

def generate_boq(
    foundation_width,
    foundation_length,
    total_load,
    soil_capacity,
    foundation_depth=0.4  # รับ depth เป็น parameter, default 0.4 m
):
    """
    Generate Bill of Quantities for foundation.
    - foundation_depth เป็น parameter เพื่อให้ยืดหยุ่น (ไม่ hardcode อีกต่อไป)
    - ถ้าเรียกโดยไม่ส่ง depth จะใช้ default 0.4 m และสามารถแจ้งใน UI ได้
    """

    # Foundation geometry
    foundation_area = foundation_width * foundation_length

    # Concrete volume
    concrete_volume_m3 = foundation_area * foundation_depth

    # Excavation volume (working space factor 1.8)
    excavation_volume_m3 = concrete_volume_m3 * 1.8

    # Reinforcement estimate (~100 kg/m³ concrete)
    reinforcement_estimate = concrete_volume_m3 * 100

    # Return BOQ dictionary
    boq = {
        "foundation_area": round(foundation_area, 3),
        "foundation_depth": round(foundation_depth, 2),  # แสดง depth ที่ใช้จริง
        "concrete_volume_m3": round(concrete_volume_m3, 3),
        "excavation_volume_m3": round(excavation_volume_m3, 3),
        "reinforcement_estimate": round(reinforcement_estimate, 2)
    }

    return boq