import re
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from app.models import LMPCStatus, DeclarationFieldResult

# 6 Mandatory Declarations under Legal Metrology (Packaged Commodities) Rules:
# 1. Name and address of manufacturer / packer / importer
# 2. Country of origin (for imported products)
# 3. Common or generic name of commodity
# 4. Net quantity in standard units (g, kg, ml, l, or number)
# 5. Month and year of manufacture / packing / import
# 6. Maximum Retail Price (MRP) inclusive of all taxes

DECLARATION_MRP = "mrp"
DECLARATION_NET_QUANTITY = "net_quantity"
DECLARATION_DATES = "dates"
DECLARATION_MANUFACTURER = "manufacturer_packer"
DECLARATION_COUNTRY_OF_ORIGIN = "country_of_origin"
DECLARATION_GENERIC_NAME = "generic_name"

# Regex patterns as requested
MRP_PATTERN = re.compile(r'(?:MRP|M\.R\.P\.?|Rs\.?|₹)\s*[:.]?\s*(\d+(?:\.\d{1,2})?)', re.IGNORECASE)
NET_QTY_PATTERN = re.compile(r'(\d+(?:\.\d+)?)\s*(kg|g|gm|gms|l|ml|ltr|units|n|pcs)\b', re.IGNORECASE)
DATES_PATTERN = re.compile(r'(?:MFD|MFG|PKD|PACKED|EXP|BEST BEFORE)\s*[:.]?\s*([0-9]{1,2}[/-][0-9]{2,4}|[A-Za-z]{3}[/-][0-9]{2,4})', re.IGNORECASE)
COUNTRY_ORIGIN_PATTERN = re.compile(r'(?:Country of Origin|Made in|Product of)\s*[:.]?\s*([A-Za-z]+)', re.IGNORECASE)

MANUFACTURER_PATTERN = re.compile(
    r'(?:Mfd\.?\s*by|Mfg\.?\s*by|Manufactured\s+by|Marketed\s+by|Packed\s+by|Pkd\s+by|Pkg\s+by|Imported\s+by|Producer|Brand\s+Owner)\s*[:.]?\s*([A-Za-z0-9\s.,&-]+?)(?=(?:\r?\n|$|[.;]))',
    re.IGNORECASE
)

GENERIC_NAME_PATTERN = re.compile(
    r'(?:Product|Commodity|Item|Name of Commodity|Generic Name)\s*[:.]?\s*([A-Za-z0-9\s.,&-]+?)(?=(?:\r?\n|$|[.;]))',
    re.IGNORECASE
)

def get_required_font_size(pdp_area_cm2: Optional[float], print_type: str = "normal") -> Optional[float]:
    """Legacy/general PDP area based font size calculator."""
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

def get_min_font_size_for_net_quantity(
    net_weight_in_grams_or_ml: Optional[float],
    pdp_area_cm2: Optional[float] = None,
    category: str = "packaged_food"
) -> float:
    """
    Category-specific / LMPC minimum font size rules based on net weight/area:
    net wt <= 50g -> 1.0mm,
    50-200g -> 1.5mm,
    200-1kg (200-1000g) -> 2.0mm,
    >1kg (>1000g) -> 4.0mm.
    Falls back to PDP area calculation if weight is unavailable, or 1.0mm default.
    """
    if net_weight_in_grams_or_ml is not None:
        if net_weight_in_grams_or_ml <= 50:
            return 1.0
        elif net_weight_in_grams_or_ml <= 200:
            return 1.5
        elif net_weight_in_grams_or_ml <= 1000:
            return 2.0
        else:
            return 4.0
    
    # Fallback to PDP area if weight not available
    if pdp_area_cm2 is not None:
        pdp_req = get_required_font_size(pdp_area_cm2)
        if pdp_req is not None:
            return pdp_req
            
    return 1.0

