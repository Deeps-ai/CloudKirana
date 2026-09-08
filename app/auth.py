import json
import base64
import hmac
import hashlib
import time
import os
from enum import Enum
from typing import Dict, Any, List, Optional
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-fallback-key-replace-in-prod")

class Role(str, Enum):
    CONSUMER = "CONSUMER"
    RETAILER = "RETAILER"
    WHOLESALER = "WHOLESALER"
    MANUFACTURER = "MANUFACTURER"
    AUDITOR = "AUDITOR"

# Standard Library JWT Implementation (HS256)
def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')

def _base64url_decode(b64: str) -> bytes:
    padding = '=' * (4 - (len(b64) % 4))
    return base64.urlsafe_b64decode(b64 + padding)

def create_access_token(data: dict, expires_delta_minutes: int = 15) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload = data.copy()
    payload["exp"] = int(time.time()) + (expires_delta_minutes * 60)
    
    header_b64 = _base64url_encode(json.dumps(header).encode('utf-8'))
    payload_b64 = _base64url_encode(json.dumps(payload).encode('utf-8'))
    
    signature_input = f"{header_b64}.{payload_b64}".encode('utf-8')
    signature = hmac.new(SECRET_KEY.encode('utf-8'), signature_input, hashlib.sha256).digest()
    signature_b64 = _base64url_encode(signature)
    
    return f"{header_b64}.{payload_b64}.{signature_b64}"

def verify_token(token: str) -> Optional[dict]:
    parts = token.split('.')
    if len(parts) != 3:
        return None
        
    header_b64, payload_b64, signature_b64 = parts
    
    signature_input = f"{header_b64}.{payload_b64}".encode('utf-8')
    expected_signature = hmac.new(SECRET_KEY.encode('utf-8'), signature_input, hashlib.sha256).digest()
    expected_signature_b64 = _base64url_encode(expected_signature)
    
    if not hmac.compare_digest(signature_b64, expected_signature_b64):
        return None
        
    try:
        payload = json.loads(_base64url_decode(payload_b64).decode('utf-8'))
        if payload.get('exp', 0) < time.time():
            return None # Expired
        return payload
    except Exception:
        return None

# Password Hashing using standard library (PBKDF2 HMAC)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    # hashed_password format: salt$hash (hex strings)
    try:
        salt, expected_hash = hashed_password.split('$')
        new_hash = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), bytes.fromhex(salt), 100000).hex()
        return hmac.compare_digest(new_hash, expected_hash)
    except Exception:
        # Fallback for plain text matching during dev / mocking
        return plain_password == hashed_password

def get_password_hash(password: str) -> str:
    salt = os.urandom(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000).hex()
    return f"{salt.hex()}${hashed}"

# FastAPI Dependencies
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload

def require_role(allowed_roles: List[Role]):
    def role_checker(user: dict = Security(get_current_user)):
        user_role = user.get("role")
        if user_role not in [r.value for r in allowed_roles]:
            raise HTTPException(status_code=403, detail="Insufficient privileges")
        return user
    return role_checker

class LoginRequest(BaseModel):
    phone: str
    password: str # Can also be OTP
