import cv2
import easyocr
import numpy as np
from typing import Dict, Any, Union

_reader = None

def get_reader():
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(["en"], gpu=False)
    return _reader

def inspect_text(image_input: Union[str, np.ndarray]) -> Dict[str, Any]:
    if isinstance(image_input, str):
        image = cv2.imread(image_input)
        if image is None:
            return {
                "ocr_status": "ERROR",
                "error": f"Could not read image from {image_input}"
            }
    else:
        image = image_input

    try:
        reader = get_reader()
        results = reader.readtext(image)

        text_regions = []
        for bbox, text, conf in results:
            ys = [p[1] for p in bbox]
            height_px = max(ys) - min(ys)
            
            bbox_native = [[float(x), float(y)] for x, y in bbox]
            
            text_regions.append({
                "text": text,
                "confidence": float(conf),
                "text_height_px": int(height_px),
                "bbox": bbox_native
            })

        return {
            "ocr_status": "SUCCESS",
            "text_regions": text_regions
        }
    except Exception as e:
        return {
            "ocr_status": "ERROR",
            "error": str(e)
        }
