# pylint: disable=duplicate-code
"""Deployable Service expected schema after transformations"""

deployable_service_output_schema = {
    "id": "string",
    "pid": "string",
    "slug": "string",
    "title": "string",
    "abbreviation": "string",
    "tagline": "string",
    "description": "string",
    "keywords": "array<string>",
    "keywords_tg": "array<string>",
    "url": "string",
    "node": "string",  # TODO fix in the MP
    "version": "string",
    "license": "string",  # TODO fix in the MP
    "last_update": "date",
    "publication_date": "date",
    "updated_at": "date",
    "synchronized_at": "date",
    "status": "string",
    "resource_organisation": "string",
    "catalogues": "array<string>",
    "scientific_domains": "array<string>",
    "upstream_id": "bigint",
    "creator_names": "array<string>",
    "creator_identifiers": "array<string>",
    "creator_affiliations": "array<string>",
    "creators_searchable": "array<string>",
    "type": "string",
}
