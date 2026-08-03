# pylint: disable=line-too-long, logging-fstring-interpolation
"""Transform interoperability guidelines."""

import json
import logging
import re
from html import unescape
from typing import Any

import pandas as pd
from pandas import DataFrame

from app.services.solr.validate.schema.validate import validate_pydantic_data
from app.settings import settings
from schemas.input.guideline import GuidelineInputSchema
from schemas.se.guideline import GuidelineSESchema

logger = logging.getLogger(__name__)


def _list(value: list | None) -> list:
    """Return an empty list for null multi-value fields."""
    return value or []


def _compact(values: list[Any]) -> list[str]:
    """Drop empty values and cast kept values to strings."""
    return [str(value) for value in values if value not in (None, "")]


def _clean_html(value: str | None) -> str:
    """Remove basic HTML tags and HTML entities from a Provider Component string."""
    if not value:
        return ""

    without_tags = re.sub(r"</?[a-zA-Z][^>]*>", "", value)
    return unescape(without_tags).replace("\u00a0", " ").strip()


def _join(values: list[str]) -> str | None:
    """Serialize Solr text fields that are stored as a single string."""
    return ", ".join(values) if values else None


def _creator_name(creator: dict) -> str | None:
    """Build a creator display name from first and last name fields."""
    name = " ".join(
        part
        for part in (
            creator.get("firstName"),
            creator.get("lastName"),
        )
        if part
    )
    return name or None


def _transform_record(record: dict) -> dict:
    """Flatten a validated Provider Component guideline into a Solr document."""
    guideline = GuidelineInputSchema.model_validate(record)
    item = guideline.model_dump()

    resource_type_info = item.get("resourceTypeInfo") or {}
    license_info = item.get("license") or {}

    creators = _list(item.get("creators"))
    author_given_names = _compact([creator.get("firstName") for creator in creators])
    author_family_names = _compact([creator.get("lastName") for creator in creators])
    author_names = _compact([_creator_name(creator) for creator in creators])
    author_names_tg = author_names

    author_names_id = []
    author_affiliations = []
    author_affiliations_id = []
    author_types = []

    for creator in creators:
        for pid in _list(creator.get("PIDs")):
            author_names_id.extend(_compact([pid.get("creatorPID")]))

        for affiliation in _list(creator.get("affiliations")):
            author_affiliations.extend(_compact([affiliation.get("affiliationName")]))
            identifier = affiliation.get("affiliationIdentifier") or {}
            author_affiliations_id.extend(_compact([identifier.get("creatorID")]))
            author_types.extend(_compact([identifier.get("creatorType")]))

    creators_list = []
    for creator in creators:
        first_name = creator.get("firstName")
        last_name = creator.get("lastName")

        author_name_parts = [part for part in (last_name, first_name) if part]
        author_name_formatted = ", ".join(author_name_parts)

        pids = _list(creator.get("PIDs"))
        author_names_id_val = pids[0].get("creatorPID") if pids else None

        affiliations = _list(creator.get("affiliations"))
        author_affiliation_info = None
        if affiliations:
            aff = affiliations[0]
            ident = aff.get("affiliationIdentifier") or {}
            author_affiliation_info = {
                "author_affiliations": aff.get("affiliationName"),
                "author_affiliations_id": ident.get("creatorID"),
            }

        creator_obj = {
            "author_name_type_info": {
                "author_names": author_name_formatted,
                "author_types": "ir_name_type-personal",
            },
            "author_given_names": first_name,
            "author_family_names": last_name,
            "author_names_id": author_names_id_val,
            "author_affiliation_info": author_affiliation_info,
        }
        creators_list.append(creator_obj)

    creators_json = json.dumps(creators_list, ensure_ascii=False)

    related_standards = _list(item.get("relatedStandards"))
    related_standards_id = _compact(
        [standard.get("relatedStandardIdentifier") for standard in related_standards]
    )
    related_standards_uri = _compact(
        [standard.get("relatedStandardURI") for standard in related_standards]
    )

    alternative_pids = _list(item.get("alternativePIDs"))
    alternative_ids = _compact([pid.get("pid") for pid in alternative_pids])
    alternative_id_schemes = _compact(
        [pid.get("pidSchema") for pid in alternative_pids]
    )

    publication_date = item.get("publishingDate")
    publication_year = publication_date.year if publication_date else None
    publication_date_value = publication_date.isoformat() if publication_date else None
    resource_owner = item.get("resourceOwner")
    provider = record.get("provider")
    provider_id = record.get("providerId")
    node = record.get("node") or item.get("nodePID")

    return {
        "alternative_id_schemes": alternative_id_schemes,
        "alternative_ids": _join(alternative_ids),
        "author_affiliations": author_affiliations,
        "author_affiliations_id": author_affiliations_id,
        "author_family_names": author_family_names,
        "author_given_names": author_given_names,
        "author_names": author_names,
        "author_names_id": author_names_id,
        "author_names_tg": author_names_tg,
        "author_types": author_types,
        "catalogue": item.get("catalogue", None),
        "catalogues": [item.get("catalogue", None)],
        "creators": creators_json,
        "description": _compact([_clean_html(item.get("description"))]),
        "id": item["id"],
        "license": license_info.get("licenseName"),
        "license_url": license_info.get("licenseURL"),
        "node": node,
        "provider": provider,
        "providerId": provider_id,
        "providers": [provider],
        "publication_date": publication_date_value,
        "publication_year": publication_year,
        "public_contacts": _list(item.get("publicContacts")),
        "related_standards_id": related_standards_id,
        "related_standards_uri": related_standards_uri,
        "resource_owner": resource_owner,
        "title": _compact([item.get("name")]),
        "type": settings.GUIDELINE,
        "type_general": _compact([resource_type_info.get("resourceTypeGeneral")]),
        "type_info": _compact([resource_type_info.get("resourceType")]),
    }


def transform_guidelines(data: dict | list[dict]) -> DataFrame:
    """Transform Provider Component interoperability records into Solr documents."""
    records = data if isinstance(data, list) else [data]

    validate_pydantic_data(records, GuidelineInputSchema, settings.GUIDELINE, "input")
    transformed = [_transform_record(record) for record in records]
    validate_pydantic_data(transformed, GuidelineSESchema, settings.GUIDELINE, "output")

    return pd.DataFrame(transformed)
