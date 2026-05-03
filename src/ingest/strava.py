# GIT PUBLIC REPO

import os
import re
import time
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

_TOKEN_URL = "https://www.strava.com/oauth/token"
_API_BASE  = "https://www.strava.com/api/v3"

SPORT_TYPE_MAP = {
    "Ride":              "road_bike",
    "GravelRide":        "gravel_bike",
    "MountainBikeRide":  "mountain_bike",
    "Run":               "run",
    "TrailRun":          "run",
    "Hike":              "hike",
    "Walk":              "walk",
    "Swim":              "swim",
    "Rowing":            "row",
    "WeightTraining":    "strength",
    "Workout":           "misc",
    "Yoga":              "yoga",
    "Pilates":           "pilates",
    "PhysicalTherapy":   "stretch_mobility",
}


def _get_access_token():
    resp = requests.post(_TOKEN_URL, data={
        "client_id":     os.environ["STRAVA_CLIENT_ID"],
        "client_secret": os.environ["STRAVA_CLIENT_SECRET"],
        "refresh_token": os.environ["STRAVA_REFRESH_TOKEN"],
        "grant_type":    "refresh_token",
    })
    resp.raise_for_status()
    return resp.json()["access_token"]


def _activity_to_dict(raw):
    sport_type = raw.get("sport_type") or raw.get("type", "")
    activity_type = SPORT_TYPE_MAP.get(sport_type)
    if activity_type is None:
        return None  # skip unsupported types

    start_local = raw.get("start_date_local", "")
    try:
        activity_date = datetime.fromisoformat(start_local.replace("Z", "")).date()
    except (ValueError, AttributeError):
        return None

    distance_m   = raw.get("distance") or 0
    elevation_m  = raw.get("total_elevation_gain")
    avg_speed_ms = raw.get("average_speed")
    avg_hr       = raw.get("average_heartrate")
    moving_time  = raw.get("moving_time") or 0

    activity_id = raw["id"]
    name        = raw.get("name", "Activity")

    # Parse strength metadata from activity name
    strength_parsed = _parse_strength_description(name) if activity_type == "strength" else {}

    # Compute swim pace per 100m if distance and duration available
    avg_pace_per_100m = None
    if activity_type == "swim" and distance_m and moving_time:
        pace_sec = (moving_time / 60) * 60 / ((distance_m / 1000) * 10)
        m, s = divmod(int(pace_sec), 60)
        avg_pace_per_100m = f"{m}:{s:02d}"

    return {
        "strava_id":            activity_id,
        "strava_url":           f"https://www.strava.com/activities/{activity_id}",
        "name":                 name,
        "activity_type":        activity_type,
        "source":               "strava",
        "date":                 activity_date,
        "duration_minutes":     round(moving_time / 60, 1),
        "distance_km":          round(distance_m / 1000, 2) if distance_m else None,
        "elevation_m":          round(elevation_m, 1) if elevation_m is not None else None,
        "avg_hr":               round(avg_hr) if avg_hr else None,
        "avg_speed_kmh":        round(avg_speed_ms * 3.6, 2) if avg_speed_ms else None,
        "avg_pace_per_100m":    avg_pace_per_100m,
        "zones4plus_minutes": None,   # populated after zone fetch
        "strength_type":        strength_parsed.get("strength_type"),
        "weight_volume_kg":     strength_parsed.get("weight_volume_kg"),
        "back_squat_kg":        strength_parsed.get("back_squat_kg"),
        "load_score":           None,
    }


_LBS_TO_KG = 0.453592

_STRENGTH_TYPE_MAP = {
    "leg":     "leg",
    "push":    "push",
    "pull":    "pull",
    "general": "general",
}


