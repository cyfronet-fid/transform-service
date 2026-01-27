"""
Tests for AMS message processing (_process_ams_message)
"""

import json
from unittest.mock import patch

import pytest

from app.transform.live_update.process_message import _process_ams_message


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
        },
    }


@pytest.fixture
def sample_training_message():
    """Sample training resource message"""
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


@pytest.fixture
def adapter_ack_id():
    """Sample ack_id for adapter-update subscription"""
    return "projects/eosc-beyond-providers/subscriptions/transformer-adapter-update:22"


@pytest.fixture
def training_ack_id():
    """Sample ack_id for training_resource-create subscription"""
    return "projects/eosc-beyond-providers/subscriptions/transformer-training_resource-create:10"


@pytest.fixture
def guideline_ack_id():
    """Sample ack_id for interoperability_record-delete subscription"""
    return "projects/eosc-beyond-providers/subscriptions/transformer-interoperability_record-delete:5"


class TestProcessAmsMessageActions:
    """Tests for different action types"""

    @patch("app.transform.live_update.process_message.handle_create_action")
    def test_process_adapter_create(self, mock_handle_create, sample_adapter_message):
        """Test processing adapter create message"""
        message_json = json.dumps(sample_adapter_message)
        ack_id = "projects/test/subscriptions/transformer-adapter-create:1"

        with patch("app.settings.settings.ADAPTER", "adapters"):
            _process_ams_message(message_json, ack_id)
            mock_handle_create.assert_called_once()

    @patch("app.transform.live_update.process_message.handle_update_action")
    def test_process_adapter_update(
        self, mock_handle_update, sample_adapter_message, adapter_ack_id
    ):
        """Test processing adapter update message"""
        message_json = json.dumps(sample_adapter_message)

        with patch("app.settings.settings.ADAPTER", "adapters"):
            _process_ams_message(message_json, adapter_ack_id)
            mock_handle_update.assert_called_once()

    @patch("app.transform.live_update.process_message.handle_delete_action")
    def test_process_adapter_delete(self, mock_handle_delete, sample_adapter_message):
        """Test processing adapter delete message"""
        message_json = json.dumps(sample_adapter_message)
        ack_id = "projects/test/subscriptions/transformer-adapter-delete:1"

        with patch("app.settings.settings.ADAPTER", "adapters"):
            _process_ams_message(message_json, ack_id)
            mock_handle_delete.assert_called_once()

    @patch("app.transform.live_update.process_message.handle_create_action")
    def test_process_training_create(
        self, mock_handle_create, sample_training_message, training_ack_id
    ):
        """Test processing training resource create message"""
        message_json = json.dumps(sample_training_message)

        with patch("app.settings.settings.TRAINING", "trainings"):
            _process_ams_message(message_json, training_ack_id)
            mock_handle_create.assert_called_once()

    @patch("app.transform.live_update.process_message.handle_delete_action")
    def test_process_guideline_delete(
        self, mock_handle_delete, sample_guideline_message, guideline_ack_id
    ):
        """Test processing interoperability record delete message"""
        message_json = json.dumps(sample_guideline_message)

        with patch("app.settings.settings.GUIDELINE", "guidelines"):
            _process_ams_message(message_json, guideline_ack_id)
            mock_handle_delete.assert_called_once()


class TestProcessAmsMessageFormats:
    """Tests for different message formats"""

    @patch("app.transform.live_update.process_message.handle_update_action")
    def test_process_string_message(
        self, mock_handle_update, sample_adapter_message, adapter_ack_id
    ):
        """Test processing JSON string message"""
        message_json = json.dumps(sample_adapter_message)

        with patch("app.settings.settings.ADAPTER", "adapters"):
            _process_ams_message(message_json, adapter_ack_id)
            mock_handle_update.assert_called_once()

    @patch("app.transform.live_update.process_message.handle_update_action")
    def test_process_dict_message(
        self, mock_handle_update, sample_adapter_message, adapter_ack_id
    ):
        """Test processing dict message (not string)"""
        with patch("app.settings.settings.ADAPTER", "adapters"):
            _process_ams_message(sample_adapter_message, adapter_ack_id)
            mock_handle_update.assert_called_once()

    def test_process_invalid_json(self):
        """Test processing invalid JSON data"""
        invalid_json = "not valid json at all"

        with patch("app.transform.live_update.process_message.logger") as mock_logger:
            _process_ams_message(invalid_json, None)
            mock_logger.error.assert_called()


class TestSubscriptionNameExtraction:
    """Tests for subscription name extraction from ack_id"""

    @patch("app.transform.live_update.process_message.handle_update_action")
    def test_extract_subscription_name(
        self, mock_handle_update, sample_adapter_message, adapter_ack_id
    ):
        """Test subscription name extraction from ack_id"""
        message_json = json.dumps(sample_adapter_message)

        with patch("app.settings.settings.ADAPTER", "adapters"), patch(
            "app.transform.live_update.process_message.logger"
        ) as mock_logger:
            _process_ams_message(message_json, adapter_ack_id)
            # Check that subscription name was extracted
            logger_calls = str(mock_logger.info.call_args_list)
            assert "transformer-adapter-update" in logger_calls

    def test_invalid_ack_id_format(self, sample_adapter_message):
        """Test handling of invalid ack_id format"""
        message_json = json.dumps(sample_adapter_message)
        invalid_ack_id = "invalid-format"

        with patch("app.settings.settings.ADAPTER", "adapters"), patch(
            "app.transform.live_update.process_message.logger"
        ) as mock_logger, patch(
            "app.transform.live_update.process_message.handle_update_action"
        ):
            _process_ams_message(message_json, invalid_ack_id)
            # Should handle gracefully and use fallback
            mock_logger.warning.assert_called()


