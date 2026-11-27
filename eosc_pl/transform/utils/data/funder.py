"""Harvest funder as arr[str] from 'funding'"""

from pandas import DataFrame

from eosc_pl.mappings.funder import funder_mapping


def map_funder(funder: str) -> str:
    """Map funder if necessary"""
    if funder.lower() in funder_mapping.keys():
        return funder_mapping[funder.lower()]
    return funder


def harvest_funder(df: DataFrame) -> list[list[str]]:
    """Create funder column from Rodbuk's 'funding' nested field"""
    if "metadataBlocks" not in df.columns:
        return [[] for _ in range(len(df))]

    funder_column = []
    for row in df["metadataBlocks"]:
        if (
            not isinstance(row, dict)
            or "citation" not in row
            or "fields" not in row["citation"]
        ):
            funder_column.append([])
            continue
        for field in row["citation"]["fields"]:
            raw_funder_row = []
            if field.get("typeName") == "funding":  # funder property
                for val in field.get("value", []):
                    if isinstance(val, dict) and val.get("fundingAgency"):
                        raw_funder_row.append(map_funder(val["fundingAgency"]["value"]))
                funder_column.append(
                    list(set(raw_funder_row))
                )  # there are duplicated values
                break
        else:
            funder_column.append([])

    return funder_column
