from app.ocr import inspect_text
from app.compliance import get_required_font_size
from app.models import InspectionParameters, TextRegionResult, InspectionResultData, InspectionResponse
from typing import Union
import numpy as np

def run_inspection(image_input: Union[str, np.ndarray], params: InspectionParameters) -> InspectionResponse:
    ocr_result = inspect_text(image_input)
    
    if ocr_result.get("ocr_status") != "SUCCESS":
        return InspectionResponse(
            success=False,
            error=ocr_result.get("error", "Unknown OCR Error")
        )

    results_list = []
    
    for region in ocr_result["text_regions"]:
        height_px = region["text_height_px"]
        required_mm = get_required_font_size(params.pdp_area_cm2, params.print_type)
        
        if params.pixels_per_mm is not None:
            text_height_mm = height_px / params.pixels_per_mm
        else:
            text_height_mm = None
            
        if required_mm is None and text_height_mm is None:
            status = "UNVERIFIED"
            reason = "Physical image scale and PDP area unavailable"
        elif text_height_mm is None:
            status = "UNVERIFIED"
            reason = "Physical image scale unavailable"
        elif required_mm is None:
            status = "UNVERIFIED"
            reason = "PDP area unavailable"
        else:
            if text_height_mm >= required_mm:
                status = "PASS"
                reason = "Measured text height meets or exceeds required minimum"
            else:
                status = "FAIL"
                reason = "Measured text height is below required minimum"
                
        text_result = TextRegionResult(
            text=region["text"],
            confidence=region["confidence"],
            bbox=region["bbox"],
            text_height_px=height_px,
            text_height_mm=round(text_height_mm, 2) if text_height_mm is not None else None,
            required_mm=required_mm,
            status=status,
            reason=reason
        )
        results_list.append(text_result)

    if not results_list:
        overall_font_compliance = "UNVERIFIED"
    elif any(r.status == "FAIL" for r in results_list):
        overall_font_compliance = "FAIL"
    elif any(r.status == "UNVERIFIED" for r in results_list):
        overall_font_compliance = "UNVERIFIED"
    else:
        overall_font_compliance = "PASS"

    overall_status = overall_font_compliance

    inspection_data = InspectionResultData(
        inspection_target_detected=True,
        ocr_status="SUCCESS",
        font_compliance=overall_font_compliance,
        overall_status=overall_status,
        parameters=params.model_dump(),
        results=results_list
    )

    return InspectionResponse(
        success=True,
        inspection=inspection_data
    )