def parse_net_quantity_to_standard_unit(qty_str: str, unit: str) -> Optional[float]:
    try:
        val = float(qty_str)
        u = unit.lower()
        if u in ("kg", "l", "ltr"):
            return val * 1000.0
        elif u in ("g", "gm", "gms", "ml"):
            return val
        else:
            return val
    except Exception:
        return None

def validate_date_string(date_str: str) -> Tuple[bool, str]:
    """
    Validates month and year date string (e.g., 05/24, 05/2024, May/2024, 05-24).
    Returns (is_valid, reason).
    """
    cleaned = date_str.strip()
    # Replace delimiter with slash
    normalized = cleaned.replace("-", "/")
    parts = normalized.split("/")
    if len(parts) != 2:
        return False, f"Unrecognized date format: {date_str}"
    
    m_part, y_part = parts[0], parts[1]
    
    # Check month
    month = None
    if m_part.isdigit():
        month = int(m_part)
        if not (1 <= month <= 12):
            return False, f"Invalid month: {m_part}"
    else:
        try:
            # Try parsing 3-letter month like Jan, Feb, etc.
            dt = datetime.strptime(m_part[:3], "%b")
            month = dt.month
        except Exception:
            return False, f"Invalid month name: {m_part}"
            
    # Check year
    if not y_part.isdigit():
        return False, f"Invalid year: {y_part}"
        
    year = int(y_part)
    if len(y_part) == 2:
        year += 2000
    elif len(y_part) != 4:
        return False, f"Invalid year length: {y_part}"
        
    if year < 2000 or year > 2040:
        return False, f"Year out of realistic bounds: {year}"
        
    return True, "Valid date format"

def extract_entities_from_text(full_text: str) -> Dict[str, Dict[str, Any]]:
    """
    Extracts LMPC declarations from raw OCR text using regex and heuristics.
    """
    detected: Dict[str, Dict[str, Any]] = {}

    # 1. MRP
    mrp_match = MRP_PATTERN.search(full_text)
    if mrp_match:
        detected[DECLARATION_MRP] = {
            "value": f"₹{mrp_match.group(1)}",
            "raw_match": mrp_match.group(0),
            "numeric_value": float(mrp_match.group(1))
        }

    # 2. Net Quantity
    qty_match = NET_QTY_PATTERN.search(full_text)
    if qty_match:
        qty_num = qty_match.group(1)
        unit = qty_match.group(2)
        std_qty = parse_net_quantity_to_standard_unit(qty_num, unit)
        detected[DECLARATION_NET_QUANTITY] = {
            "value": f"{qty_num} {unit}",
            "raw_match": qty_match.group(0),
            "normalized_grams_or_ml": std_qty
        }

    # 3. Dates (MFD/MFG/PKD/EXP)
    date_match = DATES_PATTERN.search(full_text)
    if date_match:
        detected[DECLARATION_DATES] = {
            "value": date_match.group(0),
            "date_part": date_match.group(1),
            "raw_match": date_match.group(0)
        }

    # 4. Country of Origin
    coo_match = COUNTRY_ORIGIN_PATTERN.search(full_text)
    if coo_match:
        detected[DECLARATION_COUNTRY_OF_ORIGIN] = {
            "value": coo_match.group(1).capitalize(),
            "raw_match": coo_match.group(0)
        }
    else:
        # Heuristic check for common country words if explicit keyword missing
        country_words = ["India", "Bharat", "USA", "China", "Germany", "Japan", "Thailand", "UK", "Italy", "France"]
        for cw in country_words:
            if re.search(r'\b' + re.escape(cw) + r'\b', full_text, re.IGNORECASE):
                detected[DECLARATION_COUNTRY_OF_ORIGIN] = {
                    "value": cw,
                    "raw_match": cw
                }
                break

    # 5. Manufacturer / Packer
    mfg_match = MANUFACTURER_PATTERN.search(full_text)
    if mfg_match:
        detected[DECLARATION_MANUFACTURER] = {
            "value": mfg_match.group(1).strip()[:100],
            "raw_match": mfg_match.group(0)
        }
    else:
        # Heuristic search for Pvt Ltd, Ltd, Foods, Industries
        co_match = re.search(r'([A-Za-z0-9\s.,&-]+(?:Pvt\.?\s*Ltd|Private\s+Limited|Industries|Enterprises|Foods|Beverages))', full_text, re.IGNORECASE)
        if co_match:
            detected[DECLARATION_MANUFACTURER] = {
                "value": co_match.group(1).strip()[:100],
                "raw_match": co_match.group(0)
            }

    # 6. Common / Generic Name
    gen_match = GENERIC_NAME_PATTERN.search(full_text)
    if gen_match:
        detected[DECLARATION_GENERIC_NAME] = {
            "value": gen_match.group(1).strip()[:60],
            "raw_match": gen_match.group(0)
        }
    else:
        # Fallback heuristic: check if common item names are present in first 3 lines
        lines = [line.strip() for line in full_text.splitlines() if line.strip()]
        if lines:
            detected[DECLARATION_GENERIC_NAME] = {
                "value": lines[0][:60],
                "raw_match": lines[0][:60]
            }

    return detected

