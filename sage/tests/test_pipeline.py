from unittest.mock import MagicMock, patch

from sage.pipeline import calculate_checksum, flatten_datasets, main


def test_calculate_checksum_is_deterministic():
    datasets = [
        {"@id": "dataset-2", "name": "Dataset 2"},
        {"@id": "dataset-1", "name": "Dataset 1"},
    ]

    checksum_1 = calculate_checksum(datasets)
    checksum_2 = calculate_checksum(list(reversed(datasets)))

    assert checksum_1 == checksum_2


def test_calculate_checksum_changes_when_dataset_changes():
    datasets = [
        {"@id": "dataset-1", "name": "Dataset 1"},
    ]

    original_checksum = calculate_checksum(datasets)

    datasets[0]["name"] = "Changed Dataset"

    changed_checksum = calculate_checksum(datasets)

    assert original_checksum != changed_checksum


def test_calculate_checksum_changes_when_dataset_is_added():
    datasets = [
        {"@id": "dataset-1"},
    ]

    original_checksum = calculate_checksum(datasets)

    datasets.append({"@id": "dataset-2"})

    changed_checksum = calculate_checksum(datasets)

    assert original_checksum != changed_checksum


def test_calculate_checksum_changes_when_dataset_is_removed():
    datasets = [
        {"@id": "dataset-1"},
        {"@id": "dataset-2"},
    ]

    original_checksum = calculate_checksum(datasets)

    datasets.pop()

    changed_checksum = calculate_checksum(datasets)

    assert original_checksum != changed_checksum


def test_flatten_datasets_handles_single_dataset():
    catalogs = [
        {
            "dspace:participantId": "did:web:test.example",
            "originator": "https://example.com",
            "dcat:dataset": {
                "@id": "dataset-1",
                "@type": "dcat:Dataset",
                "name": "Dataset 1",
            },
        }
    ]

    result = flatten_datasets(catalogs)

    assert len(result) == 1
    assert result[0]["@id"] == "dataset-1"
    assert result[0]["catalogue"] == "did:web:test.example"
    assert result[0]["participant_id"] == "did:web:test.example"
    assert result[0]["originator"] == "https://example.com"


def test_flatten_datasets_handles_multiple_datasets():
    catalogs = [
        {
            "dspace:participantId": "participant-1",
            "originator": "originator-1",
            "dcat:dataset": [
                {"@id": "dataset-1"},
                {"@id": "dataset-2"},
            ],
        }
    ]

    result = flatten_datasets(catalogs)

    assert len(result) == 2
    assert result[0]["@id"] == "dataset-1"
    assert result[1]["@id"] == "dataset-2"

    assert result[0]["participant_id"] == "participant-1"
    assert result[1]["participant_id"] == "participant-1"


def test_flatten_datasets_handles_multiple_catalogs():
    catalogs = [
        {
            "dspace:participantId": "participant-1",
            "dcat:dataset": {
                "@id": "dataset-1",
            },
        },
        {
            "dspace:participantId": "participant-2",
            "dcat:dataset": {
                "@id": "dataset-2",
            },
        },
    ]

    result = flatten_datasets(catalogs)

    assert len(result) == 2

    assert result[0]["@id"] == "dataset-1"
    assert result[0]["participant_id"] == "participant-1"

    assert result[1]["@id"] == "dataset-2"
    assert result[1]["participant_id"] == "participant-2"


def test_flatten_datasets_returns_empty_list_for_invalid_input():
    assert flatten_datasets(None) == []
    assert flatten_datasets({}) == []
    assert flatten_datasets("invalid") == []


def test_flatten_datasets_ignores_invalid_dataset():
    catalogs = [
        {
            "dspace:participantId": "participant-1",
            "dcat:dataset": [
                {"@id": "dataset-1"},
                "invalid-dataset",
                None,
            ],
        }
    ]

    result = flatten_datasets(catalogs)

    assert len(result) == 1
    assert result[0]["@id"] == "dataset-1"