def _parse_strength_description(description):
    """Parse a strength workout description in the format:
        Leg strength, volume: 12450lbs, back squat: 185lbs
        Push day strength, volume: 8320lbs
        Pull day strength, volume: 9150lbs
        General strength, volume: 7200lbs

    Returns a dict with:
        strength_type     : "leg" | "push" | "pull" | "general" | None
        weight_volume_kg  : float | None  (converted from lbs)
        back_squat_kg     : float | None  (converted from lbs, if present)
        
    Note for later: Volume data comes from MyFitBod. MFB does not have an API. 
    Adding metrics into Strava isn't ideal. Ask MyFitBod about possible API rollout."""
    
    if not description:
        return {"strength_type": None, "weight_volume_kg": None, "back_squat_kg": None}

    desc = description.lower()

    # Workout type
    strength_type = None
    for key in _STRENGTH_TYPE_MAP:
        if key in desc:
            strength_type = _STRENGTH_TYPE_MAP[key]
            break

    # Volume — "volume: 12,450lbs" or "volume: 12450lbs"
    volume_kg = None
    m = re.search(r"volume\s*:\s*([\d,]+)\s*lbs", desc)
    if m:
        lbs = float(m.group(1).replace(",", ""))
        volume_kg = round(lbs * _LBS_TO_KG, 1)

    # Back squat — "back squat: 185lbs"
    back_squat_kg = None
    m = re.search(r"back\s+squat\s*:\s*([\d,]+)\s*lbs", desc)
    if m:
        lbs = float(m.group(1).replace(",", ""))
        back_squat_kg = round(lbs * _LBS_TO_KG, 1)

    return {
        "strength_type":    strength_type,
        "weight_volume_kg": volume_kg,
        "back_squat_kg":    back_squat_kg,
    }


def _fetch_zones4plus_minutes(activity_id, headers, max_hr=185):
    """Fetch HR zone data for an activity and return minutes in Zone 4+.

    Counts time in any zone that:
      - zone position >= 4 (1-based), i.e. the 4th zone or higher in Strava's
        list — catches custom 6- and 7-zone configs explicitly
      - zone min bpm >= 80% of max HR (bpm-threshold fallback for standard zones)

    Returns None if zone data not available."""

    try:
        resp = requests.get(
            f"{_API_BASE}/activities/{activity_id}/zones",
            headers=headers,
            timeout=10,
        )
        if resp.status_code != 200:
            return None
        # Response is a list; find the heartrate entry
        zone_list = resp.json()
        hr_data   = next((z for z in zone_list if z.get("type") == "heartrate"), None)
        if not hr_data:
            return None
        buckets = hr_data.get("distribution_buckets", [])
        if not buckets:
            return None
        threshold_bpm = max_hr * 0.80
        seconds_above = sum(
            b["time"] for i, b in enumerate(buckets)
            if i >= 3 or b.get("min", 0) >= threshold_bpm  # zone 4+ by position or bpm
        )
        return round(seconds_above / 60, 1)
    except Exception:
        return None


def fetch_activities(days_back=90):
    """Fetch activities from Strava for the past `days_back` days.

    For strength workouts, fetches the full activity detail to extract
    a vol:XXXX tag from the description (total weight volume in kg).

    Returns list of activity dicts in the dashboard's internal format. 
    Unsupported activity types skipped."""

    access_token = _get_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}
    after_ts = int(time.time()) - days_back * 86400

    activities = []
    page = 1
    while True:
        resp = requests.get(
            f"{_API_BASE}/athlete/activities",
            headers=headers,
            params={"after": after_ts, "per_page": 100, "page": page},
        )
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        for raw in batch:
            parsed = _activity_to_dict(raw)
            if parsed:
                activities.append((parsed, raw["id"]))
        if len(batch) < 100:
            break
        page += 1

    # Fetch HR zone data for activities that have heart rate
    result = []
    for activity, activity_id in activities:
        if activity.get("avg_hr") is not None:
            activity["zones4plus_minutes"] = _fetch_zones4plus_minutes(
                activity_id, headers
            )
        result.append(activity)

    return sorted(result, key=lambda a: a["date"], reverse=True)
