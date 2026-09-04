# CloudKirana

CloudKirana Inspection Backend prototype for label compliance checking.

## Purpose
This project is an inspection backend that detects text on products using EasyOCR and evaluates whether the font size complies with configurable mm requirements.

**IMPORTANT WARNING**: This system only checks label/font compliance. It does NOT determine product authenticity or counterfeit status. A font compliance failure does not mean a product is fake. `pixels_per_mm` is a calibration parameter that must represent a real physical calibration mechanism in production.

## Folder Structure
```
CloudKirana/
├── .venv/                 # Virtual environment
├── Assets/                # Test images
├── app/                   # FastAPI backend module
│   ├── __init__.py
│   ├── compliance.py      # Rules for font size
│   ├── inspection.py      # Core inspection orchestration
│   ├── main.py            # FastAPI entrypoint
│   ├── models.py          # Pydantic models
│   └── ocr.py             # EasyOCR integration
├── Demo                   # Legacy CLI interface
├── README.md              # Documentation
└── requirements.txt       # Project dependencies
```

## Installation
```bash
python -m venv .venv
# Activate the venv (e.g., .venv\Scripts\activate on Windows)
pip install -r requirements.txt
```

## Running the CLI (Demo)
```bash
# Basic test (Missing physical scale will result in UNVERIFIED)
python Demo --image "Assets/Test.jpeg"

# Full validation test
python Demo --image "Assets/Test.jpeg" --pixels_per_mm 10 --pdp_area_cm2 120 --print_type normal
```

## Running FastAPI
```bash
python -m uvicorn app.main:app --reload
```
- Health Check: `http://127.0.0.1:8000/health`
- Swagger UI (Documentation & Testing): `http://127.0.0.1:8000/docs`

## API Example Response
```json
{
    "success": true,
    "inspection": {
        "inspection_target_detected": true,
        "ocr_status": "SUCCESS",
        "font_compliance": "FAIL",
        "overall_status": "FAIL",
        "parameters": {
            "pdp_area_cm2": 120.0,
            "pixels_per_mm": 10.0,
            "print_type": "normal"
        },
        "results": [
            {
                "text": "WEIGHT",
                "confidence": 0.95,
                "bbox": [...],
                "text_height_px": 21,
                "text_height_mm": 2.1,
                "required_mm": 2.5,
                "status": "FAIL",
                "reason": "Measured text height is below required minimum"
            }
        ]
    }
}
```

## Status Meanings
- **PASS**: All applicable mandatory compliance checks pass.
- **FAIL**: At least one applicable mandatory compliance check fails.
- **UNVERIFIED**: No mandatory check has failed, but one or more mandatory checks cannot be performed because required information (like physical scale `pixels_per_mm` or `pdp_area_cm2`) is missing.