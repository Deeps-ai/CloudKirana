from typing import Optional

def get_required_font_size(pdp_area_cm2: Optional[float], print_type: str = "normal") -> Optional[float]:
    if pdp_area_cm2 is None:
        return None
    
    if pdp_area_cm2 <= 50:
        return 1.0 if print_type == "normal" else 2.0
    elif pdp_area_cm2 <= 100:
        return 1.5 if print_type == "normal" else 3.0
    elif pdp_area_cm2 <= 500:
        return 2.5 if print_type == "normal" else 4.0
    elif pdp_area_cm2 <= 2500:
        return 4.0 if print_type == "normal" else 6.0
    else:
        return 6.0