class TestActionDetection:
    """Tests for action detection from subscription name"""

    @patch("app.transform.live_update.process_message.handle_create_action")
    @patch("app.transform.live_update.process_message.handle_update_action")
    @patch("app.transform.live_update.process_message.handle_delete_action")
    def test_action_detection_create(
        self, mock_delete, mock_update, mock_create, sample_adapter_message
    ):
        """Test create action detection"""
        message_json = json.dumps(sample_adapter_message)
        ack_id = "projects/test/subscriptions/transformer-adapter-create:1"

        with patch("app.settings.settings.ADAPTER", "adapters"):
            _process_ams_message(message_json, ack_id)
            assert mock_create.called
            assert not mock_update.called
            assert not mock_delete.called

    @patch("app.transform.live_update.process_message.handle_create_action")
    @patch("app.transform.live_update.process_message.handle_update_action")
    @patch("app.transform.live_update.process_message.handle_delete_action")
    def test_action_detection_update(
        self,
        mock_delete,
        mock_update,
        mock_create,
        sample_adapter_message,
        adapter_ack_id,
    ):
        """Test update action detection"""
        message_json = json.dumps(sample_adapter_message)

        with patch("app.settings.settings.ADAPTER", "adapters"):
            _process_ams_message(message_json, adapter_ack_id)
            assert not mock_create.called
            assert mock_update.called
            assert not mock_delete.called

    @patch("app.transform.live_update.process_message.handle_create_action")
    @patch("app.transform.live_update.process_message.handle_update_action")
    @patch("app.transform.live_update.process_message.handle_delete_action")
    def test_action_detection_delete(
        self, mock_delete, mock_update, mock_create, sample_adapter_message
    ):
        """Test delete action detection"""
        message_json = json.dumps(sample_adapter_message)
        ack_id = "projects/test/subscriptions/transformer-adapter-delete:1"

        with patch("app.settings.settings.ADAPTER", "adapters"):
            _process_ams_message(message_json, ack_id)
            assert not mock_create.called
            assert not mock_update.called
            assert mock_delete.called


class TestResourceTypeDetection:
    """Tests for resource type detection"""

    @patch("app.transform.live_update.process_message.handle_update_action")
    def test_detect_adapter_resource(self, mock_handle, sample_adapter_message):
        """Test adapter resource detection"""
        message_json = json.dumps(sample_adapter_message)
        ack_id = "projects/test/subscriptions/transformer-adapter-update:1"

        with patch("app.settings.settings.ADAPTER", "adapters"):
            _process_ams_message(message_json, ack_id)
            # Verify handler was called
            assert mock_handle.called

    @patch("app.transform.live_update.process_message.handle_create_action")
    def test_detect_training_resource(self, mock_handle, sample_training_message):
        """Test training resource detection"""
        message_json = json.dumps(sample_training_message)
        ack_id = "projects/test/subscriptions/transformer-training_resource-create:1"

        with patch("app.settings.settings.TRAINING", "trainings"):
            _process_ams_message(message_json, ack_id)
            # Verify handler was called
            assert mock_handle.called

    @patch("app.transform.live_update.process_message.handle_delete_action")
    def test_detect_guideline_resource(self, mock_handle, sample_guideline_message):
        """Test guideline resource detection"""
        message_json = json.dumps(sample_guideline_message)
        ack_id = (
            "projects/test/subscriptions/transformer-interoperability_record-delete:1"
        )

        with patch("app.settings.settings.GUIDELINE", "guidelines"):
            _process_ams_message(message_json, ack_id)
            # Verify handler was called
            assert mock_handle.called


class TestMessageStatus:
    """Tests for message status handling"""

    @patch("app.transform.live_update.process_message.handle_create_action")
    def test_approved_status(self, mock_handle, sample_adapter_message):
        """Test message with approved status"""
        message_json = json.dumps(sample_adapter_message)
        ack_id = "projects/test/subscriptions/transformer-adapter-create:1"

        with patch("app.settings.settings.ADAPTER", "adapters"):
            _process_ams_message(message_json, ack_id)
            mock_handle.assert_called_once()

    @patch("app.transform.live_update.process_message.handle_update_action")
    def test_inactive_message(self, mock_handle):
        """Test message with inactive status"""
        message = {
            "active": False,
            "suspended": False,
            "status": "approved adapter",
            "adapter": {"id": "test", "name": "test"},
        }
        message_json = json.dumps(message)
        ack_id = "projects/test/subscriptions/transformer-adapter-update:1"

        with patch("app.settings.settings.ADAPTER", "adapters"):
            _process_ams_message(message_json, ack_id)
            mock_handle.assert_called_once()
            # Verify inactive status is passed
            call_args = mock_handle.call_args
            assert call_args[0][0] is False  # active=False

    @patch("app.transform.live_update.process_message.handle_update_action")
    def test_suspended_message(self, mock_handle):
        """Test message with suspended status"""
        message = {
            "active": True,
            "suspended": True,
            "status": "approved adapter",
            "adapter": {"id": "test", "name": "test"},
        }
        message_json = json.dumps(message)
        ack_id = "projects/test/subscriptions/transformer-adapter-update:1"

        with patch("app.settings.settings.ADAPTER", "adapters"):
            _process_ams_message(message_json, ack_id)
            mock_handle.assert_called_once()
            # Verify suspended status is passed
            call_args = mock_handle.call_args
            assert call_args[0][1] is True  # suspended=True
