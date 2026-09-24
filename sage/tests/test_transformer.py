from sage.transfomer import transform_raw_dataset


def test_transform_raw_dataset_supports_v017_jsonld_format():
    raw = {
        "@id": "dataset-1",
        "@type": "http://www.w3.org/ns/dcat#Dataset",
        "edc:id": "dataset-1",
        "edc:name": "Dataset 1",
        "edc:version": "1.0",
        "edc:contenttype": "application/json",
        "edc:baseUrl": "https://example.com/dataset",
        "edc:metadata": {
            "http://purl.org/dc/terms/description": ("Dataset description"),
            "http://purl.org/dc/terms/issued": "2025-01-01",
            "http://www.w3.org/ns/dcat#keyword": [
                "keyword-1",
                "keyword-2",
            ],
        },
        "participant_id": "did:web:test.example",
        "catalogue": "did:web:test.example",
        "originator": "https://connector.example",
    }

    result = transform_raw_dataset(raw)

    assert result["id"] == "dataset-1"
    assert result["title"] == "Dataset 1"
    assert result["version"] == "1.0"
    assert result["url"] == "https://example.com/dataset"
    assert result["content_type"] == "application/json"
    assert result["participant_id"] == "did:web:test.example"
    assert result["originator"] == "https://connector.example"

    assert result["description"] == "Dataset description"
    assert result["publication_date"] == "2025-01-01"
    assert result["keywords"] == [
        "keyword-1",
        "keyword-2",
    ]