def find_font_height_for_entity(raw_match: str, text_regions: List[Dict[str, Any]], pixels_per_mm: Optional[float]) -> Optional[float]:
    """Finds the font height in mm for the OCR text region corresponding to the matched entity."""
    if not pixels_per_mm or pixels_per_mm <= 0 or not raw_match:
        return None

    raw_clean = re.sub(r'\s+', ' ', raw_match.strip().lower())
    for region in text_regions:
        reg_text = re.sub(r'\s+', ' ', str(region.get("text", "")).strip().lower())
        if raw_clean in reg_text or reg_text in raw_clean:
            height_px = region.get("text_height_px", 0)
            if height_px > 0:
                return round(float(height_px) / pixels_per_mm, 2)

    return None

def evaluate_lmpc_compliance(
    text_regions: List[Dict[str, Any]],
    pdp_area_cm2: Optional[float] = None,
    pixels_per_mm: Optional[float] = None,
    category: str = "packaged_food"
) -> Dict[str, Any]:
    """
    Evaluates LMPC mandatory declarations, font sizes, and calculates compliance score.
    Returns:
    - declarations: Dict[str, DeclarationFieldResult]
    - overall_compliance_score: float (0.0 to 100.0)
    - classification: LMPCStatus
    - category: str
    """
    full_text = " \n ".join([str(r.get("text", "")) for r in text_regions])
    extracted = extract_entities_from_text(full_text)

    # Determine minimum required font size based on category and net quantity if detected
    net_weight = None
    if DECLARATION_NET_QUANTITY in extracted:
        net_weight = extracted[DECLARATION_NET_QUANTITY].get("normalized_grams_or_ml")
    min_required_font_mm = get_min_font_size_for_net_quantity(net_weight, pdp_area_cm2, category)

    mandatory_fields = [
        (DECLARATION_MRP, "Maximum Retail Price (MRP)"),
        (DECLARATION_NET_QUANTITY, "Net Quantity"),
        (DECLARATION_DATES, "Date of Manufacture/Expiry"),
        (DECLARATION_MANUFACTURER, "Manufacturer/Packer Details"),
        (DECLARATION_COUNTRY_OF_ORIGIN, "Country of Origin"),
        (DECLARATION_GENERIC_NAME, "Generic / Common Name")
    ]

    declarations: Dict[str, DeclarationFieldResult] = {}
    
    presence_points = 0.0
    font_points = 0.0
    date_points = 0.0
    
    total_fields = len(mandatory_fields) # 6 fields
    font_applicable_count = 0

    for key, human_name in mandatory_fields:
        is_present = key in extracted
        detected_val = extracted[key]["value"] if is_present else None
        raw_match = extracted[key].get("raw_match", "") if is_present else ""
        font_height_mm = find_font_height_for_entity(raw_match, text_regions, pixels_per_mm) if is_present else None

        reasons: List[str] = []
        field_status = LMPCStatus.NON_COMPLIANT

        if not is_present:
            reasons.append(f"Mandatory declaration '{human_name}' is missing.")
            field_status = LMPCStatus.NON_COMPLIANT
        else:
            presence_points += 1.0
            field_status = LMPCStatus.COMPLIANT

            # Check font size compliance if image scale is known
            if font_height_mm is not None:
                font_applicable_count += 1
                if font_height_mm >= min_required_font_mm:
                    font_points += 1.0
                    reasons.append(f"Font height ({font_height_mm:.2f}mm) satisfies minimum {min_required_font_mm:.2f}mm.")
                else:
                    field_status = LMPCStatus.POTENTIAL_ISSUE
                    reasons.append(f"Font height ({font_height_mm:.2f}mm) below required {min_required_font_mm:.2f}mm.")
            else:
                if pixels_per_mm is None:
                    reasons.append("Physical scale (pixels_per_mm) unavailable for exact font verification.")
                    if field_status == LMPCStatus.COMPLIANT:
                        field_status = LMPCStatus.REQUIRES_VERIFICATION

            # Date specific validity check
            if key == DECLARATION_DATES:
                date_part = extracted[key].get("date_part", "")
                is_valid_date, date_msg = validate_date_string(date_part)
                if is_valid_date:
                    date_points = 1.0
                    reasons.append(f"Date declaration is valid ({date_part}).")
                else:
                    date_points = 0.0
                    field_status = LMPCStatus.POTENTIAL_ISSUE
                    reasons.append(f"Date declaration format issue: {date_msg}")

        declarations[key] = DeclarationFieldResult(
            field_name=human_name,
            detected_value=detected_val,
            is_present=is_present,
            font_height_mm=font_height_mm,
            min_required_mm=min_required_font_mm,
            status=field_status,
            reasons=reasons
        )

    # Compliance score calculation (weighted: presence 50%, font size 30%, date validity 20%)
    presence_score = (presence_points / total_fields) * 50.0

    if font_applicable_count > 0:
        font_score = (font_points / font_applicable_count) * 30.0
    else:
        # If no font scale available, give proportional credit if entities are present (subject to verification)
        font_score = (presence_points / total_fields) * 20.0

    date_score = date_points * 20.0

    overall_score = round(presence_score + font_score + date_score, 1)
    overall_score = max(0.0, min(100.0, overall_score))

    # Overall Classification
    # COMPLIANT: all mandatory present, font >= min, dates valid
    # POTENTIAL_ISSUE: missing secondary fields or font height slightly lower
    # REQUIRES_VERIFICATION: scale not provided or ambiguous values
    # NON_COMPLIANT: critical fields like MRP/Net Qty missing or score < 50
    has_mrp = declarations[DECLARATION_MRP].is_present
    has_net_qty = declarations[DECLARATION_NET_QUANTITY].is_present

    if not has_mrp or not has_net_qty or overall_score < 50.0:
        classification = LMPCStatus.NON_COMPLIANT
    elif any(d.status == LMPCStatus.POTENTIAL_ISSUE for d in declarations.values()):
        classification = LMPCStatus.POTENTIAL_ISSUE
    elif pixels_per_mm is None or any(d.status == LMPCStatus.REQUIRES_VERIFICATION for d in declarations.values()):
        classification = LMPCStatus.REQUIRES_VERIFICATION
    elif overall_score >= 85.0 and all(d.status == LMPCStatus.COMPLIANT for d in declarations.values()):
        classification = LMPCStatus.COMPLIANT
    else:
        classification = LMPCStatus.POTENTIAL_ISSUE

    return {
        "declarations": declarations,
        "overall_compliance_score": overall_score,
        "classification": classification,
        "category": category
    }
