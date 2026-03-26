from datetime import datetime
from typing import Any, Dict, Optional


def safe_publisher(meta: Dict[str, Any]) -> Optional[str]:
    """
    Extract publisher.name or publisher.@id.
    Handles:
    - dict
    - list of dicts
    - missing
    """
    value = meta.get("dct:publisher")

    if value is None:
        return None

    # Case 1: publisher is a dict
    if isinstance(value, dict):
        return value.get("name") or value.get("@id")

    # Case 2: publisher is a list of dicts
    if isinstance(value, list) and value:
        first = value[0]
        if isinstance(first, dict):
            return first.get("name") or first.get("@id")

    return None


def clean_list(values):
    """
    Remove empty strings, None, and non-string items from a list.
    """
    if not isinstance(values, list):
        return []
    return [v for v in values if isinstance(v, str) and v.strip()]


def pick_latest_date(val: Any) -> Optional[str]:
    """
    Accepts:
      - a single ISO date string
      - or a list of ISO date strings
    Returns the *latest* date as ISO string (YYYY-MM-DD).
    """
    if not val:
        return None

    if isinstance(val, str):
        return val  # already single date

    if isinstance(val, list):
        parsed = []
        for v in val:
            if isinstance(v, str):
                try:
                    parsed.append(datetime.fromisoformat(v))
                except ValueError:
                    continue

        if not parsed:
            return None

        # Return the most recent date
        return max(parsed).date().isoformat()

    return None


def extract_metadata(meta: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Safely extract known metadata fields.
    """
    if not isinstance(meta, dict):
        return {}

    return {
        "description": meta.get("dct:abstract"),
        "publication_date": meta.get("dct:issued"),
        "last_update": pick_latest_date(meta.get("dct:updated")),
        "language": meta.get("dct:language"),
        "publisher": safe_publisher(meta),
        "license": clean_list(meta.get("dct:license") or []),
        "keywords": clean_list(meta.get("dcat:keyword") or []),
        "keywords_tg": clean_list(meta.get("dcat:keyword") or []),
        "data_quality": meta.get("dcat:dataQuality"),
        "granularity": meta.get("dcat:granularity"),
    }


def transform_raw_dataset(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Minimal safe transformer operating directly on raw dataset dicts.
    """
    meta = extract_metadata(raw.get("metadata"))

    return {
        "id": raw.get("id") or raw.get("@id"),
        "type": "dataset",
        "catalogue": raw.get("catalogue"),
        "url": raw.get("baseUrl"),
        "version": raw.get("version"),
        "title": raw.get("name"),
        **meta,
        "content_type": raw.get("contenttype"),
    }
