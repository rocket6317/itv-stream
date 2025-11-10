from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)
cache_store = {}

def extract_expiry(url):
    match = re.search(r"[?&]exp=(\d+)", url)
    if match:
        return int(match.group(1))
    return int(datetime.utcnow().timestamp()) + 3600

def set_cached_url(channel, url):
    expiry = extract_expiry(url)
    now = int(datetime.utcnow().timestamp())
    validity = expiry - now
    cache_store[channel] = {
        "url": url,
        "expiry": expiry,
        "validity": validity,
        "requests": 0  # reset count
    }
    logger.info(f"[CACHE SET] {channel} | expiry: {expiry} | validity: {validity}s")

def get_cached_url(channel):
    entry = cache_store.get(channel)
    now = int(datetime.utcnow().timestamp())
    if entry and entry["expiry"] > now:
        entry["requests"] += 1
        logger.info(f"[CACHE HIT] {channel} | count: {entry['requests']} | expires in {entry['expiry'] - now}s")
        return entry["url"]
    logger.info(f"[CACHE MISS] {channel}")
    return None

def get_cached_meta(channel):
    return cache_store.get(channel, {})
