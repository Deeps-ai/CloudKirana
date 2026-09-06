# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from app.models import (
    AuthRequest, AuthVerify, ONDCSyncRequest, InventoryAddRequest,
    InvoiceUpdateRequest, OrderRequest, NoticeRequest, RecallRequest
)
from app.db import supabase
import uuid

router = APIRouter()

# --- Auth ---
@router.post("/auth/send-otp")
async def send_otp(request: AuthRequest):
    # Mock OTP send
    return {"message": "OTP sent successfully"}

@router.post("/auth/verify-otp")
async def verify_otp(request: AuthVerify):
    # Mock OTP verification (accept any 4 digits for prototype)
    if not request.otp or len(request.otp) != 4:
        raise HTTPException(status_code=400, detail="Invalid OTP format")
    
    # Upsert user based on phone for prototype
    res = supabase.table("users").select("*").eq("phone", request.phone).execute()
    if not res.data:
        # Create a mock business and user
        business = supabase.table("businesses").insert({
            "name": f"Store for {request.phone}",
            "role": "retailer"
        }).execute()
        
        user = supabase.table("users").insert({
            "phone": request.phone,
            "business_id": business.data[0]["id"],
            "role": "retailer"
        }).execute()
        token = str(user.data[0]["id"]) # Use user ID as token for prototype
    else:
        token = str(res.data[0]["id"])
        
    return {"token": token, "role": "retailer"}

# --- Retailer ---
@router.get("/retailer/profile")
async def get_retailer_profile():
    return {
        "name": "Sharma Provision Store (API)",
        "address": "Sector 4, Greater Noida",
        "ondcSyncEnabled": True
    }

@router.get("/retailer/inventory")
async def get_inventory():
    return [
        {"id": 1, "name": "Tata Salt 1kg", "stock": 42, "mrp": 28, "compliant": True},
        {"id": 2, "name": "Maggi Noodles 70g", "stock": 105, "mrp": 14, "compliant": True},
        {"id": 3, "name": "Local Brand Sugar 1kg", "stock": 15, "mrp": 45, "compliant": False}
    ]

@router.post("/retailer/ondc-sync")
async def toggle_ondc_sync(request: ONDCSyncRequest):
    return {"status": "success", "enabled": request.enabled}

@router.post("/retailer/update-stock")
async def update_stock(request: dict):
    # Handle inventory addition from invoice
    return {"status": "success"}

# --- Consumer ---
@router.get("/consumer/products")
async def get_consumer_products():
    return [
        {"id": 1, "name": "Tata Salt 1kg", "price": 28, "verified": True},
        {"id": 2, "name": "Maggi Noodles 70g", "price": 14, "verified": True},
    ]

@router.post("/consumer/checkout")
async def checkout(request: OrderRequest):
    return {"status": "success", "orderId": str(uuid.uuid4())}

# --- Authority ---
@router.get("/authority/incidents/latest")
async def get_latest_incident():
    return {
        "id": "8842",
        "storeName": "Sharma Provision Store (API)",
        "location": "Sector 4, Greater Noida",
        "timestamp": "10:43 PM IST, Sep 5, 2026",
        "rules": [
            {"id": 1, "name": "Retail Sale Price (MRP)", "value": "₹45.00", "status": "Match"},
            {"id": 2, "name": "Net Quantity", "value": "200g", "status": "Match"},
            {"id": 3, "name": "Manufacturer Details", "value": "NOT FOUND", "status": "Violation"},
            {"id": 4, "name": "Country of Origin (2026 Rule)", "value": "NOT FOUND", "status": "Violation"}
        ]
    }

@router.post("/authority/incidents/{incident_id}/notice")
async def issue_notice(incident_id: str):
    return {"status": "success"}

@router.post("/authority/incidents/{incident_id}/recall")
async def recall_batch(incident_id: str):
    return {"status": "success"}
