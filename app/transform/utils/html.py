"""Clean HTML in resource descriptions."""

import re
from html import unescape


def clean_html(value: str | list[str] | None) -> str | list[str] | None:
    """Decode nested entities and remove tags, preserving nulls and lists."""
    if value is None:
        return None
    if isinstance(value, list):
        return [clean_html(item) for item in value]

    decoded = unescape(value)
    while decoded != value:
        value = decoded
        decoded = unescape(value)

    without_tags = re.sub(r"</?[a-zA-Z][^>]*>", "", decoded)
    return without_tags.replace("\u00a0", " ").strip()
