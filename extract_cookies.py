#!/usr/bin/env python3
"""
ITV Cookie Extractor for Safari on macOS

This script extracts ITV cookies from Safari after you've logged into itvx.com
in your browser. The extracted cookies can be added to your stack.env file.

Usage:
    python3 extract_cookies.py

Instructions:
    1. Open Safari and go to https://www.itv.com/
    2. Log in to your ITVX account
    3. Run this script
    4. Copy the output to your stack.env file on your DietPi
"""

import os
import sqlite3
import subprocess
from pathlib import Path
from urllib.parse import urlparse
import httpx

def get_safari_cookies():
    """Extract cookies from Safari on macOS."""
    cookie_path = Path.home() / "Library" / "Cookies" / "Cookies.binarycookies"

    if not cookie_path.exists():
        print("❌ Safari cookies not found!")
        print(f"   Looking for: {cookie_path}")
        return None

    print("⚠️  Safari uses BinaryCookies format which requires special tools.")
    print("   Please use Chrome or Firefox instead, or manually extract cookies:")
    print()
    print("   Manual extraction:")
    print("   1. Open Safari > Settings > Privacy > Manage Website Data")
    print("   2. Search for 'itv.com'")
    print("   3. Select and copy the cookie values")
    return None


def get_chrome_cookies():
    """Extract cookies from Chrome on macOS."""
    # Chrome stores cookies in different locations based on the Chrome variant
    possible_paths = [
        Path.home() / "Library" / "Application Support" / "Google" / "Chrome" / "Default" / "Cookies",
        Path.home() / "Library" / "Application Support" / "Google" / "Chrome" / "Profile 1" / "Cookies",
    ]

    for cookie_path in possible_paths:
        if cookie_path.exists():
            return extract_cookies_from_db(cookie_path, "Chrome")

    print("❌ Chrome cookies not found!")
    print("   Looking in:")
    for p in possible_paths:
        print(f"   - {p}")
    return None


def get_firefox_cookies():
    """Extract cookies from Firefox on macOS."""
    firefox_base = Path.home() / "Library" / "Application Support" / "Firefox" / "Profiles"

    if not firefox_base.exists():
        print("❌ Firefox not found!")
        return None

    # Find the default profile
    profiles = list(firefox_base.glob("*.default*"))
    if not profiles:
        print("❌ No Firefox profile found!")
        return None

    cookie_path = profiles[0] / "cookies.sqlite"
    if cookie_path.exists():
        return extract_cookies_from_db(cookie_path, "Firefox")

    print("❌ Firefox cookies not found!")
    return None


def extract_cookies_from_db(cookie_path, browser_name):
    """Extract cookies from a SQLite database."""
    # Chrome stores cookies in encrypted format on macOS
    # Firefox stores them in plain text

    print(f"🔍 Found {browser_name} cookies at: {cookie_path}")

    # Make a temporary copy since the DB might be locked
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
        tmp_path = tmp.name

    try:
        subprocess.run(["cp", str(cookie_path), tmp_path], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("❌ Could not copy cookie database (browser might be running)")
        return None

    try:
        conn = sqlite3.connect(tmp_path)
        cursor = conn.cursor()

        # Firefox schema: moz_cookies
        # Chrome schema: cookies

        try:
            # Try Firefox schema first
            cursor.execute("""
                SELECT name, value, host
                FROM moz_cookies
                WHERE host LIKE '%itv.com%'
                OR host LIKE '%itvx.co%'
            """)
            rows = cursor.fetchall()
        except sqlite3.OperationalError:
            # Try Chrome schema
            try:
                cursor.execute("""
                    SELECT name, value, host_key
                    FROM cookies
                    WHERE host_key LIKE '%itv.com%'
                    OR host_key LIKE '%itvx.co%'
                """)
                rows = cursor.fetchall()
            except sqlite3.OperationalError:
                print("❌ Could not read cookies from database")
                return None

        conn.close()

        if not rows:
            print("⚠️  No ITV cookies found!")
            print("   Make sure you're logged into https://www.itv.com/ in your browser")
            return None

        cookies = {}
        for row in rows:
            name, value, host = row[0], row[1], row[2]
            cookies[name] = value

        return cookies

    finally:
        os.unlink(tmp_path)


def test_cookies(cookies):
    """Test if cookies work with ITV API."""
    print()
    print("🧪 Testing cookies with ITV API...")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:126.0) Gecko/20100101 Firefox/126.0',
        'Accept': 'application/vnd.itv.online.playlist.sim.v3+json',
        'Accept-Language': 'en-GB,en;q=0.5',
        'Referer': 'https://www.itv.com/',
        'Origin': 'https://www.itv.com',
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    data = '{"user":{"itvUserId":"{4f129513-1f5b-4dc9-8a2a-b6434e93c938}","entitlements":[],"profile_id":"{4f129513-1f5b-4dc9-8a2a-b6434e93c938}_0"},"device":{"manufacturer":"Firefox","model":"126.0","os":{"name":"Mac OS","version":"10.15","type":"desktop"}},"client":{"version":"4.1","id":"browser","supportsAdPods":true,"service":"itv.x","appversion":"2.228.2"},"variantAvailability":{"player":"dash","featureset":{"min":["mpeg-dash","widevine"],"max":["mpeg-dash","widevine"]},"platformTag":"dotcom"}}'

    try:
        response = httpx.post(
            "https://simulcast.itv.com/playlist/itvonline/ITV",
            headers=headers,
            cookies=cookies,
            data=data,
            timeout=10
        )

        if response.status_code == 200:
            print("✅ Cookies work! ITV API returned 200 OK")
            return True
        else:
            print(f"❌ Cookies don't work. Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Error testing cookies: {e}")
        return False


def format_cookies_for_env(cookies):
    """Format cookies for the .env file."""
    print()
    print("=" * 60)
    print("📋 ADD THESE TO YOUR stack.env FILE:")
    print("=" * 60)
    print()

    for name, value in cookies.items():
        # Escape special characters for .env file
        safe_value = value.replace('"', '\\"')
        print(f'ITV_COOKIE_{name}="{safe_value}"')

    print()
    print("=" * 60)
    print("⚙️  INSTRUCTIONS:")
    print("=" * 60)
    print("1. Copy the lines above")
    print("2. Add them to your stack.env file on your DietPi")
    print("3. Restart the container")
    print()


def main():
    print("=" * 60)
    print("🍪 ITV Cookie Extractor")
    print("=" * 60)
    print()
    print("Please make sure you're logged into https://www.itv.com/")
    print("in your browser before running this script.")
    print()

    # Try Firefox first (easiest - plain text cookies)
    print("🔍 Checking Firefox...")
    cookies = get_firefox_cookies()

    if not cookies:
        print()
        print("🔍 Checking Chrome...")
        cookies = get_chrome_cookies()

    if not cookies:
        print()
        print("🔍 Checking Safari...")
        get_safari_cookies()
        return

    print()
    print(f"✅ Found {len(cookies)} ITV cookies:")
    for name in cookies.keys():
        print(f"   - {name}")

    # Test cookies
    if test_cookies(cookies):
        format_cookies_for_env(cookies)
    else:
        print()
        print("⚠️  Cookies were found but don't seem to work with the ITV API.")
        print("   Possible reasons:")
        print("   - You're not logged into itvx.com")
        print("   - Cookies have expired")
        print("   - You're outside the UK")
        print()
        print("   You can still try adding them to your .env file.")


if __name__ == "__main__":
    main()
