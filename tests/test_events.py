"""Tests for the event emitter system."""

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from repoforgex.events import DeveloperEvent, EventEmitter, emit_event, get_event_emitter


class TestDeveloperEvent:
    """Tests for DeveloperEvent dataclass."""

    def test_create_event(self):
        """Test creating a developer event."""
        event = DeveloperEvent(
            event_type="repo_created",
            developer="alice",
            repository="my-repo",
            timestamp="2025-11-24T12:00:00",
            xp_value=50,
            metadata={"visibility": "private"},
        )

        assert event.event_type == "repo_created"
        assert event.developer == "alice"
        assert event.repository == "my-repo"
        assert event.xp_value == 50
        assert event.metadata == {"visibility": "private"}

    def test_event_to_dict(self):
        """Test converting event to dictionary."""
        event = DeveloperEvent(
            event_type="template_applied",
            developer="bob",
            repository="test-repo",
            timestamp="2025-11-24T12:00:00",
            xp_value=20,
        )

        event_dict = event.to_dict()
        assert event_dict["event_type"] == "template_applied"
        assert event_dict["developer"] == "bob"
        assert event_dict["xp_value"] == 20


class TestEventEmitter:
    """Tests for EventEmitter class."""

    def test_emitter_initialization(self):
        """Test emitter initialization."""
        emitter = EventEmitter()
        assert not emitter.enabled
        assert len(emitter.events_buffer) == 0

        emitter_with_webhook = EventEmitter(webhook_url="https://example.com/webhook")
        assert emitter_with_webhook.enabled
        assert emitter_with_webhook.webhook_url == "https://example.com/webhook"

    def test_emit_event_without_webhook(self):
        """Test emitting event without webhook configured."""
        emitter = EventEmitter()
        result = emitter.emit(
            event_type="repo_created",
            developer="alice",
            repository="my-repo",
        )

        assert result is True
        assert len(emitter.events_buffer) == 1
        assert emitter.events_buffer[0].event_type == "repo_created"
        assert emitter.events_buffer[0].developer == "alice"
        assert emitter.events_buffer[0].xp_value == 50

    def test_emit_multiple_events(self):
        """Test emitting multiple events."""
        emitter = EventEmitter()

        emitter.emit("repo_created", "alice", "repo1")
        emitter.emit("template_applied", "alice", "repo1")
        emitter.emit("repo_created", "bob", "repo2")

        assert len(emitter.events_buffer) == 3

    @patch("repoforgex.events.requests.post")
    def test_emit_event_with_webhook_success(self, mock_post):
        """Test emitting event with webhook successfully."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        emitter = EventEmitter(webhook_url="https://example.com/webhook")
        result = emitter.emit(
            event_type="health_check_excellent",
            developer="alice",
            repository="my-repo",
            metadata={"score": 95},
        )

        assert result is True
        assert mock_post.called
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://example.com/webhook"
        assert "json" in call_args[1]

    @patch("repoforgex.events.requests.post")
    def test_emit_event_with_webhook_failure(self, mock_post):
        """Test emitting event with webhook failure."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        emitter = EventEmitter(webhook_url="https://example.com/webhook")
        result = emitter.emit("repo_created", "alice", "my-repo")

        assert result is False

    @patch("repoforgex.events.requests.post")
    def test_emit_event_with_webhook_exception(self, mock_post):
        """Test emitting event with webhook exception."""
        mock_post.side_effect = Exception("Network error")

        emitter = EventEmitter(webhook_url="https://example.com/webhook")
        result = emitter.emit("repo_created", "alice", "my-repo")

        assert result is False

    def test_xp_values(self):
        """Test XP values for different event types."""
        emitter = EventEmitter()

        emitter.emit("repo_created", "alice", "repo1")
        assert emitter.events_buffer[-1].xp_value == 50

        emitter.emit("health_check_excellent", "alice", "repo1")
        assert emitter.events_buffer[-1].xp_value == 100

        emitter.emit("template_applied", "alice", "repo1")
        assert emitter.events_buffer[-1].xp_value == 20

        emitter.emit("unknown_event", "alice", "repo1")
        assert emitter.events_buffer[-1].xp_value == 10  # default

    def test_get_total_xp(self):
        """Test getting total XP for a developer."""
        emitter = EventEmitter()

        emitter.emit("repo_created", "alice", "repo1")  # 50 XP
        emitter.emit("template_applied", "alice", "repo1")  # 20 XP
        emitter.emit("repo_created", "bob", "repo2")  # 50 XP

        assert emitter.get_total_xp("alice") == 70
        assert emitter.get_total_xp("bob") == 50
        assert emitter.get_total_xp("charlie") == 0

    def test_get_event_summary(self):
        """Test getting event summary."""
        emitter = EventEmitter()

        emitter.emit("repo_created", "alice", "repo1")
        emitter.emit("template_applied", "alice", "repo1")
        emitter.emit("repo_created", "alice", "repo2")
        emitter.emit("repo_created", "bob", "repo3")

        summary = emitter.get_event_summary()

        assert summary["total_events"] == 4
        assert summary["total_xp"] == 170  # 50+20+50+50
        assert "alice" in summary["developers"]
        assert summary["developers"]["alice"]["events"] == 3
        assert summary["developers"]["alice"]["xp"] == 120
        assert summary["developers"]["alice"]["repositories"] == 2
        assert "repo_created" in summary["event_types"]
        assert summary["event_types"]["repo_created"]["count"] == 3

    def test_get_event_summary_empty(self):
        """Test getting summary with no events."""
        emitter = EventEmitter()
        summary = emitter.get_event_summary()

        assert summary["total_events"] == 0
        assert summary["total_xp"] == 0
        assert summary["developers"] == {}
        assert summary["event_types"] == {}

    def test_export_events(self, tmp_path):
        """Test exporting events to file."""
        emitter = EventEmitter()
        emitter.emit("repo_created", "alice", "repo1")
        emitter.emit("template_applied", "alice", "repo1")

        export_path = tmp_path / "events.json"
        emitter.export_events(str(export_path))

        assert export_path.exists()

        with open(export_path) as f:
            events = json.load(f)

        assert len(events) == 2
        assert events[0]["event_type"] == "repo_created"
        assert events[1]["event_type"] == "template_applied"


class TestGlobalEmitter:
    """Tests for global emitter functions."""

    def test_get_event_emitter(self):
        """Test getting global emitter."""
        emitter1 = get_event_emitter()
        emitter2 = get_event_emitter()
        assert emitter1 is emitter2  # Same instance

    def test_emit_event_function(self):
        """Test convenience emit_event function."""
        result = emit_event(
            event_type="repo_created",
            developer="alice",
            repository="my-repo",
            metadata={"test": True},
        )

        assert result is True

        emitter = get_event_emitter()
        events = emitter.get_events()
        assert len(events) > 0
        assert events[-1].event_type == "repo_created"
        assert events[-1].metadata == {"test": True}

    def test_emit_event_with_env_webhook(self, monkeypatch):
        """Test emit_event with webhook from environment."""
        monkeypatch.setenv("NEOPLAYER_WEBHOOK_URL", "https://example.com/webhook")

        # Reset global emitter
        import repoforgex.events

        repoforgex.events._emitter = None

        with patch("repoforgex.events.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            result = emit_event("repo_created", "alice", "my-repo")

            assert result is True
            assert mock_post.called
