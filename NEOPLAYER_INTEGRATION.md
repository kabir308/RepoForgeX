# NEOPlayer Integration Guide

## Overview

RepoForgeX integrates seamlessly with NEOPlayer to gamify developer activities and reward them with XP (Experience Points) for their contributions. This integration tracks repository operations and automatically sends events to NEOPlayer for XP attribution.

## What is NEOPlayer?

NEOPlayer is a gamification system that rewards developers with XP for their activities. By integrating RepoForgeX with NEOPlayer, you can:

- **Reward repository creation** - Developers earn XP when they create new repositories
- **Incentivize best practices** - Higher XP for repositories with excellent health scores
- **Track contributions** - Monitor developer activity across multiple repositories
- **Build engagement** - Gamify the development process to increase motivation

## How It Works

### Event-Driven Architecture

RepoForgeX uses an event-driven architecture to track developer activities:

1. **Activity Detection** - RepoForgeX monitors repository operations (creation, template generation, health checks, etc.)
2. **Event Emission** - Each activity triggers an event with developer information and XP value
3. **Webhook Delivery** - Events are sent to NEOPlayer via webhooks
4. **XP Attribution** - NEOPlayer processes events and awards XP to developers

### Event Types and XP Values

| Event Type | XP Value | Description |
|------------|----------|-------------|
| `repo_created` | 50 | Created a new repository |
| `repo_initialized` | 30 | Initialized repository with code |
| `template_applied` | 20 | Applied a template to repository |
| `health_check_excellent` | 100 | Repository health score ≥ 90% |
| `health_check_good` | 50 | Repository health score ≥ 75% |
| `health_check_fair` | 25 | Repository health score ≥ 50% |
| `batch_operation_success` | 75 | Successful batch operation |
| `security_policy_added` | 40 | Added security policy |
| `ci_setup` | 60 | Set up CI/CD |
| `tests_added` | 50 | Added tests to repository |

## Setup Instructions

### 1. Configure NEOPlayer Webhook URL

Set the `NEOPLAYER_WEBHOOK_URL` environment variable to point to your NEOPlayer webhook endpoint:

```bash
export NEOPLAYER_WEBHOOK_URL="https://neoplayer.kabverse.io/webhooks/repoforgex"
```

Or add it to your `.env` file:

```env
NEOPLAYER_WEBHOOK_URL=https://neoplayer.kabverse.io/webhooks/repoforgex
```

### 2. Enable Event Tracking

Event tracking is automatically enabled when the webhook URL is configured. If you want to track events locally without sending to NEOPlayer, simply omit the webhook URL - events will still be buffered for analytics.

### 3. Docker Compose Setup

Add the webhook URL to your `docker-compose.yml`:

```yaml
version: "3.8"
services:
  repoforgex:
    build: .
    environment:
      - GITHUB_USER=${GITHUB_USER}
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - NEOPLAYER_WEBHOOK_URL=${NEOPLAYER_WEBHOOK_URL}
    ports:
      - "5000:5000"
```

## Event Payload Format

Events sent to NEOPlayer follow this JSON format:

```json
{
  "event_type": "repo_created",
  "developer": "alice",
  "repository": "my-awesome-repo",
  "timestamp": "2025-11-24T12:00:00.000000",
  "xp_value": 50,
  "metadata": {
    "visibility": "private",
    "template": "python-basic"
  }
}
```

### Field Descriptions

- **event_type** (string): Type of event that occurred
- **developer** (string): GitHub username of the developer
- **repository** (string): Name of the repository
- **timestamp** (ISO 8601): UTC timestamp when event occurred
- **xp_value** (integer): XP points to award
- **metadata** (object): Additional context about the event

## API Endpoints

RepoForgeX provides REST API endpoints for NEOPlayer integration:

### Get All Events

```http
GET /api/v1/events
```

**Response:**
```json
{
  "summary": {
    "total_events": 25,
    "total_xp": 1250,
    "developers": {
      "alice": {
        "events": 15,
        "xp": 750,
        "repositories": 5
      }
    },
    "event_types": {
      "repo_created": {
        "count": 5,
        "total_xp": 250
      }
    }
  },
  "events": [...]
}
```

### Get Developer-Specific Events

```http
GET /api/v1/events/developer/{developer}
```

**Example:**
```bash
curl http://localhost:5000/api/v1/events/developer/alice
```

**Response:**
```json
{
  "developer": "alice",
  "total_xp": 750,
  "event_count": 15,
  "events": [...]
}
```

### CI/CD Webhook Endpoint

```http
POST /api/v1/cicd/webhook
```

**Headers:**
- `X-GitHub-Event`: Event type (e.g., "push", "repository")
- `Content-Type`: application/json

**Usage:**
Configure this endpoint as a GitHub webhook to automatically track repository events.

## Usage Examples

### Programmatic Event Emission

```python
from repoforgex.events import emit_event

# Emit an event when a repository is created
emit_event(
    event_type="repo_created",
    developer="alice",
    repository="my-new-repo",
    metadata={"visibility": "private"}
)

# Emit an event for excellent health score
emit_event(
    event_type="health_check_excellent",
    developer="bob",
    repository="my-repo",
    metadata={"score": 95}
)
```

