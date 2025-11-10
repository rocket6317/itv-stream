def get_dashboard_data():
    data = {
        "latest": latest_links,
        "history": {},
        "diffs": {},
        "counts": {},
        "elapsed": {},
        "expiry": {},
        "validity": {},
        "requests": {},
        "expiry_str": {}
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

        meta = get_cached_meta(channel)
        data["expiry"][channel] = meta.get("expiry", 0)
        data["validity"][channel] = meta.get("validity", 0)
        data["requests"][channel] = meta.get("requests", 0)
        if meta.get("expiry"):
            dt = datetime.fromtimestamp(meta["expiry"])
            data["expiry_str"][channel] = dt.strftime("%a %d %b %Y %H:%M")
        else:
            data["expiry_str"][channel] = "Unknown"
    return data
