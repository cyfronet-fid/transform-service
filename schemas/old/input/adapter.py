# pylint: disable=duplicate-code
"""Raw, input adapter expected schema"""

adapter_input_schema = {
    "id": ["string"],
    "name": ["string"],
    "catalogueId": ["string"],
    "node": ["string"],
    "description": ["string"],
    "linkedResource": ["struct<type:string,id:string>"],
    "tagline": ["string"],
    "logo": ["string"],
    "documentation": ["string"],
    "repository": ["string"],
    "releases": ["array<string>"],
    "programmingLanguage": ["string"],
    "license": ["string"],
    "version": ["string"],
    "changeLog": ["string"],
    "lastUpdate": ["bigint"],
    "admins": ["array<string>"],
}
