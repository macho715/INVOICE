FIXED_FX = {"USD_AED": 3.6725}
LAYER1_TOL = 0.03
AUTOFAIL = 0.15
CG_BANDS = [(0.02, "PASS"), (0.05, "WARN"), (0.10, "HIGH"), (9.99, "CRITICAL")]
def cg_band(delta_abs: float) -> str:
    for thr, name in CG_BANDS:
        if delta_abs <= thr: return name
    return "CRITICAL"
