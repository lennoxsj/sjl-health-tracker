import os
import requests
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv()

_API_BASE = "https://api.ouraring.com/v2/usercollection"


def _headers():
    return {"Authorization": f"Bearer {os.environ['OURA_TOKEN']}"}


def _get(endpoint, start_date, end_date):
    resp = requests.get(
        f"{_API_BASE}/{endpoint}",
        headers=_headers(),
        params={"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
    )
    resp.raise_for_status()
    return resp.json().get("data", [])


def fetch_sleep(days_back=30):
    """
    Fetch nightly sleep data from Oura.

    Returns a list of dicts keyed by date, newest first:
        day, total_minutes, deep_minutes, rem_minutes,
        interrupted_minutes, rhr, hrv_ms, breath_bpm
    """
    end   = date.today() + timedelta(days=1)
    start = end - timedelta(days=days_back)
    raw   = _get("sleep", start, end)

    nights = []
    for r in raw:
        if r.get("type") == "deleted":
            continue
        nights.append({
            "day":           r["day"],
            "total_minutes": round((r.get("total_sleep_duration") or 0) / 60),
            "deep_minutes":  round((r.get("deep_sleep_duration")  or 0) / 60),
            "rem_minutes":   round((r.get("rem_sleep_duration")   or 0) / 60),
            # interrupted_minutes intentionally omitted — Eight Sleep only
            "rhr":           r.get("lowest_heart_rate"),
            "hrv_ms":        r.get("average_hrv"),
            "breath_bpm":    r.get("average_breath"),
        })

    return sorted(nights, key=lambda n: n["day"], reverse=True)
