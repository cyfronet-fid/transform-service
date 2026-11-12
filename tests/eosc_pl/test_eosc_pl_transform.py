import pandas as pd

from eosc_pl.ecudo.pipeline import transform_and_validate as ecudo_transform
from eosc_pl.ega.pipeline import transform_to_ega_output
from eosc_pl.oai_pmh.onedata.transform import transform_metadata_dc
from eosc_pl.transform.transformers.pd.repod.dataset import RepodDatasetTransformer
from eosc_pl.transform.transformers.pd.rodbuk.dataset import RodbukDatasetTransformer


def test_rodbuk_transformer_from_file():
    df = pd.DataFrame([
        {
            "name": "Test name",
            "type": "dataset",
            "url": "https://doi.org/10.17632/MPFYK7JCZ9.2",
            "global_id": "doi:10.17632/MPFYK7JCZ9.2",
            "description": "Description",
            "published_at": "2026-02-04T01:00:05Z",
            "publisher": "Faculty of Geology, Geophysics, and Environmental Protection",
            "citationHtml": "some citation",
            "identifier_of_dataverse": "wggios",
            "name_of_dataverse": "Faculty of Geology, Geophysics, and Environmental Protection",
            "citation": "some citation",
            "publicationStatuses": [
                "Published"
            ],
            "storageIdentifier": "file://10.17632/mpfyk7jcz9.2",
            "keywords": [
                "nitrogen and phosphorus loads",
                "chlorophyll ‘a’ concentrations",
                "catchment",
                "SWAT model"
            ],
            "subjects": [],
            "fileCount": 0,
            "versionId": 4258,
            "versionState": "RELEASED",
            "majorVersion": 1,
            "createdAt": "2024-05-11T23:03:24Z",
            "updatedAt": "2024-05-11T23:03:24Z",
            "contacts": [],
            "publications": [
                {
                    "citation": "The deposited dataset is the source material for the related publication"
                },
                {
                    "citation": "The deposited dataset is the source material for the related publication"
                }
            ],
            "authors": []
        },
    ])

    transformer = RodbukDatasetTransformer()
    result = transformer(df)

    assert "node" in result.columns
    assert (result["node"][0] == "EOSC PL")
    assert result["country"].tolist() == [["PL"]]
    assert (result["type"][0] == "dataset")
    assert "metadataBlocks" not in result.columns
    assert "author_names_tg" in result.columns


def test_repod_transformer_from_file(monkeypatch):
    df = pd.DataFrame([
        {
            "name": "repod test",
            "type": "dataset",
            "url": "https://doi.org/10.18150/LII8AM",
            "citationHtml": "",
            "citation": "",
            "authors": [],
            "global_id": "doi:10.18150/LII8AM",
            "published_at": "2024-03-15T19:08:41Z",
            "identifier_of_dataverse": "repod",
            "name_of_dataverse": "RepOD"
        }
    ])

    mock_detail = {
        "id": 9999,
        "persistentUrl": "https://doi.org/10.18150/TEST",
        "datasetVersion": {
            "createTime": "2024-01-01",
            "metadataBlocks": {
                "citation": {
                    "fields": [
                        {"typeName": "dsDescription", "value": [{"dsDescriptionValue": {"value": "Test description"}}]}
                    ]
                }
            },
            "files": [],
        },
    }
    monkeypatch.setattr(
        "eosc_pl.transform.transformers.pd.repod.dataset.fetch_details_concurrently",
        lambda dois, url, timeout, max_workers: [mock_detail, mock_detail],
    )

    transformer = RepodDatasetTransformer()
    result = transformer(df)

    assert "node" in result.columns
    assert (result["node"][0] == "EOSC PL")
    assert result["country"][0] == ["PL"]
    assert (result["type"][0] == "dataset")
    assert result["datasource_pids"][0] == ["eosc.icm.repod"]
    assert "author_names_tg" in result.columns


def test_repod_skips_record_on_failed_detail(monkeypatch):
    df = pd.DataFrame([
        {
            "name": "repod test",
            "type": "dataset",
            "url": "https://doi.org/10.18150/LII8AM",
            "citationHtml": "",
            "citation": "",
            "authors": [],
            "global_id": "doi:10.18150/LII8AM",
            "published_at": "2024-03-15T19:08:41Z",
            "identifier_of_dataverse": "repod",
            "name_of_dataverse": "RepOD"
        }
    ])

    mock_detail = {
        "id": 12345,
        "persistentUrl": "https://doi.org/10.18150/LII8AM",
        "datasetVersion": {
            "createTime": "2024-01-01",
            "metadataBlocks": {
                "citation": {
                    "fields": [
                        {"typeName": "dsDescription", "value": [{"dsDescriptionValue": {"value": "Test desc"}}]}
                    ]
                }
            },
            "files": [],
        },
    }

    # Simulate: 1st record succeeds, 2nd record fails (e.g. 403 Forbidden -> None)
    monkeypatch.setattr(
        "eosc_pl.transform.transformers.pd.repod.dataset.fetch_details_concurrently",
        lambda dois, url, timeout, max_workers: [mock_detail, None],
    )

    transformer = RepodDatasetTransformer()
    result = transformer(df)

    assert len(result) == 1
    assert result.iloc[0]["id"] == "repod.12345"
    assert result.iloc[0]["node"] == "EOSC PL"



def test_ecudo_transform_and_node():
    sample_records = [
        {
            "identifier": "ecudo-123",
            "title": "Oceanographic Sample Data",
            "description": "Temperature and salinity measurements",
            "issued": "2024-01-15",
            "modified": "2024-02-01",
            "keywords": "ocean, temperature, salinity",
            "publisher": {"name": "IOPAN"},
            "distribution": [{"downloadURL": "https://ecudo.pl/download/123"}],
        }
    ]
    transformed = ecudo_transform(sample_records)
    assert len(transformed) == 1
    record = transformed[0]
    assert record["id"] == "ecudo-123"
    assert record["node"] == "EOSC PL"
    assert record["datasource_pids"] == ["eosc.gdansk_tech.ecudo"]
    assert record["keywords"] == ["ocean", "temperature", "salinity"]
    assert record["publication_year"] == "2024"


def test_ega_transform_and_node():
    raw_ega = {
        "accession_id": "EGAD0000000001",
        "title": "Sample Genomic Study",
        "description": "Genomic sequence data",
        "access_type": "controlled",
        "released_date": "2023-05-10",
        "dataset_types": ["Whole Genome Sequencing"],
        "num_samples": 50,
        "is_in_beacon": True,
        "is_released": True,
        "is_deprecated": False,
        "policy_accession_id": "EGAP0000000001",
    }
    ega_out = transform_to_ega_output(raw_ega)
    assert ega_out.node == "EOSC PL"
    assert ega_out.datasource_pids == ["eosc.ega.ega"]
    assert ega_out.id == "EGAD0000000001"
    assert ega_out.type == "dataset"


def test_onedata_transform_and_node():
    raw_dc = {
        "identifier": ["https://data.eosc.pl/dataset/999"],
        "creator": ["Dr. Kowalski"],
        "date": "2024-03-01",
        "title": "OneData Sensor Metrics",
    }
    res = transform_metadata_dc(raw_dc)
    assert res["node"] == "EOSC PL"
    assert res["datasource_pids"] == ["eosc.cyfronet.onedata"]
    assert res["id"] == "https://data.eosc.pl/dataset/999"
    assert res["type"] == ["dataset"]