### Get Event Statistics

```python
from repoforgex.events import get_event_emitter

emitter = get_event_emitter()

# Get total XP for a developer
total_xp = emitter.get_total_xp("alice")
print(f"Alice has earned {total_xp} XP")

# Get event summary
summary = emitter.get_event_summary()
print(f"Total events: {summary['total_events']}")
print(f"Total XP distributed: {summary['total_xp']}")
```

### Export Events

```python
from repoforgex.events import get_event_emitter

emitter = get_event_emitter()
emitter.export_events("events_report.json")
```

## Integration with CLI

The CLI automatically emits events during repository operations:

```bash
# Create repositories and earn XP
python -m repoforgex.cli --config repos.yml

# Generate templates and earn XP
python -m repoforgex.cli --config repos.yml --auto-templates

# Health check and earn XP based on score
python -m repoforgex.cli --config repos.yml --health-check
```

## Testing the Integration

### Local Testing without NEOPlayer

You can test event tracking locally without a live NEOPlayer instance:

```python
from repoforgex.events import EventEmitter

# Create emitter without webhook
emitter = EventEmitter()

# Emit some test events
emitter.emit("repo_created", "test_user", "test_repo")
emitter.emit("health_check_excellent", "test_user", "test_repo")

# Check results
print(f"Total XP: {emitter.get_total_xp('test_user')}")
print(f"Events: {len(emitter.get_events())}")
```

### Testing Webhook Delivery

To test webhook delivery to NEOPlayer:

1. **Set up a webhook receiver** (e.g., using RequestBin or ngrok)
2. **Configure the webhook URL**:
   ```bash
   export NEOPLAYER_WEBHOOK_URL="https://your-test-webhook.com/endpoint"
   ```
3. **Trigger some events**:
   ```bash
   python -m repoforgex.cli --config repos.yml --dry-run
   ```
4. **Verify webhook delivery** in your webhook receiver logs

## Monitoring and Troubleshooting

### Check Webhook Status

View the RepoForgeX logs to monitor webhook delivery:

```bash
# Docker logs
docker compose logs -f repoforgex

# Look for messages like:
# Event sent to NEOPlayer: repo_created (50 XP) for alice
# Webhook failed with status 500: Internal Server Error
```

### Common Issues

**Webhooks not being sent:**
- Verify `NEOPLAYER_WEBHOOK_URL` is set correctly
- Check network connectivity to NEOPlayer
- Review RepoForgeX logs for error messages

**Events not tracked:**
- Ensure you're using the latest version of RepoForgeX (0.4.0+)
- Verify developer username is set correctly
- Check that operations are completing successfully

**XP values incorrect:**
- Review the XP value mapping in the documentation
- Check event metadata for additional context
- Verify event type is recognized

## Security Considerations

### Authentication

For production deployments, ensure your NEOPlayer webhook endpoint:
- Uses HTTPS (not HTTP)
- Implements authentication (API key, JWT, etc.)
- Validates incoming webhook signatures

### Example with API Key

```python
from repoforgex.events import EventEmitter

class SecureEventEmitter(EventEmitter):
    def _send_webhook(self, event):
        response = requests.post(
            self.webhook_url,
            json=event.to_dict(),
            headers={
                "Content-Type": "application/json",
                "X-API-Key": os.environ.get("NEOPLAYER_API_KEY"),
            },
            timeout=5,
        )
        # ... rest of implementation
```

### Data Privacy

Event payloads contain:
- Developer usernames (public GitHub usernames)
- Repository names
- Activity timestamps
- XP values

Ensure compliance with your organization's data privacy policies.

## Advanced Configuration

### Custom XP Values

You can customize XP values by modifying the `EventEmitter.XP_VALUES` dictionary:

```python
from repoforgex.events import get_event_emitter

emitter = get_event_emitter()
emitter.XP_VALUES["repo_created"] = 100  # Increase XP for repo creation
emitter.XP_VALUES["custom_event"] = 25   # Add custom event type
```

### Custom Event Types

Add your own event types:

```python
from repoforgex.events import emit_event

# Emit custom event
emit_event(
    event_type="custom_achievement",
    developer="alice",
    repository="my-repo",
    metadata={"achievement": "First Commit"}
)
```

## Kabverse v3 Integration

RepoForgeX is designed to be the **CI/CD Brain of Kabverse v3**. The NEOPlayer integration is a key component of this vision:

1. **Automated Tracking** - All development activities are automatically tracked
2. **Real-time XP Updates** - Developers see immediate feedback for their work
3. **Gamification Layer** - Incentivizes best practices and quality code
4. **Analytics Dashboard** - Provides insights into team productivity

### Future Enhancements

Planned features for deeper Kabverse v3 integration:
- Team leaderboards
- Achievement badges
- Milestone tracking
- XP multipliers for streaks
- Integration with other Kabverse tools

## Support and Feedback

For issues or questions about the NEOPlayer integration:
- Check the [main documentation](README.md)
- Review the [Revolutionary Features Guide](REVOLUTIONARY_FEATURES.md)
- Open an issue on GitHub
- Contact the Kabverse team

---

**Version:** 0.4.0  
**Last Updated:** 2025-11-24  
**Status:** Production Ready ✅
