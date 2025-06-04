import pytest
import requests
import requests_mock

from app.services.mp_pc.node import (
    get_node_id_name_mapping,
    reset_node_id_name_mapping_cache,
)


@pytest.fixture(autouse=True)
def reset_cache_before_test():
    """Automatically reset the mapping cache before each test."""
    reset_node_id_name_mapping_cache()


# Full valid response with all fields for 3 nodes
VALID_RESPONSE = [
    {
        "id": "node-cessda",
        "name": "CESSDA",
        "description": "CESSDA",
        "parentId": None,
        "type": "Node",
        "extras": {},
    },
    {
        "id": "node-cnb_csic",
        "name": "CNB-CSIC",
        "description": "CNB-CSIC",
        "parentId": None,
        "type": "Node",
        "extras": {},
    },
    {
        "id": "node-egi",
        "name": "EGI",
        "description": "EGI",
        "parentId": None,
        "type": "Node",
        "extras": {},
    },
]

MALFORMED_RESPONSE = [
    {"name": "OnlyName"},  # Missing "id"
    {"id": "only-id"},  # Missing "name"
    {},  # Completely empty
]


def test_successful_mapping():
    """Test that valid response returns correct mapping."""
    url = "https://test.example.com/nodes"
    with requests_mock.Mocker() as m:
        m.get(url, json=VALID_RESPONSE)
        result = get_node_id_name_mapping(url)

    assert result == {
        "node-cessda": "CESSDA",
        "node-cnb_csic": "CNB-CSIC",
        "node-egi": "EGI",
    }


def test_singleton_behavior():
    """Test that second call returns cached data without HTTP request."""
    url = "https://test.example.com/nodes"
    with requests_mock.Mocker() as m:
        m.get(url, json=VALID_RESPONSE)

        first = get_node_id_name_mapping(url)
        assert m.called
        assert m.call_count == 1

        m.reset_mock()
        second = get_node_id_name_mapping(url)
        assert second == first
        assert not m.called


def test_empty_response_returns_none():
    """Test that an empty list response returns None."""
    url = "https://test.example.com/nodes"
    with requests_mock.Mocker() as m:
        m.get(url, json=[])
        result = get_node_id_name_mapping(url)

    assert result is None


def test_malformed_response_returns_none():
    """Test that a malformed response returns None."""
    url = "https://test.example.com/nodes"
    with requests_mock.Mocker() as m:
        m.get(url, json=MALFORMED_RESPONSE)
        result = get_node_id_name_mapping(url)

    assert result is None


def test_invalid_json_returns_none():
    """Test that a non-JSON response returns None."""
    url = "https://test.example.com/nodes"
    with requests_mock.Mocker() as m:
        m.get(url, text="this is not json", status_code=200)
        result = get_node_id_name_mapping(url)

    assert result is None


def test_http_500_returns_none():
    """Test that an HTTP 500 response returns None."""
    url = "https://test.example.com/nodes"
    with requests_mock.Mocker() as m:
        m.get(url, status_code=500)
        result = get_node_id_name_mapping(url)

    assert result is None


def test_connection_error(monkeypatch):
    """Test that a requests.ConnectionError returns None."""

    def mock_get(*args, **kwargs):
        raise requests.ConnectionError("Connection failed")

    monkeypatch.setattr(requests, "get", mock_get)

    url = "https://test.example.com/nodes"
    result = get_node_id_name_mapping(url)

    assert result is None
