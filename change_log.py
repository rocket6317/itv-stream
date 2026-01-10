"""
Simple change tracking for ITV tokens and stream URLs.
Logs to file so we can analyze actual expiration patterns.
"""

import os
import json
from datetime import datetime
from pathlib import Path

LOG_FILE = os.path.join(os.path.dirname(__file__), 'change_log.json')


def log_change(event_type, channel, details=None):
    """
    Log a change event.

    event_type: 'token_refresh', 'url_refresh', 'url_error', 'token_error'
    channel: Channel name or 'ALL' for token events
    details: Optional dict with extra info (old_value, new_value, error, etc.)
    """
    entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'channel': channel,
    }

    if details:
        entry['details'] = details

    # Read existing log
    logs = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r') as f:
                logs = json.load(f)
        except (json.JSONDecodeError, IOError):
            logs = []

    # Add new entry (keep last 1000 entries)
    logs.append(entry)
    if len(logs) > 1000:
        logs = logs[-1000:]

    # Write back
    with open(LOG_FILE, 'w') as f:
        json.dump(logs, f, indent=2)


def get_logs(limit=100):
    """Get recent log entries."""
    if not os.path.exists(LOG_FILE):
        return []

    try:
        with open(LOG_FILE, 'r') as f:
            logs = json.load(f)
        return logs[-limit:]
    except (json.JSONDecodeError, IOError):
        return []


def get_token_history():
    """Analyze token refresh events to find patterns."""
    logs = get_logs(1000)
    token_events = [l for l in logs if l['event_type'] == 'token_refresh']

    if not token_events:
        return None

    # Calculate time between token refreshes
    intervals = []
    for i in range(1, len(token_events)):
        prev = datetime.fromisoformat(token_events[i-1]['timestamp'])
        curr = datetime.fromisoformat(token_events[i]['timestamp'])
        hours = (curr - prev).total_seconds() / 3600
        intervals.append(hours)

    if not intervals:
        return None

    return {
        'total_refreshes': len(token_events),
        'avg_hours_between': sum(intervals) / len(intervals) if intervals else 0,
        'min_hours': min(intervals) if intervals else 0,
        'max_hours': max(intervals) if intervals else 0,
        'last_refresh': token_events[-1]['timestamp'] if token_events else None,
    }


def get_url_history(channel=None):
    """Get URL refresh history for a channel."""
    logs = get_logs(1000)
    url_events = [l for l in logs if l['event_type'] == 'url_refresh']

    if channel:
        url_events = [l for l in url_events if l['channel'] == channel]

    return url_events[-20:]  # Last 20 events
