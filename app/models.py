from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime
from uuid import UUID

class LMPCStatus(str, Enum):
    COMPLIANT = "COMPLIANT"
    POTENTIAL_ISSUE = "POTENTIAL_ISSUE"
    REQUIRES_VERIFICATION = "REQUIRES_VERIFICATION"
    NON_COMPLIANT = "NON_COMPLIANT"

class DeclarationFieldResult(BaseModel):
    field_name: str
    detected_value: Optional[str] = None
    is_present: bool
    font_height_mm: Optional[float] = None
    min_required_mm: float
    status: LMPCStatus
    reasons: List[str] = Field(default_factory=list)

class InspectionParameters(BaseModel):
    pdp_area_cm2: Optional[float] = None
    pixels_per_mm: Optional[float] = None
    print_type: Optional[str] = "normal"
    category: Optional[str] = "packaged_food"

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
    barcodes: List[Dict[str, Any]] = Field(default_factory=list)
    label_crop_coordinates: Optional[List[int]] = None
    overall_compliance_score: float = 0.0
    classification: LMPCStatus = LMPCStatus.REQUIRES_VERIFICATION
    declarations: Dict[str, DeclarationFieldResult] = Field(default_factory=dict)
    category: str = "packaged_food"

# Alias for InspectionResult if referenced
InspectionResult = InspectionResultData

class InspectionResponse(BaseModel):
    success: bool
    inspection: Optional[InspectionResultData] = None
    error: Optional[str] = None

# New Models for CloudKirana Prototype
class AuthRequest(BaseModel):
    phone: str

class AuthVerify(BaseModel):
    phone: str
    otp: str

class ONDCSyncRequest(BaseModel):
    enabled: bool

class InventoryAddRequest(BaseModel):
    scan_id: UUID

class InvoiceUpdateRequest(BaseModel):
    invoice_id: UUID

class OrderRequest(BaseModel):
    items: List[Dict[str, Any]]
    totalAmount: float
    paymentMethod: str = "COD"

class NoticeRequest(BaseModel):
    pass

class RecallRequest(BaseModel):
    pass
