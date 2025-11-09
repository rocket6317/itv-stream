import httpx
from fastapi import HTTPException

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:126.0) Gecko/20100101 Firefox/126.0',
    'Accept': 'application/vnd.itv.online.playlist.sim.v3+json',
    'Accept-Language': 'en-GB,en;q=0.5',
    'Referer': 'https://www.itv.com/',
    'Origin': 'https://www.itv.com',
    'Content-Type': 'application/x-www-form-urlencoded',
}

COOKIES = {
    'SyrenisCookieFormConsent_Itv.Session': '{"tokens":{"content":{"entitlement":{"purchased":[],"source":"","failed_availability_checks":[]},"email_verified":true,"token_type":"bearer","missingUserData":["NoPlanSelected"]}}',
}

DATA = '{"user":{"itvUserId":"{4f129513-1f5b-4dc9-8a2a-b6434e93c938}","entitlements":[],"profile_id":"{4f129513-1f5b-4dc9-8a2a-b6434e93c938}_0"},"device":{"manufacturer":"Firefox","model":"126.0","os":{"name":"Mac OS","version":"10.15","type":"desktop"}},"client":{"version":"4.1","id":"browser","supportsAdPods":true,"service":"itv.x","appversion":"2.228.2"},"variantAvailability":{"player":"dash","featureset":{"min":["mpeg-dash","widevine"],"max":["mpeg-dash","widevine"]},"platformTag":"dotcom"}}'

async def fetch_stream_url(channel: str) -> str:
    async with httpx.AsyncClient(timeout=5) as client:
        try:
            response = await client.post(
                f"https://simulcast.itv.com/playlist/itvonline/{channel}",
                headers=HEADERS,
                cookies=COOKIES,
                data=DATA,
            )
            response.raise_for_status()
            return response.json()['Playlist']['Video']['VideoLocations'][0]['Url']
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Failed to fetch stream URL: {e}")
