import time
import logging

logger = logging.getLogger(__name__)

latest_links = {}
link_history = {}

def record_link(channel: str, new_url: str):
    current_url = latest_links.get(channel)
    if current_url != new_url:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        logger.info(f"[LINK CHANGE] Channel: {channel} | New URL: {new_url} | Time: {timestamp}")
        latest_links[channel] = new_url
        link_history.setdefault(channel, []).append({
            "url": new_url,
            "timestamp": timestamp
        })

def get_dashboard_data():
    return {
        "latest": latest_links,
        "history": link_history
    }
