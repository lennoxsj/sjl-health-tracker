"""
Eight Sleep ingest module.

Uses Eight Sleep's OAuth2 API (auth-api.8slp.net) with Bearer token auth.
The old /v1/login session token approach was deprecated; this uses the
OAuth2 password grant with the known client credentials from the
lukas-clarke/eight_sleep Home Assistant integration.
"""

import os
import requests
import time
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv()

_AUTH_URL       = "https://auth-api.8slp.net/v1/tokens"
_CLIENT_API_URL = "https://client-api.8slp.net/v1"
_CLIENT_ID      = "0894c7f33bb94800a03f1f4df13a4f38"
_CLIENT_SECRET  = "f0954a3ed5763ba3d06834c73731a32f15f168f47d4f164751275def86db0c76"

_DEFAULT_HEADERS = {
    "content-type": "application/json",
    "user-agent":   "okhttp/4.9.3",
    "accept":       "application/json",
}

# Simple in-process token cache (token, expiry_epoch)
_token_cache: tuple[str, float] | None = None


def _get_token() -> tuple[str, str]:
    """Return (access_token, user_id), refreshing if needed."""
    global _token_cache

    if _token_cache:
        token, user_id, expiry = _token_cache
        if time.time() + 120 < expiry:   # 2-minute buffer
            return token, user_id

    resp = requests.post(_AUTH_URL, json={
        "client_id":     _CLIENT_ID,
        "client_secret": _CLIENT_SECRET,
        "grant_type":    "password",
        "username":      os.environ["EIGHT_SLEEP_EMAIL"],
        "password":      os.environ["EIGHT_SLEEP_PASSWORD"],
    }, headers=_DEFAULT_HEADERS, timeout=30)
    resp.raise_for_status()

    data      = resp.json()
    token     = data["access_token"]
    user_id   = data["userId"]
    expires_in = data.get("expires_in", 86400)
    expiry    = time.time() + expires_in
    _token_cache = (token, user_id, expiry)
    return token, user_id


def _auth_headers() -> dict:
    token, _ = _get_token()
    return {**_DEFAULT_HEADERS, "authorization": f"Bearer {token}"}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _avg(values: list[float]) -> float | None:
    valid = [v for v in values if v is not None]
    return round(sum(valid) / len(valid), 1) if valid else None


def _interval_to_night(iv: dict) -> dict | None:
    """Parse a single Eight Sleep interval into our normalised sleep dict."""
    ss = iv.get("stageSummary", {})

    sleep_s = ss.get("sleepDuration", 0) or 0
    if sleep_s < 1800:   # < 30 minutes — skip
        return None

    # ── Sleep stages ───────────────────────────────────────────────────────────
    total_min = round(sleep_s / 60)
    deep_min  = round((ss.get("deepDuration",  0) or 0) / 60)
    rem_min   = round((ss.get("remDuration",   0) or 0) / 60)
    # Wake After Sleep Onset (interruptions during the night)
    waso_min  = round((ss.get("wasoDuration",  0) or 0) / 60)

    # ── Biometrics from timeseries ─────────────────────────────────────────────
    ts = iv.get("timeseries", {})

    # RMSSD HRV — filter obvious outliers (first reading often huge)
    rmssd_vals = [v[1] for v in ts.get("rmssd", []) if 10 < v[1] < 300]
    hrv_ms = _avg(rmssd_vals)

    # RHR — minimum valid heart rate reading
    hr_vals = [v[1] for v in ts.get("heartRate", []) if 30 < v[1] < 150]
    rhr = round(min(hr_vals)) if hr_vals else None

    # Respiratory rate — average across the night
    rr_vals = [v[1] for v in ts.get("respiratoryRate", []) if v[1]]
    breath_bpm = _avg(rr_vals)

    # ── Date — use ts field (interval start, local-ish date) ──────────────────
    day = iv["ts"][:10]   # "YYYY-MM-DD"

    return {
        "day":                 day,
        "total_minutes":       total_min,
        "deep_minutes":        deep_min,
        "rem_minutes":         rem_min,
        "interrupted_minutes": waso_min,
        "rhr":                 rhr,
        "hrv_ms":              hrv_ms,
        "breath_bpm":          breath_bpm,
    }


# ── Public API ─────────────────────────────────────────────────────────────────

def fetch_sleep(days_back: int = 30) -> list[dict]:
    """
    Fetch nightly sleep data from Eight Sleep.

    Returns list of dicts (newest first):
        day, total_minutes, deep_minutes, rem_minutes,
        interrupted_minutes, rhr, hrv_ms, breath_bpm
    """
    _, user_id = _get_token()
    h = _auth_headers()

    # Fetch paginated intervals until we have enough days
    all_intervals: list[dict] = []
    url    = f"{_CLIENT_API_URL}/users/{user_id}/intervals"
    params = {}

    while True:
        resp = requests.get(url, headers=h, params=params, timeout=30)
        resp.raise_for_status()
        payload   = resp.json()
        intervals = payload.get("intervals", [])
        if not intervals:
            break
        all_intervals.extend(intervals)

        # Check if oldest fetched interval is still within our window
        oldest_day = all_intervals[-1]["ts"][:10]
        cutoff     = (date.today() - timedelta(days=days_back)).isoformat()
        if oldest_day <= cutoff:
            break

        # Paginate using the cursor
        cursor = payload.get("next")
        if not cursor:
            break
        params = {"next": cursor}

    nights = []
    for iv in all_intervals:
        night = _interval_to_night(iv)
        if night and night["day"] >= (date.today() - timedelta(days=days_back)).isoformat():
            nights.append(night)

    return sorted(nights, key=lambda n: n["day"], reverse=True)
