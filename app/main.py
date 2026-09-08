# pyrefly: ignore [missing-import]
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from typing import Optional
from app.models import InspectionResponse, InspectionParameters
from app.inspection import run_inspection
import numpy as np
import cv2

from fastapi.middleware.cors import CORSMiddleware
from app.routers import router as api_router

FRONTEND_FILE = Path(__file__).resolve().parent.parent / "Frontend_1.html"

app = FastAPI(
    title="CloudKirana Inspection Backend",
    description="Inspection backend for CloudKirana labeling compliance.",
    version="1.0.0"
)

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

@app.get("/")
def serve_frontend():
    if not FRONTEND_FILE.exists():
        raise HTTPException(status_code=404, detail="Frontend_1.html not found")
    return FileResponse(FRONTEND_FILE)

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "CloudKirana",
        "frontend": "wired"
    }

@app.post("/api/v1/inspect", response_model=InspectionResponse)
async def inspect_endpoint(
    image: UploadFile = File(...),
    pdp_area_cm2: Optional[float] = Form(None),
    pixels_per_mm: Optional[float] = Form(None),
    print_type: Optional[str] = Form("normal")
):
    if print_type not in ["normal", "blown_formed_moulded_embossed"]:
        raise HTTPException(status_code=400, detail="Invalid print_type")

    if not image.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        raise HTTPException(status_code=400, detail="Unsupported image type")

    try:
        contents = await image.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image file")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process image: {str(e)}")

    params = InspectionParameters(
        pdp_area_cm2=pdp_area_cm2,
        pixels_per_mm=pixels_per_mm,
        print_type=print_type
    )

    try:
        response = run_inspection(img, params)
        if not response.success:
            raise HTTPException(status_code=500, detail=response.error)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
