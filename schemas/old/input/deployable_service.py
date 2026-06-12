# pylint: disable=duplicate-code
"""Deployable expected input schema"""

deployable_service_input_schema = {
    "abbreviation": ["string"],
    "catalogue": ["string"],
    "creators": [
        "array<struct<givenName:string,familyName:string,nameIdentifier:string,creatorNameTypeInfo:struct<nameType:string,creatorName:string>,creatorAffiliationInfo:struct<affiliation:string,affiliationIdentifier:string>>>"
    ],
    "description": ["string"],
    "id": ["bigint"],
    "last_update": ["string"],
    "license_name": ["string"],
    "license_url": ["string"],
    "name": ["string"],
    "node": ["string"],
    "pid": ["string"],
    "publication_date": ["string"],
    "publishing_date": ["string"],
    "public_contact_emails": ["array<string>"],
    "resource_organisation": ["string"],
    "resource_type": ["string"],
    "scientific_domains": ["array<string>"],
    "slug": ["string"],
    "status": ["string"],
    "synchronized_at": ["string"],
    "tag_list": ["array<string>"],
    "tagline": ["string"],
    "updated_at": ["string"],
    "upstream_id": ["bigint"],
    "url": ["string"],
    "urls": ["array<string>"],
    "version": ["string"],
}
