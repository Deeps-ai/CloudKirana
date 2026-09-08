import cv2
import easyocr
import numpy as np
from typing import Dict, Any, Union, List, Optional, Tuple

_reader = None
_qr_detector = None
_barcode_detector = None

def get_reader():
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(["en"], gpu=False)
    return _reader

def get_qr_detector():
    global _qr_detector
    if _qr_detector is None:
        _qr_detector = cv2.QRCodeDetector()
    return _qr_detector

def get_barcode_detector():
    global _barcode_detector
    if _barcode_detector is None:
        if hasattr(cv2, "barcode_BarcodeDetector"):
            _barcode_detector = cv2.barcode_BarcodeDetector()
    return _barcode_detector

def isolate_packaging_region(image: np.ndarray) -> Tuple[Optional[List[int]], np.ndarray]:
    """
    Isolates the primary packaging/label region using grayscale conversion,
    morphological gradient, and adaptive thresholding if background noise exists.
    Returns (label_crop_coordinates [x, y, w, h], processed_image_for_ocr).
    """
    if image is None or image.size == 0:
        return None, image

    h, w = image.shape[:2]
    
    # Do not crop if image is too small
    if h < 50 or w < 50:
        return None, image

    try:
        # Grayscale conversion
        if len(image.shape) == 3 and image.shape[2] == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        elif len(image.shape) == 3 and image.shape[2] == 4:
            gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
        else:
            gray = image.copy()

        # Morphological gradient to emphasize label edges and boundary transitions
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        gradient = cv2.morphologyEx(gray, cv2.MORPH_GRADIENT, kernel)

        # Adaptive thresholding to segment salient packaging/label areas
        thresh = cv2.adaptiveThreshold(
            gradient,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            15,
            -2
        )

        # Morphological closing to connect nearby components into coherent region
        close_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, close_kernel)

        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        total_area = float(w * h)
        best_box = None
        max_area = 0

        for cnt in contours:
            x_b, y_b, w_b, h_b = cv2.boundingRect(cnt)
            area = w_b * h_b
            # Check if contour is significant (>15% of image and not the entire canvas edge artifact)
            if area > 0.15 * total_area and area < 0.98 * total_area:
                if area > max_area:
                    max_area = area
                    best_box = [x_b, y_b, w_b, h_b]

        if best_box is not None:
            bx, by, bw, bh = best_box
            # Add a small 2% margin around the detected box
            pad_x = int(bw * 0.02)
            pad_y = int(bh * 0.02)
            crop_x1 = max(0, bx - pad_x)
            crop_y1 = max(0, by - pad_y)
            crop_x2 = min(w, bx + bw + pad_x)
            crop_y2 = min(h, by + bh + pad_y)
            
            crop_coords = [crop_x1, crop_y1, crop_x2 - crop_x1, crop_y2 - crop_y1]
            # Use cropped image for OCR only if meaningful crop
            if (crop_x2 - crop_x1) > 40 and (crop_y2 - crop_y1) > 40:
                cropped_img = image[crop_y1:crop_y2, crop_x1:crop_x2]
                return crop_coords, cropped_img

        return None, image
    except Exception:
        return None, image

