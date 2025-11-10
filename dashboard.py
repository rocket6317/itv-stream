import time
import logging
import difflib
import threading
from datetime import datetime

logger = logging.getLogger(__name__)

latest_links = {}
link_history = {}

CHANNELS = ["ITV", "ITV2", "ITV3", "ITV4", "ITVBe"]

def fetch_stream_url(channel: str) -> str:
    # Replace with actual logic to fetch the current stream URL
    return f"https://stream.itv.com/live/{channel.lower()}.m3u8"

def record_link(channel: str, new_url: str):
    current_url = latest_links.get(channel)
    if current_url != new_url:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        logger.info(f"[LINK CHANGE] Channel: {channel} | Time: {timestamp}")
        latest_links[channel] = new_url
        link_history.setdefault(channel, []).append({
            "url": new_url,
            "timestamp": timestamp
        })

def highlight_diff(old: str, new: str) -> str:
    diff = difflib.ndiff(old, new)
    result = ""
    for part in diff:
        if part.startswith("+ "):
            result += f"<b style='color:red'>{part[2:]}</b>"
        elif part.startswith("  "):
            result += part[2:]
    return result

def get_dashboard_data():
    data = {
        "latest": latest_links,
        "history": {},
        "diffs": {},
        "counts": {},
        "elapsed": {}
    }
    now = datetime.now()
    for channel, history in link_history.items():
        data["history"][channel] = history
        data["counts"][channel] = len(history)

        last_time = datetime.strptime(history[-1]["timestamp"], "%Y-%m-%d %H:%M:%S")
        delta = now - last_time
        hours, remainder = divmod(delta.total_seconds(), 3600)
        minutes, _ = divmod(remainder, 60)
        data["elapsed"][channel] = f"{int(hours)}h {int(minutes)}m ago"

        if len(history) >= 2:
            old = history[-2]["url"]
            new = history[-1]["url"]
            data["diffs"][channel] = highlight_diff(old, new)
        else:
            data["diffs"][channel] = f"<b>{history[-1]['url']}</b>"
    return data

def auto_check_loop(interval_seconds=300):
    def loop():
        while True:
            for channel in CHANNELS:
                new_url = fetch_stream_url(channel)
                record_link(channel, new_url)
            time.sleep(interval_seconds)
    threading.Thread(target=loop, daemon=True).start()
