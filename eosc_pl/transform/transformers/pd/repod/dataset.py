import json
from logging import getLogger
from typing import Optional

from pandas import DataFrame, Series, to_datetime

from eosc_pl.settings import Repository, get_config
from eosc_pl.transform.schemas.output import PlDataset
from eosc_pl.transform.utils.consts import (
    AUTHOR_NAMES,
    AUTHOR_NAMES_TG,
    DATASET,
    KEYWORDS,
    KEYWORDS_TG,
    SUBJECTS,
)
from eosc_pl.transform.utils.loader import (
    fetch_detail_data,
    fetch_details_concurrently,
)

from ..base import BaseDataverseTransformer

logger = getLogger(__name__)
conf = get_config(Repository.REPOD)


class RepodDatasetTransformer(BaseDataverseTransformer):
    """Transformer used to transform datasets from RepOD repository"""

    def __init__(self):
        self.type = DATASET.lower()

        super().__init__(self.type, self.cols_to_drop, self.cols_to_rename)

    def cast_columns(self, df: DataFrame) -> DataFrame:
        """Cast columns"""
        return df

    @property
    def cols_to_drop(self) -> str | None:
        """Drop those columns from the dataframe"""
        return None

    @property
    def cols_to_rename(self) -> dict[str, str] | None:
        """Columns to rename. Keys are mapped to the values"""
        return None

    def transform(self, df: DataFrame) -> DataFrame:
        """Apply df transformations to a new df returned by _create_full_df helper function"""
        new_df = self._create_full_df(df)
        new_df["datasource_pids"] = [["eosc.icm.repod"]] * len(new_df)
        new_df["country"] = [["PL"]] * len(new_df)
        new_df["type"] = [self.type] * len(new_df)
        new_df["node"] = "EOSC PL"
        self.serialize(new_df, ["contacts", "publications"])
        return new_df.reindex(sorted(new_df.columns), axis=1)

    def _create_obj_from_initial_data(self, row: Series) -> PlDataset:
        """Helper function transforming a row from the data received from list endpoint to Python objects"""
        if publication_date := row.get("published_at"):
            publication_year = to_datetime(publication_date).year
        else:
            publication_year = None
        global_id = row.get("global_id", "")
        doi_val = global_id.split("doi:")[-1] if global_id else None
        doi = [doi_val] if doi_val else []
        url = [row["url"]] if row.get("url") else []
        title = [row["name"]] if row.get("name") else []

        return PlDataset(
            author_names=row.get("authors"),
            citation=[row.get("citation")] if row.get("citation") else None,
            citation_html=(
                [row.get("citationHtml")] if row.get("citationHtml") else None
            ),
            doi=doi,
            dataverse_id=row.get("identifier_of_dataverse"),
            dataverse_name=row.get("name_of_dataverse"),
            publication_date=publication_date,
            publication_year=publication_year,
            url=url,
            title=title,
            node="EOSC PL",
            country=["PL"],
            datasource_pids=["eosc.icm.repod"],
            type=self.type,
        )

    def _get_affiliation(self, ds_contact: dict) -> Optional[str]:
        if aff := (ds_contact.get("datasetContactAffiliation")):
            return aff.get("value") if isinstance(aff, dict) else str(aff)
        return None

    def _get_contact(self, ds_contact: dict) -> Optional[str]:
        if name := (ds_contact.get("datasetContactName")):
            return name.get("value") if isinstance(name, dict) else str(name)
        return None

    def _get_affiliation_and_contacts(self, ds_contacts: dict) -> tuple:
        if not ds_contacts or "value" not in ds_contacts:
            return None, None
        contact = []
        affiliation = []
        for ds_contact in ds_contacts.get("value", []):
            cont = self._get_contact(ds_contact)
            aff = self._get_affiliation(ds_contact)
            contact.append({"name": cont, "affiliation": aff})
            if aff:
                affiliation.append(aff)
        if not any(contact):
            contact = None
        affiliation = list(set(affiliation)) if any(affiliation) else None
        return contact, affiliation

    def _get_description(self, ds_description: dict) -> Optional[list[str]]:
        if not ds_description or "value" not in ds_description:
            return None
        descriptions = []
        for ds_desc in ds_description.get("value", []):
            if description := ds_desc.get("dsDescriptionValue", {}).get("value"):
                descriptions.append(description)
        return descriptions if descriptions else None

    def _get_publications(self, ds_publications: dict) -> Optional[list[dict]]:
        if not ds_publications or "value" not in ds_publications:
            return None
        publications = []
        for ds_pub in ds_publications.get("value", []):
            pub_dict = {
                "url": ds_pub.get("publicationURL", {}).get("value"),
                "citation": ds_pub.get("publicationCitation", {}).get("value"),
            }
            publications.append(pub_dict)
        return publications if publications else None

    def _get_keywords(self, ds_keywords: dict) -> Optional[list[str]]:
        if not ds_keywords or "value" not in ds_keywords:
            return None
        keywords = []
        for ds_kw in ds_keywords.get("value", []):
            if keyword := ds_kw.get("keywordValue", {}).get("value"):
                keywords.append(keyword)
        return keywords if keywords else None

    def _get_license(self, ds_files: list[dict], doi: str) -> Optional[str]:
        if not ds_files:
            return None
        licences = []
        for file in ds_files:
            if isinstance(file, dict) and file.get("licenseName"):
                licences.append(file["licenseName"])
        licenses = list(set(licences))
        if len(licenses) > 1:
            logger.warning(f"More than 1 licence for {doi}")
        return licenses[0] if licenses else None

    def _create_detail_row_data(
        self, data: Optional[dict], obj: PlDataset
    ) -> Optional[PlDataset]:
        """Function responsible for updating PLDataset with data fetched from detail endpoint.

        Returns None if detail data is missing or inaccessible, so the record is omitted.
        """
        if not data or not isinstance(data, dict) or "datasetVersion" not in data:
            doi_str = obj.doi[0] if (obj.doi and len(obj.doi) > 0) else "unknown"
            logger.warning(
                "Skipping RepOD dataset (DOI: %s): detail data missing or inaccessible",
                doi_str,
            )
            return None

        ds_version = data.get("datasetVersion", {})
        fields = (
            ds_version.get("metadataBlocks", {}).get("citation", {}).get("fields", [])
        )
        fields_dict = {
            field["typeName"]: field
            for field in fields
            if isinstance(field, dict) and "typeName" in field
        }
        contacts, affiliation = self._get_affiliation_and_contacts(
            fields_dict.get("datasetContact")
        )
        keywords = self._get_keywords(fields_dict.get("keyword"))
        record_id = f"repod.{data.get('id')}"

        obj.id = record_id
        obj.affiliation = affiliation
        obj.contacts = contacts
        obj.created_at = ds_version.get("createTime")
        obj.description = self._get_description(fields_dict.get("dsDescription"))
        obj.file_count = len(ds_version.get("files", []))
        obj.keywords = keywords
        persistent_url = data.get("persistentUrl", "")
        doi_suffix = persistent_url.split("doi.org/")[-1] if persistent_url else ""
        obj.license = self._get_license(ds_version.get("files"), doi_suffix)
        obj.major_version = ds_version.get("versionNumber")
        obj.publications = self._get_publications(fields_dict.get("publication"))
        obj.publisher = [data.get("publisher")] if data.get("publisher") else None
        obj.storage_id = data.get("storageIdentifier")
        subjects_data = fields_dict.get("subject", {})
        obj.subjects = (
            subjects_data.get("value")
            if isinstance(subjects_data, dict)
            else subjects_data
        )
        obj.updated_at = ds_version.get("lastUpdateTime")
        obj.version_id = ds_version.get("id")
        obj.version_state = ds_version.get("versionState")
        return obj

    def _create_full_row_data(self, row: Series) -> Optional[PlDataset]:
        """Helper function responsible for calling detail endpoint."""
        main_row_data_obj = self._create_obj_from_initial_data(row)
        if main_row_data_obj.doi and len(main_row_data_obj.doi) > 0:
            detail_raw_data = fetch_detail_data(
                main_row_data_obj.doi[0],
                conf.DATASET_DETAIL_ADDRESS,
                timeout=conf.TIMEOUT_SECONDS,
            )
            return self._create_detail_row_data(detail_raw_data, main_row_data_obj)
        return None

    def _create_full_df(self, list_response: DataFrame) -> DataFrame:
        """Function creating full DataFrame with concurrent fetching of detail records."""
        initial_objs = [
            self._create_obj_from_initial_data(row)
            for _, row in list_response.iterrows()
        ]

        dois_to_fetch = [
            (obj.doi[0] if obj.doi and len(obj.doi) > 0 else "") for obj in initial_objs
        ]

        logger.info(
            "Fetching detail data concurrently for %d RepOD records...",
            len(dois_to_fetch),
        )
        detail_results = fetch_details_concurrently(
            dois_to_fetch,
            conf.DATASET_DETAIL_ADDRESS,
            timeout=conf.TIMEOUT_SECONDS,
            max_workers=16,
        )

        rows = []
        skipped_count = 0
        for obj, detail_data in zip(initial_objs, detail_results):
            full_obj = self._create_detail_row_data(detail_data, obj)
            if full_obj is not None:
                rows.append(full_obj.model_dump())
            else:
                skipped_count += 1

        if skipped_count > 0:
            logger.info(
                "Skipped %d RepOD record(s) due to missing or inaccessible detail data.",
                skipped_count,
            )

        return DataFrame(rows, columns=PlDataset.model_fields.keys())
