from datetime import datetime
from typing import Any, Dict, List, Optional

FOAF_NAME_KEY = "http://xmlns.com/foaf/0.1/name"

DCAT_DISTRIBUTION = "http://www.w3.org/ns/dcat#distribution"
DCAT_KEYWORD = "http://www.w3.org/ns/dcat#keyword"
DCAT_DATA_QUALITY = "http://www.w3.org/ns/dcat#dataQuality"
DCAT_GRANULARITY = "http://www.w3.org/ns/dcat#granularity"

DCT_DESCRIPTION = "http://purl.org/dc/terms/description"
DCT_ISSUED = "http://purl.org/dc/terms/issued"
DCT_UPDATED = "http://purl.org/dc/terms/modified"
DCT_LANGUAGE = "http://purl.org/dc/terms/language"
DCT_PUBLISHER = "http://purl.org/dc/terms/publisher"
DCT_LICENSE = "http://purl.org/dc/terms/license"

EDC_ID = "edc:id"
EDC_NAME = "edc:name"
EDC_VERSION = "edc:version"
EDC_METADATA = "edc:metadata"
EDC_CONTENT_TYPE = "edc:contenttype"
EDC_BASE_URL = "edc:baseUrl"


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
    Extract a publisher label from dct:publisher.

    Supported input shapes:
    - a single dict
    - a list whose first element is a dict

    Supported keys, in order of preference:
    - ``name``
    - ``http://xmlns.com/foaf/0.1/name``
    - ``@id``
    """
    value = meta.get(DCT_PUBLISHER)

    # Backward compatibility with Federated Catalog 0.14.
    if value is None:
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

    Supports both the new 0.17 JSON-LD keys and the old 0.14 keys.
    ``dcat:distribution`` may be either a single dict or a list of dicts.
    """
    licenses = clean_list(meta.get(DCT_LICENSE) or meta.get("dct:license") or [])

    distributions = meta.get(DCAT_DISTRIBUTION)

    # Backward compatibility with Federated Catalog 0.14.
    if distributions is None:
        distributions = meta.get("dcat:distribution")

    if isinstance(distributions, dict):
        licenses.extend(
            clean_list(
                distributions.get(DCT_LICENSE) or distributions.get("dct:license") or []
            )
        )

    elif isinstance(distributions, list):
        for distribution in distributions:
            if isinstance(distribution, dict):
                licenses.extend(
                    clean_list(
                        distribution.get(DCT_LICENSE)
                        or distribution.get("dct:license")
                        or []
                    )
                )

    return unique_strings(licenses)


def pick_latest_date(val: Any) -> Optional[str]:
    """
    Accepts:
    - a single ISO date string
    - or a list of ISO date strings

    Returns the latest date as ISO string (YYYY-MM-DD).
    """
    if not val:
        return None

    if isinstance(val, str):
        return val

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

    Supports both the old 0.14 JSON-LD keys and the new 0.17 keys.
    """
    if not isinstance(meta, dict):
        return {}

    description = meta.get(DCT_DESCRIPTION)

    if description is None:
        description = meta.get("dct:abstract")

    publication_date = meta.get(DCT_ISSUED)

    if publication_date is None:
        publication_date = meta.get("dct:issued")

    last_update = meta.get(DCT_UPDATED)

    if last_update is None:
        last_update = meta.get("dct:updated")

    language = meta.get(DCT_LANGUAGE)

    if language is None:
        language = meta.get("dct:language")

    keywords = meta.get(DCAT_KEYWORD)

    if keywords is None:
        keywords = meta.get("dcat:keyword")

    data_quality = meta.get(DCAT_DATA_QUALITY)

    if data_quality is None:
        data_quality = meta.get("dcat:dataQuality")

    granularity = meta.get(DCAT_GRANULARITY)

    if granularity is None:
        granularity = meta.get("dcat:granularity")

    return {
        "description": description,
        "publication_date": publication_date,
        "last_update": pick_latest_date(last_update),
        "language": language,
        "publisher": safe_publisher(meta),
        "license": extract_licenses(meta),
        "keywords": clean_list(keywords or []),
        "keywords_tg": clean_list(keywords or []),
        "data_quality": data_quality,
        "granularity": granularity,
    }


def transform_raw_dataset(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build the indexed dataset document from a raw SAGE dataset record.

    Supports both the old 0.14 JSON-LD keys and the new 0.17 keys.
    """
    meta = raw.get(EDC_METADATA)

    # Backward compatibility with Federated Catalog 0.14.
    if meta is None:
        meta = raw.get("metadata")

    dataset_id = raw.get(EDC_ID)

    if dataset_id is None:
        dataset_id = raw.get("id") or raw.get("@id")

    url = raw.get(EDC_BASE_URL)

    if url is None:
        url = raw.get("baseUrl")

    version = raw.get(EDC_VERSION)

    if version is None:
        version = raw.get("version")

    title = raw.get(EDC_NAME)

    if title is None:
        title = raw.get("name")

    content_type = raw.get(EDC_CONTENT_TYPE)

    if content_type is None:
        content_type = raw.get("contenttype")

    return {
        "id": dataset_id,
        "type": "dataset",
        "catalogue": extract_catalogue_name(raw.get("catalogue")),
        "participant_id": raw.get("participant_id"),
        "url": url,
        "version": version,
        "title": title,
        "originator": raw.get("originator"),
        **extract_metadata(meta),
        "content_type": content_type,
    }
