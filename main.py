import asyncio
import logging
import os
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.status import HTTP_401_UNAUTHORIZED
from dotenv import load_dotenv
from dashboard import get_dashboard_data
from cache import get_cached_url, set_cached_url, peek_cached_entry
from client import fetch_stream_url
from change_log import get_logs, get_token_history, get_url_history

app = FastAPI()
templates = Jinja2Templates(directory="templates")
security = HTTPBasic()
logger = logging.getLogger("uvicorn")

load_dotenv("stack.env")
USERNAME = os.getenv("DASHBOARD_USER")
PASSWORD = os.getenv("DASHBOARD_PASS")
REFRESH_INTERVAL = int(os.getenv("REFRESH_INTERVAL", "21300"))
CHANNELS = ["ITV", "ITV2", "ITV3", "ITV4", "ITVBe"]

def check_auth(credentials: HTTPBasicCredentials):
    if credentials.username != USERNAME or credentials.password != PASSWORD:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED)

from fastapi import Request

@app.get("/itvx")
async def redirect_itv(channel: str, request: Request):
    ip = request.client.host
    entry = get_cached_url(channel, ip)
    if entry:
        return RedirectResponse(entry["url"], status_code=302)
    raise HTTPException(status_code=503, detail="Stream not ready or expired")

@app.get("/dashboard")
async def dashboard(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(security)
):
    check_auth(credentials)
    data = get_dashboard_data()
    return templates.TemplateResponse("dashboard.html", {"request": request, "data": data})

@app.get("/dashboard/json")
async def dashboard_json(credentials: HTTPBasicCredentials = Depends(security)):
    check_auth(credentials)
    return get_dashboard_data()

@app.get("/raw")
async def raw_manifest():
    return RedirectResponse("https://example.com/static.mpd")

@app.get("/health")
async def health_check():
    """Health check endpoint that also verifies token validity."""
    try:
        # Try to fetch a stream URL to verify token is valid
        url = await fetch_stream_url("ITV")
        return {
            "status": "healthy",
            "token_valid": True,
            "test_stream": url[:100] + "..."
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "token_valid": False,
            "error": str(e)
        }, 503

@app.post("/admin/reload-token")
async def reload_token(
    credentials: HTTPBasicCredentials = Depends(security)
):
    """Manually trigger a token reload from environment."""
    check_auth(credentials)

    # Reload environment variables
    from dotenv import load_dotenv
    load_dotenv("stack.env", override=True)

    # Clear the cache to force re-fetch with new token
    from cache import CACHE
    CACHE.clear()

    return {"status": "success", "message": "Token reloaded from environment"}

@app.on_event("startup")
async def startup_event():
    for channel in CHANNELS:
        try:
            url = await fetch_stream_url(channel)
            set_cached_url(channel, url)
            logger.info(f"[STARTUP] Cached {channel}")
        except Exception as e:
            logger.warning(f"[STARTUP ERROR] {channel}: {e}")
    asyncio.create_task(auto_refresh_loop())

async def auto_refresh_loop():
    while True:
        for channel in CHANNELS:
            try:
                url = await fetch_stream_url(channel)
                set_cached_url(channel, url)
                logger.info(f"[AUTO REFRESH] {channel} updated.")
            except Exception as e:
                logger.warning(f"[AUTO REFRESH ERROR] {channel}: {e}")
        await asyncio.sleep(REFRESH_INTERVAL)

@app.get("/logs")
async def view_logs(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(security)
):
    """View recent change logs."""
    check_auth(credentials)
    logs = get_logs(100)
    return templates.TemplateResponse("logs.html", {"request": request, "logs": logs})

@app.get("/logs/json")
async def view_logs_json(credentials: HTTPBasicCredentials = Depends(security)):
    """Get logs as JSON."""
    check_auth(credentials)
    return get_logs(200)

@app.get("/stats")
async def view_stats(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(security)
):
    """View statistics about token and URL changes."""
    check_auth(credentials)
    token_stats = get_token_history()
    channel_stats = {}
    for ch in CHANNELS:
        channel_stats[ch] = get_url_history(ch)[-10:]
    return templates.TemplateResponse("stats.html", {
        "request": request,
        "token_stats": token_stats,
        "channel_stats": channel_stats,
        "channels": CHANNELS
    })

@app.get("/stats/json")
async def view_stats_json(credentials: HTTPBasicCredentials = Depends(security)):
    """Get stats as JSON."""
    check_auth(credentials)
    return {
        'token': get_token_history(),
        'channels': {ch: get_url_history(ch)[-10:] for ch in CHANNELS}
    }
