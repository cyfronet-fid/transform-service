from unittest.mock import MagicMock, patch

import requests

from sage.sender import (
    chunk_iterable,
    delete_all_from_solr,
    send_batch_to_solr,
    send_to_solr,
)


def test_chunk_iterable():
    data = list(range(5))

    result = list(chunk_iterable(data, 2))

    assert result == [
        [0, 1],
        [2, 3],
        [4],
    ]


def test_chunk_iterable_empty():
    assert list(chunk_iterable([], 10)) == []


@patch("sage.sender.requests.post")
def test_delete_all_from_solr(mock_post):
    response = MagicMock()
    response.raise_for_status.return_value = None

    mock_post.return_value = response

    result = delete_all_from_solr()

    assert result is True

    mock_post.assert_called_once()

    _, kwargs = mock_post.call_args

    assert kwargs["json"] == {
        "delete": {
            "query": "*:*",
        }
    }


@patch("sage.sender.requests.post")
def test_delete_all_from_solr_returns_false_on_http_error(mock_post):
    response = MagicMock()
    response.raise_for_status.side_effect = requests.HTTPError(
        "HTTP error"
    )

    mock_post.return_value = response

    result = delete_all_from_solr()

    assert result is False


@patch("sage.sender.requests.post")
def test_send_batch_to_solr(mock_post):
    response = MagicMock()
    response.raise_for_status.return_value = None

    mock_post.return_value = response

    docs = [
        {"id": "1"},
        {"id": "2"},
    ]

    result = send_batch_to_solr(docs)

    assert result is True

    mock_post.assert_called_once()

    _, kwargs = mock_post.call_args

    assert kwargs["json"] == docs


def test_send_batch_to_solr_empty_batch():
    assert send_batch_to_solr([]) is True


@patch("sage.sender.send_batch_to_solr")
def test_send_to_solr_sends_batches(mock_send_batch):
    mock_send_batch.return_value = True

    docs = [{"id": str(i)} for i in range(450)]

    result = send_to_solr(docs)

    assert result is True
    assert mock_send_batch.call_count == 3

    calls = mock_send_batch.call_args_list

    assert len(calls[0].args[0]) == 200
    assert len(calls[1].args[0]) == 200
    assert len(calls[2].args[0]) == 50


@patch("sage.sender.send_batch_to_solr")
def test_send_to_solr_returns_false_if_any_batch_fails(mock_send_batch):
    mock_send_batch.side_effect = [
        True,
        False,
        True,
    ]

    docs = [{"id": str(i)} for i in range(450)]

    result = send_to_solr(docs)

    assert result is False


@patch("sage.sender.send_batch_to_solr")
def test_send_to_solr_returns_false_for_empty_documents(mock_send_batch):
    result = send_to_solr([])

    assert result is False
    mock_send_batch.assert_not_called()
