"""Harvest document_type as arr[str] from 'kindOfDataMain'"""

from pandas import DataFrame

from eosc_pl.mappings.document_type import document_type_mapping


def map_document_type(document_type: str) -> str:
    """Map document_type if necessary"""
    if document_type.lower() in document_type_mapping.keys():
        return document_type_mapping[document_type.lower()]
    return document_type


def harvest_document_type(df: DataFrame) -> list[list[str]]:
    """Create document_type column from Rodbuk's 'kindOfDataMain' nested field"""
    if "metadataBlocks" not in df.columns:
        return [[] for _ in range(len(df))]

    document_type_column = []
    for row in df["metadataBlocks"]:
        if (
            not isinstance(row, dict)
            or "citation" not in row
            or "fields" not in row["citation"]
        ):
            document_type_column.append([])
            continue
        for field in row["citation"]["fields"]:
            raw_document_type_row = []
            if field.get("typeName") == "kindOfDataMain":  # document_type property
                for val in field.get("value", []):
                    if isinstance(val, dict) and val.get("kindOfData"):
                        raw_document_type_row.append(
                            map_document_type(val["kindOfData"]["value"])
                        )
                document_type_column.append(list(set(raw_document_type_row)))
                break
        else:
            document_type_column.append([])

    return document_type_column
