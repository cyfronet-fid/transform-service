from datetime import datetime
from typing import Any, Dict, List, Optional

FOAF_NAME_KEY = "http://xmlns.com/foaf/0.1/name"


def first_nonempty_string(values: List[Any]) -> Optional[str]:
    """
    Return the first non-empty string from a list of candidate values.

    This is used for metadata fields that may expose the same semantic value
    under several keys, for example publisher name under both ``name`` and
    ``foaf:name``-style keys.
    """
    for value in values:
        if isinstance(value, str) and value.strip():
            return value
    return None


def safe_publisher(meta: Dict[str, Any]) -> Optional[str]:
    """
    Extract a publisher label from ``dct:publisher``.

    Supported input shapes:
    - a single dict
    - a list whose first element is a dict

    Supported keys, in order of preference:
    - ``name``
    - ``http://xmlns.com/foaf/0.1/name``
    - ``@id``
    """
    value = meta.get("dct:publisher")

    if value is None:
        return None

    # Case 1: publisher is a dict
    if isinstance(value, dict):
        return first_nonempty_string(
            [
                value.get("name"),
                value.get(FOAF_NAME_KEY),
                value.get("@id"),
            ]
        )

    # Case 2: publisher is a list of dicts
    if isinstance(value, list) and value:
        first = value[0]
        if isinstance(first, dict):
            return first_nonempty_string(
                [
                    first.get("name"),
                    first.get(FOAF_NAME_KEY),
                    first.get("@id"),
                ]
            )

    return None


def clean_list(values):
    """
    Normalize metadata values to a list of non-empty strings.

    Some SAGE fields arrive as a single string, while others arrive as a list.
    This helper accepts both shapes and drops empty or non-string values.
    """
    if isinstance(values, str):
        return [values] if values.strip() else []
    if not isinstance(values, list):
        return []
    return [v for v in values if isinstance(v, str) and v.strip()]


def unique_strings(values: List[str]) -> List[str]:
    """
    Return strings in their original order without duplicates.

    This keeps the output stable while preventing repeated metadata values from
    multiple sources such as repeated distributions.
    """
    seen = set()
    result = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def extract_licenses(meta: Dict[str, Any]) -> List[str]:
    """
    Extract licenses from dataset-level metadata and GeoDCAT distributions.

    We keep dataset-level ``dct:license`` for backward compatibility, but the
    current SAGE/GeoDCAT records expose licenses primarily under
    ``dcat:distribution`` -> ``dct:license``. ``dcat:distribution`` may be
    either a single dict or a list of dicts, so both forms are supported.
    """
    licenses = clean_list(meta.get("dct:license") or [])
    distributions = meta.get("dcat:distribution")

    if isinstance(distributions, dict):
        licenses.extend(clean_list(distributions.get("dct:license") or []))
    elif isinstance(distributions, list):
        for distribution in distributions:
            if isinstance(distribution, dict):
                licenses.extend(clean_list(distribution.get("dct:license") or []))

    return unique_strings(licenses)


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


def extract_catalogue_name(catalogue: Optional[str]) -> Optional[str]:
    _CATALOGUE_NAME_MAP = {
        "edwin": "EDWIN",
        "sage-public": "Sage Public",
    }

    if not catalogue or not isinstance(catalogue, str):
        return None

    last_segment = catalogue.rsplit(":", 1)[-1].strip()
    if not last_segment:
        return None

    if last_segment in _CATALOGUE_NAME_MAP:
        return _CATALOGUE_NAME_MAP[last_segment]

    # Fallback: kebab-case -> Title Case
    return last_segment.replace("-", " ").title()


def extract_metadata(meta: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Normalize selected dataset metadata for indexing.

    The transformer intentionally extracts only a small, flat subset of the
    source metadata. Where current SAGE data differs from older assumptions, we
    adapt here, for example by reading licenses from ``dcat:distribution`` and
    accepting both string and list forms for keywords.
    """
    if not isinstance(meta, dict):
        return {}

    return {
        "description": meta.get("dct:abstract"),
        "publication_date": meta.get("dct:issued"),
        "last_update": pick_latest_date(meta.get("dct:updated")),
        "language": meta.get("dct:language"),
        "publisher": safe_publisher(meta),
        "license": extract_licenses(meta),
        "keywords": clean_list(meta.get("dcat:keyword") or []),
        "keywords_tg": clean_list(meta.get("dcat:keyword") or []),
        "data_quality": meta.get("dcat:dataQuality"),
        "granularity": meta.get("dcat:granularity"),
    }


def transform_raw_dataset(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build the indexed dataset document from a raw SAGE dataset record.

    Dataset-level fields are copied directly from the raw payload, while the
    nested ``metadata`` object is normalized through ``extract_metadata()``.
    """
    meta = extract_metadata(raw.get("metadata"))

    return {
        "id": raw.get("id") or raw.get("@id"),
        "type": "dataset",
        "catalogue": extract_catalogue_name(raw.get("catalogue")),
        "participant_id": raw.get("participant_id"),
        "url": raw.get("baseUrl"),
        "version": raw.get("version"),
        "title": raw.get("name"),
        "originator": raw.get("originator"),
        **meta,
        "content_type": raw.get("contenttype"),
    }
