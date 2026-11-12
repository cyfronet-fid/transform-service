"""Harvest affiliation as arr[str] from 'contacts'"""

from pandas import DataFrame


def harvest_affiliation(df: DataFrame) -> list[list[str]]:
    """Create affiliation column from Rodbuk's 'contacts' nested field"""
    # there is some random nan of type float in the data
    if "contacts" not in df.columns:
        return [[] for _ in range(len(df))]

    return [
        (
            list(
                {
                    contact["affiliation"]
                    for contact in contacts
                    if isinstance(contact, dict) and contact.get("affiliation")
                }
            )
            if isinstance(contacts, list)
            else []
        )
        for contacts in df["contacts"]
    ]