def decode_barcodes_and_qrcodes(image: np.ndarray) -> Tuple[List[Dict[str, Any]], Optional[float]]:
    """
    Decodes Barcodes and QR Codes using OpenCV (and pyzbar if available).
    Calculates estimated pixels-per-mm reference if a standard barcode (e.g. EAN-13 ~37.29mm) is detected.
    Returns (barcodes_list, estimated_pixels_per_mm).
    """
    barcodes: List[Dict[str, Any]] = []
    estimated_px_per_mm: Optional[float] = None

    if image is None or image.size == 0:
        return barcodes, estimated_px_per_mm

    # 1. Check pyzbar if available
    try:
        import pyzbar.pyzbar as pyzbar
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        decoded_objs = pyzbar.decode(gray)
        for obj in decoded_objs:
            data_str = obj.data.decode("utf-8", errors="ignore")
            sym_type = obj.type
            rect = obj.rect
            bbox = [[rect.left, rect.top],
                    [rect.left + rect.width, rect.top],
                    [rect.left + rect.width, rect.top + rect.height],
                    [rect.left, rect.top + rect.height]]
            barcodes.append({
                "data": data_str,
                "type": sym_type,
                "bbox": bbox
            })
            if sym_type in ("EAN13", "EAN-13", "UPCA", "UPC-A") and rect.width > 0:
                # EAN-13 nominal standard width is ~37.29 mm
                estimated_px_per_mm = round(float(rect.width) / 37.29, 2)
    except Exception:
        pass

    # 2. OpenCV QR Code Detector
    try:
        qr_detector = get_qr_detector()
        # Try detectAndDecodeMulti or detectAndDecode
        if hasattr(qr_detector, "detectAndDecodeMulti"):
            retval, decoded_infos, points, _ = qr_detector.detectAndDecodeMulti(image)
            if retval and points is not None:
                for idx, text in enumerate(decoded_infos):
                    if text:
                        pts = points[idx].tolist() if idx < len(points) else []
                        barcodes.append({
                            "data": text,
                            "type": "QR_CODE",
                            "bbox": pts
                        })
        else:
            text, points, _ = qr_detector.detectAndDecode(image)
            if text and points is not None:
                pts = points[0].tolist() if len(points.shape) == 3 else points.tolist()
                barcodes.append({
                    "data": text,
                    "type": "QR_CODE",
                    "bbox": pts
                })
    except Exception:
        pass

    # 3. OpenCV Barcode Detector (EAN-13, EAN-8, UPC-A, UPC-E, etc.)
    try:
        b_detector = get_barcode_detector()
        if b_detector is not None:
            ret, texts, types, points = b_detector.detectAndDecodeWithType(image)
            if ret and texts and points is not None:
                for idx, (data_str, b_type) in enumerate(zip(texts, types)):
                    if data_str:
                        pts = points[idx].tolist() if idx < len(points) else []
                        
                        # Normalize type name
                        type_name = str(b_type).upper()
                        if "EAN_13" in type_name or "EAN13" in type_name:
                            type_name = "EAN-13"
                        elif "UPC_A" in type_name or "UPCA" in type_name:
                            type_name = "UPC-A"
                        elif "QR" in type_name:
                            type_name = "QR_CODE"
                            
                        barcodes.append({
                            "data": data_str,
                            "type": type_name,
                            "bbox": pts
                        })

                        # Estimate pixels per mm if width can be measured
                        if estimated_px_per_mm is None and pts and len(pts) >= 4:
                            xs = [p[0] for p in pts]
                            barcode_w_px = max(xs) - min(xs)
                            if barcode_w_px > 10:
                                # Standard nominal EAN-13 width is ~37.29 mm
                                estimated_px_per_mm = round(float(barcode_w_px) / 37.29, 2)
    except Exception:
        pass

    # Deduplicate barcodes by data string if multiple detectors returned the same
    unique_barcodes: List[Dict[str, Any]] = []
    seen = set()
    for b in barcodes:
        key = (b["data"], b["type"])
        if key not in seen:
            seen.add(key)
            unique_barcodes.append(b)

    return unique_barcodes, estimated_px_per_mm

def inspect_text(image_input: Union[str, np.ndarray], pixels_per_mm_ref: Optional[float] = None) -> Dict[str, Any]:
    """
    Preprocesses packaging area, detects Barcodes/QRs, runs OCR, and calculates text metrics.
    Returns consolidated payload:
    - barcodes: List[Dict[str, Any]]
    - detected_texts / text_regions: List[Dict[str, Any]]
    - label_crop_coordinates: Optional[List[int]]
    - estimated_pixels_per_mm: Optional[float]
    - ocr_status: "SUCCESS" | "ERROR"
    """
    if isinstance(image_input, str):
        image = cv2.imread(image_input)
        if image is None:
            return {
                "ocr_status": "ERROR",
                "error": f"Could not read image from {image_input}",
                "barcodes": [],
                "detected_texts": [],
                "text_regions": [],
                "label_crop_coordinates": None
            }
    else:
        image = image_input

    try:
        # 1. Detect barcodes & QR codes before heavy modifications
        barcodes, auto_px_per_mm = decode_barcodes_and_qrcodes(image)
        active_px_per_mm = pixels_per_mm_ref or auto_px_per_mm

        # 2. Isolate packaging / label area
        crop_coords, proc_image = isolate_packaging_region(image)
        offset_x = crop_coords[0] if crop_coords else 0
        offset_y = crop_coords[1] if crop_coords else 0

        # 3. Run EasyOCR on the image (using the packaging region or full image)
        reader = get_reader()
        results = reader.readtext(proc_image)

        detected_texts = []
        for bbox, text, conf in results:
            # Map coordinates back to full image space if cropped
            bbox_native = [[float(x + offset_x), float(y + offset_y)] for x, y in bbox]
            ys = [p[1] for p in bbox_native]
            height_px = max(ys) - min(ys)
            
            height_mm = None
            if active_px_per_mm and active_px_per_mm > 0:
                height_mm = round(float(height_px) / active_px_per_mm, 2)

            item = {
                "text": text,
                "confidence": float(conf),
                "text_height_px": int(height_px),
                "text_height_mm": height_mm,
                "bbox": bbox_native
            }
            detected_texts.append(item)

        return {
            "ocr_status": "SUCCESS",
            "barcodes": barcodes,
            "detected_texts": detected_texts,
            "text_regions": detected_texts,  # Keep text_regions for backwards-compatibility
            "label_crop_coordinates": crop_coords,
            "estimated_pixels_per_mm": auto_px_per_mm
        }
    except Exception as e:
        return {
            "ocr_status": "ERROR",
            "error": str(e),
            "barcodes": [],
            "detected_texts": [],
            "text_regions": [],
            "label_crop_coordinates": None
        }
