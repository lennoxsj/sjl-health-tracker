"""
Loads dashboard data from synced JSON files in data/.
Falls back to mock data for any file not yet synced.
"""

import json
import os
from datetime import date
from src.dashboard import hard_code_data as mock
from src.scores.activity_metrics import steepness_index, grade_adjusted_pace

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")

_MIN_SLEEP_MINUTES = 30


def _load_json(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def _parse_dates(activities):
    for a in activities:
        if isinstance(a.get("date"), str):
            a["date"] = date.fromisoformat(a["date"])
    return activities


def _avg_values(*values):
    valid = [v for v in values if v is not None]
    return round(sum(valid) / len(valid), 1) if valid else None


# ── Activity log ───────────────────────────────────────────────────────────────

def _load_steps():
    """Load Garmin daily steps and return as activity-log-compatible dicts.
    Excludes today's entry since the step count is still accumulating."""
    raw = _load_json("garmin_steps.json") or []
    today = date.today()
    result = []
    for entry in raw:
        if not entry.get("steps"):
            continue
        if date.fromisoformat(entry["day"]) >= today:
            continue
        result.append({
            "name":             "Steps",
            "activity_type":    "steps",
            "source":           "garmin",
            "date":             date.fromisoformat(entry["day"]),
            "steps":            entry["steps"],
            "duration_minutes": None,
            "distance_km":      None,
            "elevation_m":      None,
            "avg_hr":           None,
            "avg_speed_kmh":    None,
            "avg_pace_per_100m": None,
            "zones4plus_minutes": None,
            "strength_type":    None,
            "weight_volume_kg": None,
            "back_squat_kg":    None,
            "load_score":       None,
            "strava_id":        None,
            "strava_url":       None,
        })
    return result


def load_activities():
    raw = _load_json("strava_activities.json")
    activities = _parse_dates(raw) if raw is not None else mock.activity_log
    activities += _load_steps()
    activities.sort(key=lambda a: a["date"], reverse=True)
    return activities


# ── Sleep & biometrics ─────────────────────────────────────────────────────────

def _valid_nights(data):
    """Filter out nights with insufficient sleep (ring not worn etc.)."""
    return [n for n in (data or []) if (n.get("total_minutes") or 0) >= _MIN_SLEEP_MINUTES]


def _build_sleep_and_biometrics():
    oura        = _valid_nights(_load_json("oura_sleep.json"))
    garmin      = _valid_nights(_load_json("garmin_sleep.json"))
    eight_sleep = _valid_nights(_load_json("eight_sleep_sleep.json"))

    if not oura and not garmin and not eight_sleep:
        return mock.last_night_sleep, mock.sleep_rolling, mock.last_night_biometrics, mock.rolling_7day_biometrics

    # Determine which sources have last-night data
    sources_available = {}
    if oura:
        sources_available["oura"]        = oura[0]
    if garmin:
        sources_available["garmin"]      = garmin[0]
    if eight_sleep:
        sources_available["eight_sleep"] = eight_sleep[0]

    active_sources = list(sources_available.keys())

    # ── Last night ─────────────────────────────────────────────────────────────
    # Sleep stages: average across all available sources
    def avg_field(field):
        return _avg_values(*[sources_available[s].get(field) for s in active_sources])

    # Interruptions: Eight Sleep only
    interrupted = (
        sources_available["eight_sleep"].get("interrupted_minutes")
        if "eight_sleep" in sources_available else None
    )

    last_night_sleep = {
        "total_minutes":       round(avg_field("total_minutes") or 0),
        "deep_minutes":        round(avg_field("deep_minutes")  or 0),
        "rem_minutes":         round(avg_field("rem_minutes")   or 0),
        "interrupted_minutes": interrupted,
        "sources":             active_sources,
    }

    # Breath rate: Eight Sleep preferred, Oura fallback (Garmin doesn't track it)
    breath_bpm = None
    if "eight_sleep" in sources_available:
        breath_bpm = sources_available["eight_sleep"].get("breath_bpm")
    if breath_bpm is None and "oura" in sources_available:
        breath_bpm = sources_available["oura"].get("breath_bpm")

    last_night_bio = {
        "rhr":        avg_field("rhr"),
        "hrv_ms":     avg_field("hrv_ms"),
        "breath_bpm": breath_bpm,
        "sources":    active_sources,
    }

    # ── Rolling averages — use only the same sources as last night ─────────────
    def rolling_avg(source_nights, field, n=7):
        valid = [v for v in [d.get(field) for d in source_nights[:n]] if v is not None]
        return round(sum(valid) / len(valid), 1) if valid else None

    sleep_rolling = {
        "total_minutes_avg": round(_avg_values(
            rolling_avg(oura,        "total_minutes") if "oura"        in active_sources else None,
            rolling_avg(garmin,      "total_minutes") if "garmin"      in active_sources else None,
            rolling_avg(eight_sleep, "total_minutes") if "eight_sleep" in active_sources else None,
        ) or 0),
        "deep_minutes_avg": round(_avg_values(
            rolling_avg(oura,        "deep_minutes") if "oura"        in active_sources else None,
            rolling_avg(garmin,      "deep_minutes") if "garmin"      in active_sources else None,
            rolling_avg(eight_sleep, "deep_minutes") if "eight_sleep" in active_sources else None,
        ) or 0),
        "rem_minutes_avg": round(_avg_values(
            rolling_avg(oura,        "rem_minutes") if "oura"        in active_sources else None,
            rolling_avg(garmin,      "rem_minutes") if "garmin"      in active_sources else None,
            rolling_avg(eight_sleep, "rem_minutes") if "eight_sleep" in active_sources else None,
        ) or 0),
        "interrupted_minutes_avg": (
            rolling_avg(eight_sleep, "interrupted_minutes")
            if "eight_sleep" in active_sources else None
        ),
        "nights": 7,
    }

    rolling_bio = {
        "rhr": _avg_values(
            rolling_avg(oura,        "rhr") if "oura"        in active_sources else None,
            rolling_avg(garmin,      "rhr") if "garmin"      in active_sources else None,
            rolling_avg(eight_sleep, "rhr") if "eight_sleep" in active_sources else None,
        ),
        "hrv_ms": _avg_values(
            rolling_avg(oura,        "hrv_ms") if "oura"        in active_sources else None,
            rolling_avg(garmin,      "hrv_ms") if "garmin"      in active_sources else None,
            rolling_avg(eight_sleep, "hrv_ms") if "eight_sleep" in active_sources else None,
        ),
        # Breath: Eight Sleep preferred, Oura fallback
        "breath_bpm": (
            rolling_avg(eight_sleep, "breath_bpm") if "eight_sleep" in active_sources
            else rolling_avg(oura,   "breath_bpm") if "oura"        in active_sources
            else None
        ),
        "sources": active_sources,
    }

    return last_night_sleep, sleep_rolling, last_night_bio, rolling_bio


# ── VO2 Max ────────────────────────────────────────────────────────────────────

def load_vo2_max():
    raw = _load_json("garmin_vo2.json")
    if not raw:
        return mock.vo2_max

    # Most recent value
    current = raw[0]["vo2_max"] if raw else None

    # Value closest to 30 days ago
    month_ago = None
    for entry in raw:
        d = date.fromisoformat(entry["day"])
        if (date.today() - d).days >= 28:
            month_ago = entry["vo2_max"]
            break

    if not current:
        return mock.vo2_max

    return {
        "current":        current,
        "one_month_ago":  month_ago or current,
    }


# ── Weight ─────────────────────────────────────────────────────────────────────

def load_body_composition():
    raw = _load_json("garmin_weight.json")
    if not raw:
        return mock.body_composition

    recent_3 = [e["weight_kg"] for e in raw[:3]]
    avg_weight = round(sum(recent_3) / len(recent_3), 1) if recent_3 else None

    comp = dict(mock.body_composition)
    if avg_weight:
        comp["weight_kg"]         = raw[0]["weight_kg"]
        comp["weight_3day_avg_kg"] = avg_weight
    return comp


# ── Goal progress ──────────────────────────────────────────────────────────────

def _quarter_dates(quarter_str):
    """Return (start, end) dates for a quarter string like 'Q2 2026 (Apr–Jun)'."""
    month_map = {
        "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4,  "May": 5,  "Jun": 6,
        "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
    }
    quarter_months = {
        "Q1": ("Jan", "Mar"), "Q2": ("Apr", "Jun"),
        "Q3": ("Jul", "Sep"), "Q4": ("Oct", "Dec"),
    }
    year = int(quarter_str.split()[1])
    q    = quarter_str.split()[0]
    start_mon, end_mon = quarter_months[q]
    start = date(year, month_map[start_mon], 1)
    end_m = month_map[end_mon]
    end   = date(year, end_m, [31,28,31,30,31,30,31,31,30,31,30,31][end_m - 1])
    return start, end


def load_goal_progress(activities, body_comp):
    """Compute live goal progress from Strava activities and Garmin weight."""
    goals    = {k: dict(v) if isinstance(v, dict) else v for k, v in mock.goals.items()}
    q_start, q_end = _quarter_dates(goals["quarter"])

    bike_types = {"road_bike", "gravel_bike", "mountain_bike"}

    # ── Accumulation goals ─────────────────────────────────────────────────────
    bike_dist = 0.0; bike_climb = 0.0; swim_dist = 0.0

    for a in activities:
        d = a["date"] if isinstance(a["date"], date) else date.fromisoformat(a["date"])
        if not (q_start <= d <= q_end):
            continue
        atype = a.get("activity_type")
        if atype in bike_types:
            bike_dist  += a.get("distance_km")  or 0
            bike_climb += a.get("elevation_m")  or 0
        elif atype == "swim":
            swim_dist  += a.get("distance_km")  or 0

    goals["biking_distance_km"]["progress"] = round(bike_dist, 1)
    goals["biking_climbing_m"]["progress"]  = round(bike_climb)
    goals["swim_distance_km"]["progress"]   = round(swim_dist, 2)

    # ── Road bike GAP — avg of last 5 rides with speed + distance ─────────────
    road_rides = [
        a for a in activities
        if a.get("activity_type") in ("road_bike", "gravel_bike")
        and a.get("avg_speed_kmh") and a.get("distance_km")
    ][:5]
    if road_rides:
        gaps = []
        for a in road_rides:
            si  = steepness_index(a.get("elevation_m") or 0, a["distance_km"])
            gaps.append(grade_adjusted_pace(a["avg_speed_kmh"], si))
        goals["road_bike_gap_kmh"]["progress"] = round(sum(gaps) / len(gaps), 1)

    # ── Swim pace — avg of last 3 swims with duration + distance ──────────────
    swims = [
        a for a in activities
        if a.get("activity_type") == "swim"
        and a.get("duration_minutes") and a.get("distance_km")
    ][:3]
    if swims:
        pace_secs = [
            (a["duration_minutes"] * 60) / (a["distance_km"] * 10)
            for a in swims
        ]
        avg_sec = sum(pace_secs) / len(pace_secs)
        m, s = divmod(int(avg_sec), 60)
        goals["swim_pace_per_100m"]["progress"] = f"{m}:{s:02d}"

    # ── Weight — most recent Garmin reading ───────────────────────────────────
    if body_comp.get("weight_kg"):
        goals["weight_kg"]["progress"] = body_comp["weight_kg"]

    return goals


# ── Back squat ─────────────────────────────────────────────────────────────────

def load_back_squat_kg():
    """Return most recent back squat (kg) from Strava activities, or None."""
    raw = _load_json("strava_activities.json")
    if not raw:
        return None
    for activity in raw:
        if activity.get("back_squat_kg"):
            return activity["back_squat_kg"]
    return None


# ── Master loader ──────────────────────────────────────────────────────────────

def load_all():
    last_night_sleep, sleep_rolling, last_night_bio, rolling_bio = _build_sleep_and_biometrics()
    activities  = load_activities()
    body_comp   = load_body_composition()

    # Build goals from real data
    goals = load_goal_progress(activities, body_comp)

    # Overlay live back squat from Strava descriptions
    back_squat = load_back_squat_kg()
    if back_squat is not None:
        goals["back_squat_kg"]["progress"] = back_squat

    return {
        "last_night_sleep":        last_night_sleep,
        "sleep_rolling":           sleep_rolling,
        "last_night_biometrics":   last_night_bio,
        "rolling_7day_biometrics": rolling_bio,
        "vo2_max":                 load_vo2_max(),
        "activity_log":            activities,
        "body_composition":        body_comp,
        "goals":                   goals,
        "FNS_HOURS":               mock.FNS_HOURS,
    }
