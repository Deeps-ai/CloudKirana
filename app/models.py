from pydantic import BaseModel
from typing import Optional, List, Any

class InspectionParameters(BaseModel):
    pdp_area_cm2: Optional[float] = None
    pixels_per_mm: Optional[float] = None
    print_type: Optional[str] = "normal"

class TextRegionResult(BaseModel):
    text: str
    confidence: float
    bbox: Any
    text_height_px: int
    text_height_mm: Optional[float] = None
    required_mm: Optional[float] = None
    status: str
    reason: str

class InspectionResultData(BaseModel):
    inspection_target_detected: bool
    ocr_status: str
    font_compliance: str
    overall_status: str
    parameters: dict
    results: List[TextRegionResult]

class InspectionResponse(BaseModel):
    success: bool
    inspection: Optional[InspectionResultData] = None
    error: Optional[str] = None
