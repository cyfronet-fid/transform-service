"""
Tests for extract_data_from_frame function
"""

from unittest.mock import patch

import pytest

from app.transform.live_update.process_message import extract_data_from_frame


@pytest.fixture
def sample_adapter_message():
    """Sample adapter update message"""
    return {
        "active": True,
        "suspended": False,
        "status": "approved adapter",
        "adapter": {
            "id": "21.15133/ZR7MTi",
            "name": "TestAdapter",
            "catalogueId": "eosc",
            "node": "node-cnb_csic",
            "description": "<p>test</p>",
        },
    }


@pytest.fixture
def sample_training_message():
    """Sample training resource update message"""
    return {
        "active": True,
        "suspended": False,
        "status": "approved resource",
        "trainingResource": {
            "id": "21.15133/ABC123",
            "title": "Test Training",
        },
    }


@pytest.fixture
def sample_guideline_message():
    """Sample interoperability guideline message"""
    return {
        "active": True,
        "suspended": False,
        "status": "approved interoperability record",
        "interoperabilityRecord": {
            "id": "21.15133/XYZ789",
            "name": "Test Guideline",
        },
    }


class TestExtractDataFromFrame:
    """Tests for data extraction from message frames"""

    def test_extract_adapter_data(self, sample_adapter_message):
        """Test extracting adapter data from frame"""
        with patch("app.settings.settings.ADAPTER", "adapters"):
            collection, data, data_id = extract_data_from_frame(
                "adapter", sample_adapter_message
            )
            assert collection == "adapters"
            assert data[0]["id"] == "21.15133/ZR7MTi"
            assert data_id == "21.15133/ZR7MTi"

    def test_extract_training_data(self, sample_training_message):
        """Test extracting training resource data from frame"""
        with patch("app.settings.settings.TRAINING", "trainings"):
            collection, data, data_id = extract_data_from_frame(
                "training_resource", sample_training_message
            )
            assert collection == "trainings"
            assert data["id"] == "21.15133/ABC123"
            assert data_id == "21.15133/ABC123"

    def test_extract_guideline_data(self, sample_guideline_message):
        """Test extracting interoperability record data from frame"""
        with patch("app.settings.settings.GUIDELINE", "guidelines"):
            collection, data, data_id = extract_data_from_frame(
                "interoperability_record", sample_guideline_message
            )
            assert collection == "guidelines"
            assert data[0]["id"] == "21.15133/XYZ789"
            assert data_id == "21.15133/XYZ789"

    def test_extract_unknown_collection(self, sample_adapter_message):
        """Test extracting data from unknown collection type"""
        collection, data, data_id = extract_data_from_frame(
            "unknown_type", sample_adapter_message
        )
        assert collection == "unknown_type"
        assert data is None
        assert data_id is None

    def test_extract_adapter_data_structure(self, sample_adapter_message):
        """Test that adapter data is wrapped in a list"""
        with patch("app.settings.settings.ADAPTER", "adapters"):
            collection, data, data_id = extract_data_from_frame(
                "adapter", sample_adapter_message
            )
            assert isinstance(data, list)
            assert len(data) == 1

    def test_extract_training_data_structure(self, sample_training_message):
        """Test that training data is not wrapped in a list"""
        with patch("app.settings.settings.TRAINING", "trainings"):
            collection, data, data_id = extract_data_from_frame(
                "training_resource", sample_training_message
            )
            assert isinstance(data, dict)
            assert "id" in data

    def test_extract_guideline_data_structure(self, sample_guideline_message):
        """Test that guideline data is wrapped in a list"""
        with patch("app.settings.settings.GUIDELINE", "guidelines"):
            collection, data, data_id = extract_data_from_frame(
                "interoperability_record", sample_guideline_message
            )
            assert isinstance(data, list)
            assert len(data) == 1