@patch("sage.pipeline.save_checksum")
@patch("sage.pipeline.send_to_solr")
@patch("sage.pipeline.delete_all_from_solr")
@patch("sage.pipeline.get_checksum")
@patch("sage.pipeline.transform_raw_dataset")
@patch("sage.pipeline.AggregatorClient")
def test_main_skips_solr_when_checksum_is_unchanged(
    mock_client_class,
    mock_transform,
    mock_get_checksum,
    mock_delete,
    mock_send,
    mock_save_checksum,
):
    data = [
        {
            "dspace:participantId": "participant-1",
            "dcat:dataset": {
                "@id": "dataset-1",
                "name": "Dataset 1",
            },
        }
    ]

    mock_client = MagicMock()
    mock_client.fetch_catalog.return_value = data
    mock_client_class.return_value = mock_client

    # Calculate the expected checksum for this snapshot
    from sage.pipeline import calculate_checksum, flatten_datasets

    datasets = flatten_datasets(data)
    checksum = calculate_checksum(datasets)

    mock_get_checksum.return_value = checksum

    main()

    mock_client.fetch_catalog.assert_called_once()
    mock_transform.assert_not_called()
    mock_delete.assert_not_called()
    mock_send.assert_not_called()
    mock_save_checksum.assert_not_called()


@patch("sage.pipeline.save_checksum")
@patch("sage.pipeline.send_to_solr")
@patch("sage.pipeline.delete_all_from_solr")
@patch("sage.pipeline.get_checksum")
@patch("sage.pipeline.transform_raw_dataset")
@patch("sage.pipeline.AggregatorClient")
def test_main_rebuilds_solr_when_checksum_changes(
    mock_client_class,
    mock_transform,
    mock_get_checksum,
    mock_delete,
    mock_send,
    mock_save_checksum,
):
    data = [
        {
            "dspace:participantId": "participant-1",
            "dcat:dataset": {
                "@id": "dataset-1",
                "name": "Dataset 1",
            },
        }
    ]

    transformed_dataset = {
        "id": "dataset-1",
        "name": "Dataset 1",
    }

    mock_client = MagicMock()
    mock_client.fetch_catalog.return_value = data
    mock_client_class.return_value = mock_client

    mock_get_checksum.return_value = "old-checksum"
    mock_transform.return_value = transformed_dataset
    mock_delete.return_value = True
    mock_send.return_value = True

    main()

    mock_client.fetch_catalog.assert_called_once()
    mock_transform.assert_called_once()
    mock_delete.assert_called_once()
    mock_send.assert_called_once_with([transformed_dataset])
    mock_save_checksum.assert_called_once()


@patch("sage.pipeline.save_checksum")
@patch("sage.pipeline.send_to_solr")
@patch("sage.pipeline.delete_all_from_solr")
@patch("sage.pipeline.get_checksum")
@patch("sage.pipeline.transform_raw_dataset")
@patch("sage.pipeline.AggregatorClient")
def test_main_does_not_delete_solr_when_transformation_fails(
    mock_client_class,
    mock_transform,
    mock_get_checksum,
    mock_delete,
    mock_send,
    mock_save_checksum,
):
    data = [
        {
            "dspace:participantId": "participant-1",
            "dcat:dataset": {
                "@id": "dataset-1",
            },
        }
    ]

    mock_client = MagicMock()
    mock_client.fetch_catalog.return_value = data
    mock_client_class.return_value = mock_client

    mock_get_checksum.return_value = "old-checksum"

    # Transformation failed
    mock_transform.return_value = None

    main()

    mock_transform.assert_called_once()

    # Most important assertion:
    # Solr must remain untouched.
    mock_delete.assert_not_called()
    mock_send.assert_not_called()
    mock_save_checksum.assert_not_called()


@patch("sage.pipeline.save_checksum")
@patch("sage.pipeline.send_to_solr")
@patch("sage.pipeline.delete_all_from_solr")
@patch("sage.pipeline.get_checksum")
@patch("sage.pipeline.transform_raw_dataset")
@patch("sage.pipeline.AggregatorClient")
def test_main_does_not_index_when_solr_delete_fails(
    mock_client_class,
    mock_transform,
    mock_get_checksum,
    mock_delete,
    mock_send,
    mock_save_checksum,
):
    data = [
        {
            "dspace:participantId": "participant-1",
            "dcat:dataset": {
                "@id": "dataset-1",
            },
        }
    ]

    mock_client = MagicMock()
    mock_client.fetch_catalog.return_value = data
    mock_client_class.return_value = mock_client

    mock_get_checksum.return_value = "old-checksum"
    mock_transform.return_value = {
        "id": "dataset-1",
    }
    mock_delete.return_value = False

    main()

    mock_delete.assert_called_once()
    mock_send.assert_not_called()
    mock_save_checksum.assert_not_called()


