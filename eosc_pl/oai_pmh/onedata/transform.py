"""Transformations for OneData OAI-PMH metadata records."""


def transform_metadata_dc(metadata_dc: dict) -> dict:
    """
    Apply transformations to metadata_dc dict.
    - identifier -> url
    - creator -> author_names
    - date -> publication_date
    - add datasource_pids = ["eosc.cyfronet.onedata"]
    - add id = first identifier string
    """
    if not metadata_dc:
        return {}

    transformed = {}
    identifier_values = None

    for key, value in metadata_dc.items():
        new_key = key

        if key == "identifier":
            new_key = "url"
            identifier_values = value
        elif key == "creator":
            new_key = "author_names"
        elif key == "date":
            new_key = "publication_date"

        transformed[new_key] = value

    # Derive 'id' from the first identifier (if exists)
    if identifier_values:
        if isinstance(identifier_values, list) and len(identifier_values) > 0:
            transformed["id"] = identifier_values[0]
        elif isinstance(identifier_values, str):
            transformed["id"] = identifier_values
        else:
            transformed["id"] = None
    else:
        transformed["id"] = None

    # Add static source tag
    transformed["datasource_pids"] = ["eosc.cyfronet.onedata"]
    transformed["type"] = ["dataset"]

    return transformed
