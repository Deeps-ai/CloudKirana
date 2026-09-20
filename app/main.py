# pyrefly: ignore [missing-import]
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
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
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_origins=["null"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app.include_router(api_router, prefix="/api")


# Mount Assets if directory exists
assets_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Assets")
if os.path.exists(assets_path):
    app.mount("/Assets", StaticFiles(directory=assets_path), name="assets")

@app.get("/")
def read_root():
    frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Frontend_1.html")
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)
    return {
        "status": "ok",
        "service": "CloudKirana"
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "CloudKirana",
        "frontend": "wired"
    }

from app.audit import record_audit_event
from app.invoice_parser import parse_invoice_image, InvoiceData
from app.matcher import ProductMatcher
from app.db import supabase
from app.auth import Role, create_access_token, verify_password, require_role, LoginRequest

@app.post("/api/auth/login")
def login(request: LoginRequest):
    if not supabase:
        # Fallback for dev without DB
        if request.phone == "1234567890":
            return {
                "access_token": create_access_token({"id": "mock-id", "role": "RETAILER", "business_id": "mock-biz"}),
                "user": {"id": "mock-id", "role": "RETAILER"}
            }
        raise HTTPException(status_code=500, detail="Database not connected")
        
    res = supabase.table("users").select("id, role, business_id").eq("phone", request.phone).execute()
    if not res.data:
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    user = res.data[0]
    # For now, bypassing password validation assuming OTP handles it, or using dummy mock
    # In full prod, we'd verify password hash here
    
    token_data = {
        "id": user["id"],
        "role": user["role"],
        "business_id": user.get("business_id")
    }
    access_token = create_access_token(token_data)
    
    return {
        "access_token": access_token,
        "user": token_data
    }

@app.post("/inspect", response_model=InspectionResponse)
@app.post("/api/v1/inspect", response_model=InspectionResponse)
async def inspect_endpoint(
    image: UploadFile = File(...),
    pdp_area_cm2: float = Form(120.0),
    pixels_per_mm: float = Form(10.0),
    print_type: str = Form("normal"),
    region: str = Form("Unknown"),
    pincode: str = Form("Unknown"),
    supplier_id: str = Form("Unknown"),
    brand_name: str = Form("Unknown")
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
            
        # Log immutable audit event
        if supabase:
            violation_categories = []
            if response.data and response.data.declarations:
                for dec in response.data.declarations:
                    if not dec.is_compliant:
                        violation_categories.append(f"Missing/Invalid {dec.field_name}")
                        
            metadata = {
                "region": region,
                "pincode": pincode,
                "supplier_id": supplier_id,
                "brand_name": brand_name,
                "overall_compliance_score": response.data.overall_compliance_score if response.data else 0,
                "status": response.data.status if response.data else "UNKNOWN",
                "violation_categories": violation_categories
            }
            
            # Generating a random entity ID for the inspection instance
            import uuid
            inspection_id = str(uuid.uuid4())
            
            record_audit_event(
                db_client=supabase,
                entity_type="INSPECTION",
                entity_id=inspection_id,
                actor_id="system", # Assuming system automated check
                actor_role="system",
                action="INSPECTION_COMPLETED",
                metadata_payload=metadata
            )
            
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.get("/api/authority/dashboard")
async def authority_dashboard():
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
        
    try:
        # Fetch all inspection audit logs
        res = supabase.table("audit_logs").select("*").eq("entity_type", "INSPECTION").execute()
        logs = res.data
        
        total_inspected = len(logs)
        compliant_count = 0
        violations_count = 0
        
        by_region = {}
        by_brand = {}
        violation_tally = {}
        
        for log in logs:
            meta = log.get("metadata", {})
            status = meta.get("status")
            if status == "COMPLIANT":
                compliant_count += 1
            else:
                violations_count += 1
                
            region = meta.get("region", "Unknown")
            by_region[region] = by_region.get(region, 0) + 1
            
            brand = meta.get("brand_name", "Unknown")
            by_brand[brand] = by_brand.get(brand, 0) + 1
            
            for cat in meta.get("violation_categories", []):
                violation_tally[cat] = violation_tally.get(cat, 0) + 1
                
        # Simple percentage calculation
        compliant_pct = (compliant_count / total_inspected * 100) if total_inspected > 0 else 0
        violations_pct = (violations_count / total_inspected * 100) if total_inspected > 0 else 0
        
        return {
            "total_inspected": total_inspected,
            "compliant_pct": round(compliant_pct, 2),
            "violations_pct": round(violations_pct, 2),
            "groupings": {
                "by_region": by_region,
                "by_brand": by_brand,
                "violation_categories": violation_tally
            },
            "timeseries": [
                # In a real scenario, group logs by date here.
                # Returning dummy timeseries structure based on logs
                {"date": log.get("timestamp")[:10] if log.get("timestamp") else "Unknown", "count": 1} 
                for log in logs
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from app.invoice_parser import parse_invoice_image, InvoiceData
from app.matcher import ProductMatcher
from app.db import supabase

@app.post("/api/invoices/process")
async def process_invoice(image: UploadFile = File(...)):
    if not image.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        raise HTTPException(status_code=400, detail="Unsupported image type")
    
    try:
        contents = await image.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image file")
            
        matcher = None
        if supabase:
            res_prod = supabase.table("products").select("id, name, gtin").execute()
            if res_prod.data:
                matcher = ProductMatcher(res_prod.data)
            
        result = parse_invoice_image(img, matcher=matcher)
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result.get("message"))
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process image: {str(e)}")

@app.post("/api/inventory/sync-invoice")
async def sync_inventory_from_invoice(invoice: InvoiceData, store_id: str):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
        
    try:
        for item in invoice.items:
            # 1. Find or create product
            res_prod = supabase.table("products").select("id").eq("name", item.item_name).execute()
            if not res_prod.data:
                # Create product
                new_prod = supabase.table("products").insert({
                    "name": item.item_name,
                    "mrp": item.unit_price,  # Assuming unit_price as MRP for simplicity
                    "category": "Uncategorized"
                }).execute()
                product_id = new_prod.data[0]["id"]
            else:
                product_id = res_prod.data[0]["id"]
                
            # 2. Update inventory items
            res_inv = supabase.table("inventory_items").select("id, quantity").eq("business_id", store_id).eq("product_id", product_id).execute()
            if res_inv.data:
                new_qty = res_inv.data[0]["quantity"] + item.quantity
                supabase.table("inventory_items").update({"quantity": new_qty}).eq("id", res_inv.data[0]["id"]).execute()
            else:
                supabase.table("inventory_items").insert({
                    "business_id": store_id,
                    "product_id": product_id,
                    "quantity": item.quantity
                }).execute()
                
            # 3. Create batch
            supabase.table("batches").insert({
                "product_id": product_id,
                "batch_no": item.batch_number or "UNKNOWN",
                "expiry_date": item.expiry_date,
                "stock_qty": item.quantity,
                "mrp": item.unit_price
            }).execute()
            
            # 4. Log stock transaction
            supabase.table("stock_transactions").insert({
                "store_id": store_id,
                "product_id": product_id,
                "type": "INVOICE_IN",
                "qty_change": item.quantity,
                "reference_id": invoice.invoice_number
            }).execute()
            
        return {"status": "success", "message": "Inventory synced successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

