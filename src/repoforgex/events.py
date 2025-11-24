"""
Event system for emitting developer activity events to external systems like NEOPlayer.
Supports webhooks for tracking repository operations and awarding XP to developers.
"""

import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


@dataclass
class DeveloperEvent:
    """Represents a developer activity event that can earn XP."""

    event_type: str
    developer: str
    repository: str
    timestamp: str
    xp_value: int
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for JSON serialization."""
        return asdict(self)


class EventEmitter:
    """Emits developer activity events to configured webhooks."""

    # XP values for different event types
    XP_VALUES = {
        "repo_created": 50,
        "repo_initialized": 30,
        "template_applied": 20,
        "health_check_excellent": 100,
        "health_check_good": 50,
        "health_check_fair": 25,
        "batch_operation_success": 75,
        "security_policy_added": 40,
        "ci_setup": 60,
        "tests_added": 50,
    }

    def __init__(self, webhook_url: Optional[str] = None):
        """
        Initialize the event emitter.

        Args:
            webhook_url: URL to send webhooks to (defaults to env var)
        """
        self.webhook_url = webhook_url or os.environ.get("NEOPLAYER_WEBHOOK_URL")
        self.enabled = bool(self.webhook_url)
        self.events_buffer: List[DeveloperEvent] = []

    def emit(
        self,
        event_type: str,
        developer: str,
        repository: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Emit a developer activity event.

        Args:
            event_type: Type of event (e.g., 'repo_created')
            developer: Developer username
            repository: Repository name
            metadata: Additional event data

        Returns:
            True if event was emitted successfully, False otherwise
        """
        xp_value = self.XP_VALUES.get(event_type, 10)

        event = DeveloperEvent(
            event_type=event_type,
            developer=developer,
            repository=repository,
            timestamp=datetime.now(timezone.utc).isoformat(),
            xp_value=xp_value,
            metadata=metadata or {},
        )

        self.events_buffer.append(event)

        if self.enabled:
            return self._send_webhook(event)
        else:
            logger.debug(
                f"Event emitted (webhook disabled): {event_type} "
                f"for {developer} on {repository}"
            )
            return True

    def _send_webhook(self, event: DeveloperEvent) -> bool:
        """
        Send event to webhook endpoint.

        Args:
            event: Event to send

        Returns:
            True if webhook was sent successfully, False otherwise
        """
        if not self.webhook_url:
            return False

        try:
            response = requests.post(
                self.webhook_url,
                json=event.to_dict(),
                headers={"Content-Type": "application/json"},
                timeout=5,
            )

            if response.status_code == 200:
                logger.info(
                    f"Event sent to NEOPlayer: {event.event_type} "
                    f"({event.xp_value} XP) for {event.developer}"
                )
                return True
            else:
                logger.warning(
                    f"Webhook failed with status {response.status_code}: {response.text}"
                )
                return False
        except (requests.RequestException, Exception) as e:
            logger.error(f"Failed to send webhook: {e}")
            return False

    def get_events(self) -> List[DeveloperEvent]:
        """Get all buffered events."""
        return self.events_buffer

    def get_total_xp(self, developer: str) -> int:
        """
        Calculate total XP earned by a developer.

        Args:
            developer: Developer username

        Returns:
            Total XP earned
        """
        return sum(event.xp_value for event in self.events_buffer if event.developer == developer)

    def get_event_summary(self) -> Dict[str, Any]:
        """
        Get summary of all events.

        Returns:
            Dictionary with event statistics
        """
        if not self.events_buffer:
            return {
                "total_events": 0,
                "total_xp": 0,
                "developers": {},
                "event_types": {},
            }

        developers = {}
        event_types = {}

        for event in self.events_buffer:
            # Track by developer
            if event.developer not in developers:
                developers[event.developer] = {
                    "events": 0,
                    "xp": 0,
                    "repositories": set(),
                }
            developers[event.developer]["events"] += 1
            developers[event.developer]["xp"] += event.xp_value
            developers[event.developer]["repositories"].add(event.repository)

            # Track by event type
            if event.event_type not in event_types:
                event_types[event.event_type] = {"count": 0, "total_xp": 0}
            event_types[event.event_type]["count"] += 1
            event_types[event.event_type]["total_xp"] += event.xp_value

        # Convert sets to counts
        for dev_data in developers.values():
            dev_data["repositories"] = len(dev_data["repositories"])

        return {
            "total_events": len(self.events_buffer),
            "total_xp": sum(e.xp_value for e in self.events_buffer),
            "developers": developers,
            "event_types": event_types,
        }

    def export_events(self, filepath: str) -> None:
        """
        Export events to a JSON file.

        Args:
            filepath: Path to export file
        """
        with open(filepath, "w") as f:
            json.dump([event.to_dict() for event in self.events_buffer], f, indent=2)
        logger.info(f"Exported {len(self.events_buffer)} events to {filepath}")


# Global event emitter instance
_emitter: Optional[EventEmitter] = None


def get_event_emitter() -> EventEmitter:
    """Get or create the global event emitter instance."""
    global _emitter
    if _emitter is None:
        _emitter = EventEmitter()
    return _emitter


def emit_event(
    event_type: str,
    developer: str,
    repository: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Convenience function to emit an event using the global emitter.

    Args:
        event_type: Type of event
        developer: Developer username
        repository: Repository name
        metadata: Additional event data

    Returns:
        True if event was emitted successfully
    """
    emitter = get_event_emitter()
    return emitter.emit(event_type, developer, repository, metadata)
