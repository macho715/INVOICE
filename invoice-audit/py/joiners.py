import re
CANON_DEST = {"Shuweihat":"SHUWEIHAT Site","Mirfa":"MIRFA SITE","Mussafah Yard":"Storage Yard"}
def canon_dest(s:str)->str:
    if not s: return s
    s2 = re.sub(r"\s+"," ",s).strip()
    return CANON_DEST.get(s2, s2)
def unit_key(u:str)->str:
    u=(u or "").strip().lower()
    return {"per rt":"per RT","per truck":"per truck"}.get(u,u)
def port_hint(port:str,dest:str,unit:str)->str:
    d=(dest or "").upper()
    return "Khalifa Port" if unit_key(unit)=="per truck" and any(x in d for x in ["MIRFA","SHUWEIHAT","STORAGE YARD"]) else (port or "")
