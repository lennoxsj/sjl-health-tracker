"""
Sync script — fetch data from all sources and save to data/.

Run manually each morning after getting up:
    python3 sync.py

Also scheduled to run automatically at 9am via cron (set up separately).
"""

import json
import os
from datetime import date, datetime
from src.ingest.strava import fetch_activities
from src.ingest.oura import fetch_sleep as fetch_oura_sleep
from src.ingest.eight_sleep import fetch_sleep as fetch_eight_sleep
from src.ingest.garmin import (
    fetch_sleep as fetch_garmin_sleep,
    fetch_steps as fetch_garmin_steps,
    fetch_weight as fetch_garmin_weight,
    fetch_vo2_max as fetch_garmin_vo2,
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def _json_serial(obj):
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def _save(filename, data):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=_json_serial)
    print(f"  Saved {len(data) if isinstance(data, list) else '1'} record(s) → {filename}")


def sync_strava():
    print("Fetching Strava activities (rolling 6 months)...")
    activities = fetch_activities(days_back=180)
    _save("strava_activities.json", activities)
    return activities


def sync_oura():
    print("Fetching Oura sleep data (last 30 days)...")
    nights = fetch_oura_sleep(days_back=30)
    _save("oura_sleep.json", nights)
    return nights


def sync_eight_sleep():
    print("Fetching Eight Sleep data (last 30 days)...")
    nights = fetch_eight_sleep(days_back=30)
    _save("eight_sleep_sleep.json", nights)
    return nights


def sync_garmin():
    print("Fetching Garmin data...")
    _save("garmin_sleep.json",  fetch_garmin_sleep(days_back=30))
    _save("garmin_steps.json",  fetch_garmin_steps(days_back=30))
    _save("garmin_weight.json", fetch_garmin_weight(days_back=90))
    _save("garmin_vo2.json",    fetch_garmin_vo2(days_back=90))


if __name__ == "__main__":
    print(f"=== Sync started at {datetime.now().strftime('%Y-%m-%d %H:%M')} ===")
    os.makedirs(DATA_DIR, exist_ok=True)

    sync_strava()
    sync_oura()
    sync_eight_sleep()
    sync_garmin()

    print("=== Sync complete ===")