@patch("sage.pipeline.save_checksum")
@patch("sage.pipeline.send_to_solr")
@patch("sage.pipeline.delete_all_from_solr")
@patch("sage.pipeline.get_checksum")
@patch("sage.pipeline.transform_raw_dataset")
@patch("sage.pipeline.AggregatorClient")
def test_main_does_not_save_checksum_when_indexing_fails(
    mock_client_class,
    mock_transform,
    mock_get_checksum,
    mock_delete,
    mock_send,
    mock_save_checksum,
):
    data = [
        {
            "dspace:participantId": "participant-1",
            "dcat:dataset": {
                "@id": "dataset-1",
            },
        }
    ]

    mock_client = MagicMock()
    mock_client.fetch_catalog.return_value = data
    mock_client_class.return_value = mock_client

    mock_get_checksum.return_value = "old-checksum"
    mock_transform.return_value = {
        "id": "dataset-1",
    }
    mock_delete.return_value = True
    mock_send.return_value = False

    main()

    mock_delete.assert_called_once()
    mock_send.assert_called_once()

    # Very important:
    # checksum must remain unchanged if indexing failed.
    mock_save_checksum.assert_not_called()


@patch("sage.pipeline.save_checksum")
@patch("sage.pipeline.send_to_solr")
@patch("sage.pipeline.delete_all_from_solr")
@patch("sage.pipeline.get_checksum")
@patch("sage.pipeline.transform_raw_dataset")
@patch("sage.pipeline.AggregatorClient")
def test_main_saves_checksum_only_after_successful_indexing(
    mock_client_class,
    mock_transform,
    mock_get_checksum,
    mock_delete,
    mock_send,
    mock_save_checksum,
):
    data = [
        {
            "dspace:participantId": "participant-1",
            "dcat:dataset": {
                "@id": "dataset-1",
            },
        }
    ]

    mock_client = MagicMock()
    mock_client.fetch_catalog.return_value = data
    mock_client_class.return_value = mock_client

    mock_get_checksum.return_value = "old-checksum"
    mock_transform.return_value = {
        "id": "dataset-1",
    }
    mock_delete.return_value = True
    mock_send.return_value = True

    main()

    mock_delete.assert_called_once()
    mock_send.assert_called_once()
    mock_save_checksum.assert_called_once()


@patch("sage.pipeline.save_checksum")
@patch("sage.pipeline.send_to_solr")
@patch("sage.pipeline.delete_all_from_solr")
@patch("sage.pipeline.get_checksum")
@patch("sage.pipeline.transform_raw_dataset")
@patch("sage.pipeline.AggregatorClient")
def test_main_performs_operations_in_correct_order(
    mock_client_class,
    mock_transform,
    mock_get_checksum,
    mock_delete,
    mock_send,
    mock_save_checksum,
):
    data = [
        {
            "dspace:participantId": "participant-1",
            "dcat:dataset": {
                "@id": "dataset-1",
            },
        }
    ]

    mock_client = MagicMock()
    mock_client.fetch_catalog.return_value = data
    mock_client_class.return_value = mock_client

    mock_get_checksum.return_value = "old-checksum"

    call_order = []

    mock_transform.side_effect = lambda dataset: (
        call_order.append("transform") or {"id": "dataset-1"}
    )

    mock_delete.side_effect = lambda: (call_order.append("delete") or True)

    mock_send.side_effect = lambda docs: (call_order.append("send") or True)

    mock_save_checksum.side_effect = lambda checksum: (
        call_order.append("save_checksum")
    )

    main()

    assert call_order == [
        "transform",
        "delete",
        "send",
        "save_checksum",
    ]


def test_calculate_checksum_ignores_dynamic_policy_id():
    dataset = {
        "@id": "dataset-1",
        "name": "Test dataset",
        "odrl:hasPolicy": {
            "@id": "policy-id-1",
            "@type": "odrl:Offer",
            "odrl:permission": [],
            "odrl:prohibition": [],
            "odrl:obligation": [],
        },
    }

    dataset_with_different_policy_id = {
        "@id": "dataset-1",
        "name": "Test dataset",
        "odrl:hasPolicy": {
            "@id": "policy-id-2",
            "@type": "odrl:Offer",
            "odrl:permission": [],
            "odrl:prohibition": [],
            "odrl:obligation": [],
        },
    }

    assert calculate_checksum([dataset]) == calculate_checksum(
        [dataset_with_different_policy_id]
    )


def test_calculate_checksum_does_not_modify_dataset():
    dataset = {
        "@id": "dataset-1",
        "odrl:hasPolicy": {
            "@id": "policy-id-1",
            "@type": "odrl:Offer",
        },
    }

    calculate_checksum([dataset])

    assert dataset["odrl:hasPolicy"]["@id"] == "policy-id-1"
