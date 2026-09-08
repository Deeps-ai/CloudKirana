import re
import difflib
from typing import List, Dict, Any, Tuple, Optional

class ProductMatcher:
    def __init__(self, canonical_catalog: List[Dict[str, Any]]):
        """
        Initialize with a master catalog list of dicts.
        Expected format: [{"id": 1, "name": "Aashirvaad Shudh Chakki Atta 5kg", "gtin": "123456789"}, ...]
        """
        self.catalog = canonical_catalog
        # Build GTIN index for O(1) matching
        self.gtin_index = {
            item.get("gtin"): item 
            for item in self.catalog 
            if item.get("gtin")
        }
        # Pre-compute normalized names for fuzzy matching
        for item in self.catalog:
            item["_normalized_name"] = self._normalize_text(item["name"])

    def _normalize_text(self, text: str) -> str:
        """
        Cleans and normalizes text: lowercases, handles weight/vol variations, then removes punctuation.
        """
        if not text:
            return ""
            
        t = text.lower()
        
        # Normalize weights/volumes (e.g. 500 ml -> 500ml, 0.5L -> 500ml, 1 kg -> 1kg)
        t = re.sub(r'(\d+(?:\.\d+)?)\s*(kg|g|gm|gms|l|ml|ltr)\b', lambda m: f"{m.group(1)}{m.group(2)}", t)
        
        # Simple volume normalization (1l -> 1000ml, 1kg -> 1000g)
        def convert_unit(m):
            val = float(m.group(1))
            unit = m.group(2)
            if unit in ('kg', 'l', 'ltr'):
                return f"{int(val * 1000)}{'g' if unit == 'kg' else 'ml'}"
            if unit in ('gm', 'gms'):
                return f"{int(val)}g"
            # If it's a float that couldn't be safely converted without decimal loss, keep float format if needed, but for g/ml int is fine
            return f"{int(val)}{unit}"
            
        t = re.sub(r'(\d+(?:\.\d+)?)(kg|g|gm|gms|l|ml|ltr)\b', convert_unit, t)
        
        # Now remove punctuation
        t = re.sub(r'[^\w\s]', ' ', t)

        # Standardize extra spaces
        t = re.sub(r'\s+', ' ', t).strip()
        return t

    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """
        Calculates similarity ratio using Python's built-in SequenceMatcher.
        Returns score from 0.0 to 1.0.
        """
        return difflib.SequenceMatcher(None, s1, s2).ratio()

    def match(self, query_name: str, query_gtin: Optional[str] = None) -> Dict[str, Any]:
        """
        Matches a query against the canonical catalog.
        Returns dict with:
        - status: "MATCHED", "SUGGESTIONS", "UNMATCHED"
        - confidence: float
        - match: item dict (if MATCHED)
        - suggestions: list of item dicts (if SUGGESTIONS)
        """
        # 1. Exact match by GTIN
        if query_gtin and query_gtin in self.gtin_index:
            return {
                "status": "MATCHED",
                "confidence": 1.0,
                "match": self.gtin_index[query_gtin]
            }

        if not query_name:
            return {"status": "UNMATCHED", "confidence": 0.0}

        # 2. Fuzzy ratio matching
        norm_query = self._normalize_text(query_name)
        
        results = []
        for item in self.catalog:
            norm_item = item["_normalized_name"]
            score = self._calculate_similarity(norm_query, norm_item)
            results.append((score, item))

        # Sort by score descending
        results.sort(key=lambda x: x[0], reverse=True)
        
        if not results:
            return {"status": "UNMATCHED", "confidence": 0.0}

        top_score, top_item = results[0]

        if top_score >= 0.85:
            return {
                "status": "MATCHED",
                "confidence": top_score,
                "match": top_item
            }
        elif top_score >= 0.60:
            return {
                "status": "SUGGESTIONS",
                "confidence": top_score,
                "suggestions": [item for score, item in results[:3] if score >= 0.60]
            }
        else:
            return {
                "status": "UNMATCHED",
                "confidence": top_score
            }
