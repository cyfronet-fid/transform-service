import json
from logging import getLogger
from typing import Optional

from pandas import DataFrame, Series, to_datetime
from settings import get_config
from transform.schemas.output import PlDataset
from transform.utils.consts import (
    AUTHOR_NAMES,
    AUTHOR_NAMES_TG,
    DATASET,
    KEYWORDS,
    KEYWORDS_TG,
    SUBJECTS,
    Repository,
)
from transform.utils.loader import fetch_detail_data

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
        pass

    @property
    def cols_to_rename(self) -> dict[str, str] | None:
        """Columns to rename. Keys are mapped to the values"""
        pass

    def transform(self, df: DataFrame) -> DataFrame:
        """Apply df transformations to a new df returned by _create_full_df helper function"""
        new_df = self._create_full_df(df)
        df["datasource_pids"] = [["eosc.icm.repod"]] * len(new_df)
        df["country"] = [["PL"]] * len(new_df)
        df["type"] = [self.type] * len(new_df)
        self.serialize(new_df, ["contacts", "publications"])
        return new_df.reindex(sorted(new_df.columns), axis=1)

    def _create_obj_from_initial_data(self, row: Series) -> PlDataset:
        """Helper function transforming a row from the data received from list endpoint to Python objects"""
        if publication_date := row.get("published_at"):
            publication_year = to_datetime(publication_date).year
        else:
            publication_year = None
        return PlDataset(
            author_names=row.get("authors"),
            citation=[row.get("citation")],
            citation_html=[row.get("citationHtml")],
            doi=[row["global_id"].split("doi:")[-1]],
            dataverse_id=row.get("identifier_of_dataverse"),
            dataverse_name=row.get("name_of_dataverse"),
            publication_date=publication_date,
            publication_year=publication_year,
            url=[row["url"]],
            title=[row["name"]],
        )

    def _get_affiliation(self, ds_contact: dict) -> Optional[str]:
        if aff := (ds_contact.get("datasetContactAffiliation")):
            return aff["value"]
        return None

    def _get_contact(self, ds_contact: dict) -> Optional[str]:
        if name := (ds_contact.get("datasetContactName")):
            return name["value"]
        return None

    def _get_affiliation_and_contacts(self, ds_contacts: dict) -> tuple:
        if not ds_contacts:
            return None, None
        contact = []
        affiliation = []
        for ds_contact in ds_contacts["value"]:
            cont = self._get_contact(ds_contact)
            aff = self._get_affiliation(ds_contact)
            contact.append(json.dumps({"name": cont, "affiliation": aff}))
            affiliation.append(aff)
        if not any(contact):
            contact = None
        affiliation = list(set(affiliation)) if any(affiliation) else None
        return contact, affiliation

    def _get_description(self, ds_description: dict) -> Optional[list[str]]:
        if not ds_description:
            return None
        descriptions = []
        for ds_desc in ds_description["value"]:
            if description := ds_desc.get("dsDescriptionValue", {}).get("value"):
                descriptions.append(description)
        return descriptions

    def _get_publications(self, ds_publications: dict) -> Optional[list[str]]:
        if not ds_publications:
            return
        publications = []
        for ds_pub in ds_publications["value"]:
            pub_dict = {
                "url": ds_pub.get("publicationURL", {}).get("value"),
                "citation": ds_pub.get("publicationCitation", {}).get("value"),
            }
            publications.append(json.dumps(pub_dict))
        return publications

    def _get_keywords(self, ds_keywords: dict) -> Optional[list[str]]:
        if not ds_keywords:
            return
        keywords = []
        for ds_kw in ds_keywords["value"]:
            if keyword := ds_kw.get("keywordValue", {}).get("value"):
                keywords.append(keyword)
        return keywords

    def _get_license(self, ds_files: list[dict], doi: str) -> str:
        if not ds_files:
            return
        licences = []
        for file in ds_files:
            licences.append(file.get("licenseName"))
        licenses = list(set(licences))
        if len(licenses) > 1:
            logger.warning(
                f"More than 1 licence for {doi}"
            )  # TODO several records with > 1 licence
        return licenses[0]

    def _create_detail_row_data(self, data: dict, obj: PlDataset) -> PlDataset:
        """Function responsible of adding to a PLDataset object representing a single
        record containing initially basic data present in list endpoint
        properties that has to be fetched by a call to detail endpoint.
        Args:
            data: dict containing data fetched from the detail endpoint
            obj: PLDataset object containg basic infomation fetched from the list endpoint
        Returns:
            Full PLDataset object containing all properties
        """
        ds_version = data["datasetVersion"]
        fields_dict = {
            field["typeName"]: field
            for field in ds_version["metadataBlocks"]["citation"]["fields"]
        }
        contacts, affiliation = self._get_affiliation_and_contacts(
            fields_dict.get("datasetContact")
        )
        keywords = self._get_keywords(fields_dict.get("keyword"))
        record_id = f"repod.{data['id']}"

        obj.id = record_id
        obj.affiliation = affiliation
        obj.contacts = contacts
        obj.created_at = ds_version.get("createTime")
        obj.description = self._get_description(fields_dict.get("dsDescription"))
        obj.file_count = len(ds_version.get("files", []))
        obj.keywords = keywords
        # obj.keywords_tg = keywords # TODO out
        obj.license = self._get_license(
            ds_version.get("files"), data["persistentUrl"].split("doi.org/")[-1]
        )
        obj.major_version = ds_version.get("versionNumber")
        obj.publications = self._get_publications(fields_dict.get("publication"))
        obj.publisher = [data.get("publisher")]
        obj.storage_id = data.get("storageIdentifier")
        obj.subjects = fields_dict.get("subject", {}).get("value")
        obj.updated_at = ds_version.get("lastUpdateTime")
        obj.version_id = ds_version.get("id")
        obj.version_state = ds_version.get("versionState")
        return obj

    def _create_full_row_data(self, row: Series) -> PlDataset:
        """Helper function responsible of calling the function fetching data
        from detail endpoint
        """
        main_row_data_obj = self._create_obj_from_initial_data(row)
        detail_raw_data = fetch_detail_data(
            main_row_data_obj.doi[0], conf.DATASET_DETAIL_ADDRESS
        )
        return self._create_detail_row_data(detail_raw_data, main_row_data_obj)

    def _create_full_df(self, list_response) -> DataFrame:
        """Function interating through the list response i.e. Pandas Dataframe
        containing basic information about record and creating a new Dataframe
        with those information updated by results of individual calls to detail endpoint
        Args:
            list_response: Dataframe resulting from call to list endpoint
        Returns:
            new Dataframe containing results of individual calls to detail endpoint
        """
        df = DataFrame(columns=PlDataset.model_fields.keys())
        for index, row in list_response.iterrows():
            full_row_data_obj = self._create_full_row_data(row)
            df.loc[index] = full_row_data_obj.model_dump()
        return df
