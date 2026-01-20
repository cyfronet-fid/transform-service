"""
Tests for process_message dispatcher function
"""

import json
from unittest.mock import Mock, patch

import pytest

from app.transform.live_update.process_message import process_message


@pytest.fixture
def mock_stomp_frame():
    """Create a mock STOMP frame"""
    frame = Mock()
    frame.headers = {"destination": "/queue/adapter.update"}
    frame.body = json.dumps(
        {
            "active": True,
            "suspended": False,
            "status": "approved adapter",
            "adapter": {"id": "test", "name": "test"},
        }
    )
    return frame


@pytest.fixture
def sample_ams_message_dict():
    """Sample AMS message as dict"""
    return {
        "active": True,
        "suspended": False,
        "status": "approved adapter",
        "adapter": {"id": "test", "name": "test"},
    }


@pytest.fixture
def sample_ams_ack_id():
    """Sample AMS ack_id"""
    return "projects/test/subscriptions/transformer-adapter-update:1"


class TestProcessMessageDispatcher:
    """Tests for process_message dispatcher function"""

    @patch("app.transform.live_update.process_message._process_stomp_message")
    def test_dispatch_stomp_message(self, mock_stomp, mock_stomp_frame):
        """Test that STOMP messages are routed to STOMP handler"""
        process_message(mock_stomp_frame)
        mock_stomp.assert_called_once_with(mock_stomp_frame)

    @patch("app.transform.live_update.process_message._process_ams_message")
    def test_dispatch_ams_string_message(
        self, mock_ams, sample_ams_message_dict, sample_ams_ack_id
    ):
        """Test that AMS string messages are routed to AMS handler"""
        message_str = json.dumps(sample_ams_message_dict)
        process_message(message_str, sample_ams_ack_id)
        mock_ams.assert_called_once()

    @patch("app.transform.live_update.process_message._process_ams_message")
    def test_dispatch_ams_dict_message(
        self, mock_ams, sample_ams_message_dict, sample_ams_ack_id
    ):
        """Test that AMS dict messages are routed to AMS handler"""
        process_message(sample_ams_message_dict, sample_ams_ack_id)
        mock_ams.assert_called_once()

    @patch("app.transform.live_update.process_message._process_stomp_message")
    def test_stomp_frame_has_headers_and_body(self, mock_stomp):
        """Test that STOMP detection checks for headers and body attributes"""
        frame = Mock()
        frame.headers = {"destination": "/queue/test"}
        frame.body = "{}"

        process_message(frame)
        mock_stomp.assert_called_once()

    @patch("app.transform.live_update.process_message._process_ams_message")
    def test_ams_message_without_headers_attribute(self, mock_ams):
        """Test that messages without headers attribute are treated as AMS"""
        message = "plain string message"
        process_message(message)
        mock_ams.assert_called_once()

    @patch("app.transform.live_update.process_message._process_ams_message")
    def test_ams_message_with_ack_id(
        self, mock_ams, sample_ams_message_dict, sample_ams_ack_id
    ):
        """Test that ack_id is passed to AMS handler"""
        process_message(sample_ams_message_dict, sample_ams_ack_id)
        # Verify ack_id was passed
        call_args = mock_ams.call_args
        assert call_args[0][1] == sample_ams_ack_id

    @patch("app.transform.live_update.process_message._process_ams_message")
    def test_ams_message_without_ack_id(self, mock_ams, sample_ams_message_dict):
        """Test that AMS handler works without ack_id"""
        process_message(sample_ams_message_dict)
        mock_ams.assert_called_once()

    def test_stomp_frame_detection_accuracy(self):
        """Test STOMP frame detection is accurate and doesn't false positive"""
        # This is an AMS dict that shouldn't be detected as STOMP
        ams_message = {
            "headers": "not an attribute",  # This is a key, not an attribute
            "body": "not an attribute",
            "adapter": {"id": "test"},
        }

        with patch(
            "app.transform.live_update.process_message._process_ams_message"
        ) as mock_ams:
            process_message(ams_message)
            # Should be routed to AMS handler, not STOMP
            mock_ams.assert_called_once()

    @patch("app.transform.live_update.process_message._process_stomp_message")
    def test_stomp_with_required_attributes(self, mock_stomp):
        """Test STOMP detection requires both headers AND body"""
        frame = Mock()
        frame.headers = {"destination": "/queue/test"}
        # body attribute is present (Mock creates it automatically)

        process_message(frame)
        mock_stomp.assert_called_once()

    @patch("app.transform.live_update.process_message._process_ams_message")
    def test_stomp_detection_requires_both_attrs(self, mock_ams):
        """Test that message without both headers and body goes to AMS"""
        # Create an object with only headers, not body
        frame = Mock()
        frame.headers = {"destination": "/queue/test"}
        # Remove body attribute
        del frame.body

        process_message(frame)
        mock_ams.assert_called_once()
