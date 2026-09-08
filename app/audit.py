import hashlib
import json
from typing import Dict, Any, Optional
from datetime import datetime

def record_audit_event(db_client, entity_type: str, entity_id: str, actor_id: str, actor_role: str, action: str, metadata_payload: Dict[str, Any]) -> Optional[str]:
    """
    Records an immutable audit event to the database with a cryptographic hash.
    
    Args:
        db_client: The Supabase client (or other DB interface).
        entity_type: E.g., 'INSPECTION', 'INVOICE', 'INVENTORY_TRANSFER'
        entity_id: The ID of the affected entity.
        actor_id: The ID of the user performing the action.
        actor_role: The role of the user (e.g., 'system', 'retailer').
        action: The action performed (e.g., 'CREATED', 'UPDATED').
        metadata_payload: JSON-serializable dictionary containing event details.
        
    Returns:
        The ID of the created audit log entry, or None if failed.
    """
    if not db_client:
        print("Warning: Database client not available for audit logging.")
        return None

    # Serialize metadata deterministically for hashing
    serialized_payload = json.dumps(metadata_payload, sort_keys=True, separators=(',', ':'))
    
    # Create payload hash for non-repudiation
    # We hash the combination of action, entity, actor and payload
    hash_input = f"{entity_type}:{entity_id}:{actor_id}:{action}:{serialized_payload}"
    payload_hash = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()

    try:
        result = db_client.table("audit_logs").insert({
            "entity_type": entity_type,
            "entity_id": entity_id,
            "actor_id": actor_id,
            "actor_role": actor_role,
            "action": action,
            "payload_hash": payload_hash,
            "metadata": metadata_payload
        }).execute()
        
        if result.data:
            return result.data[0].get("id")
        return None
    except Exception as e:
        print(f"Failed to write audit log: {e}")
        return None
