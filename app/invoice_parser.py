import re
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel
from uuid import UUID
import numpy as np
import cv2
from app.ocr import get_reader
from app.matcher import ProductMatcher

class InvoiceItem(BaseModel):
    item_name: str
    hsn_code: Optional[str] = None
    quantity: float
    unit_price: float
    batch_number: Optional[str] = None
    expiry_date: Optional[str] = None
    matched_product_id: Optional[str] = None
    match_status: str = "UNMATCHED"
    suggestions: Optional[List[Dict[str, Any]]] = None

class InvoiceData(BaseModel):
    supplier_gstin: str
    invoice_number: str
    invoice_date: str
    items: List[InvoiceItem]
    total_amount: float

def parse_invoice_image(image_input: Union[str, np.ndarray], matcher: Optional[ProductMatcher] = None) -> Dict[str, Any]:
    if isinstance(image_input, str):
        image = cv2.imread(image_input)
        if image is None:
            return {"status": "error", "message": "Invalid image"}
    else:
        image = image_input

    try:
        reader = get_reader()
        # Read text with paragraph=False to get line-level bounding boxes
        results = reader.readtext(image)
        
        # Sort results roughly top-to-bottom, left-to-right
        results.sort(key=lambda x: (x[0][0][1], x[0][0][0]))
        
        lines = []
        # Group text into lines heuristically
        current_line = []
        current_y = -1
        y_tolerance = 15 # pixels tolerance for same line
        
        for bbox, text, conf in results:
            y = bbox[0][1]
            if current_y == -1 or abs(y - current_y) <= y_tolerance:
                current_line.append((bbox[0][0], text))
                if current_y == -1:
                    current_y = y
            else:
                current_line.sort(key=lambda x: x[0])
                lines.append(" ".join([t[1] for t in current_line]))
                current_line = [(bbox[0][0], text)]
                current_y = y
                
        if current_line:
            current_line.sort(key=lambda x: x[0])
            lines.append(" ".join([t[1] for t in current_line]))

        supplier_gstin = ""
        invoice_number = ""
        invoice_date = ""
        total_amount = 0.0
        parsed_items: List[InvoiceItem] = []
        
        # Patterns
        gstin_pattern = re.compile(r'\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}', re.IGNORECASE)
        inv_no_pattern = re.compile(r'(?:INV|Invoice No|Bill No)[^\w]*([A-Z0-9/-]+)', re.IGNORECASE)
        date_pattern = re.compile(r'(?:Date)[^\d]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', re.IGNORECASE)
        total_pattern = re.compile(r'(?:Total|Grand Total)[^\d]*(\d+(?:\.\d{1,2})?)', re.IGNORECASE)
        
        # Item row pattern (simplified for prototype: looks for quantity and price numbers at the end)
        # Matches: [Name] [Optional HSN] [Qty] [Rate] [Amount]
        item_pattern = re.compile(r'^(.*?)\s+(?:(\d{4,8})\s+)?(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)$')
        
        # Batch and expiry heuristic (often below or near item name)
        batch_pattern = re.compile(r'(?:B\.?No|Batch)[^\w]*([A-Z0-9]+)', re.IGNORECASE)
        exp_pattern = re.compile(r'(?:Exp|Expiry)[^\w]*(\d{1,2}[/-]\d{2,4})', re.IGNORECASE)

        in_items_section = False

        for line in lines:
            line_str = line.strip()
            
            # Extract header info
            if not supplier_gstin:
                match = gstin_pattern.search(line_str)
                if match: supplier_gstin = match.group(0)
                
            if not invoice_number:
                # Avoid matching the word 'Invoice' itself
                if 'INV' in line_str.upper() or 'NO' in line_str.upper() or 'BILL' in line_str.upper():
                    match = re.search(r'(?:INV[- ]?NO|INVOICE[- ]?NO|BILL[- ]?NO)[^\w]*([A-Z0-9/-]+)', line_str, re.IGNORECASE)
                    if match: invoice_number = match.group(1)
                
            if not invoice_date:
                match = date_pattern.search(line_str)
                if match: invoice_date = match.group(1)
                
            match = total_pattern.search(line_str)
            if match:
                try:
                    total_amount = float(match.group(1))
                except ValueError:
                    pass

            # Detect Items Section
            lower_line = line_str.lower()
            if 'qty' in lower_line and ('rate' in lower_line or 'price' in lower_line):
                in_items_section = True
                continue
                
            if in_items_section:
                # Try matching item row
                item_match = item_pattern.match(line_str)
                if item_match:
                    name = item_match.group(1).strip()
                    hsn = item_match.group(2)
                    qty = float(item_match.group(3))
                    rate = float(item_match.group(4))
                    
                    # Match Canonical Product
                    m_id = None
                    m_status = "UNMATCHED"
                    suggs = None
                    
                    if matcher:
                        m_res = matcher.match(name)
                        m_status = m_res["status"]
                        if m_status == "MATCHED":
                            m_id = str(m_res["match"]["id"])
                        elif m_status == "SUGGESTIONS":
                            suggs = m_res["suggestions"]
                            
                    parsed_items.append(InvoiceItem(
                        item_name=name,
                        hsn_code=hsn,
                        quantity=qty,
                        unit_price=rate,
                        matched_product_id=m_id,
                        match_status=m_status,
                        suggestions=suggs
                    ))
                else:
                    # Look for batch/exp modifiers for the last item
                    if parsed_items:
                        b_match = batch_pattern.search(line_str)
                        if b_match: parsed_items[-1].batch_number = b_match.group(1)
                        e_match = exp_pattern.search(line_str)
                        if e_match: parsed_items[-1].expiry_date = e_match.group(1)

        # Fallbacks for empty required fields
        if not supplier_gstin: supplier_gstin = "UNKNOWN_GSTIN"
        if not invoice_number: invoice_number = "INV-UNKNOWN"
        if not invoice_date: invoice_date = "UNKNOWN_DATE"

        invoice_data = InvoiceData(
            supplier_gstin=supplier_gstin,
            invoice_number=invoice_number,
            invoice_date=invoice_date,
            items=parsed_items,
            total_amount=total_amount
        )
        
        return {"status": "success", "data": invoice_data.model_dump()}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

