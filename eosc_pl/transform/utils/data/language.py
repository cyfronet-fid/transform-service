"""Harvest language as arr[str] from 'languageMain'"""

from pandas import DataFrame


def harvest_language(df: DataFrame) -> list[list[str]]:
    """Create language column from Rodbuk's 'languageMain' nested field"""
    if "metadataBlocks" not in df.columns:
        return [[] for _ in range(len(df))]

    language_column = []
    for row in df["metadataBlocks"]:
        if (
            not isinstance(row, dict)
            or "citation" not in row
            or "fields" not in row["citation"]
        ):
            language_column.append([])
            continue
        for field in row["citation"]["fields"]:
            raw_language_row = []
            if field.get("typeName") == "languageMain":  # language property
                for val in field.get("value", []):
                    if isinstance(val, dict) and val.get("language"):
                        raw_language_row.append(val["language"]["value"])
                language_column.append(list(set(raw_language_row)))
                break
        else:
            language_column.append([])

    return language_column
