"""Mock data for dashboard development. Replace with real ingested data later."""

from datetime import datetime, date

# ── Sleep ──────────────────────────────────────────────────────────────────────

FNS_HOURS = 8.5

last_night_sleep = {
    "total_minutes": 462,       # 7h 42m
    "deep_minutes": 98,
    "rem_minutes": 102,
    "interrupted_minutes": 8,
    "sources": ["eight_sleep", "oura"],
}

sleep_rolling = {
    "total_minutes_avg": 471,
    "deep_minutes_avg": 94,
    "rem_minutes_avg": 108,
    "interrupted_minutes_avg": 12,
    "nights": 7,
}

# ── Heart & Breathing ──────────────────────────────────────────────────────────

last_night_biometrics = {
    "rhr": 51,
    "hrv_ms": 78,
    "breath_bpm": 14.2,
    "sources": ["eight_sleep", "oura", "garmin"],
}

rolling_7day_biometrics = {
    "rhr": 54,
    "hrv_ms": 72,
    "breath_bpm": 14.8,
    "sources": ["eight_sleep", "oura", "garmin"],
}

# ── VO2 Max ────────────────────────────────────────────────────────────────────

vo2_max = {
    "current": 47.0,
    "one_month_ago": 46.0,
}

# ── Activity Log ───────────────────────────────────────────────────────────────

activity_log = [
    {
        "date": date(2026, 4, 30),
        "name": "Morning Run",
        "activity_type": "run",
        "source": "strava",
        "strava_url": "https://www.strava.com/activities/1000000001",
        "duration_minutes": 52,
        "distance_km": 9.2,
        "elevation_m": 84,
        "avg_hr": 148,
        "load_score": None,
    },
    {
        "date": date(2026, 4, 29),
        "name": "Strength – Push",
        "activity_type": "strength",
        "source": "strava",
        "strava_url": "https://www.strava.com/activities/1000000002",
        "duration_minutes": 65,
        "distance_km": None,
        "elevation_m": None,
        "avg_hr": 122,
        "weight_volume_kg": 4800,
        "load_score": None,
    },
    {
        "date": date(2026, 4, 28),
        "name": "Road Ride",
        "activity_type": "road_bike",
        "source": "strava",
        "strava_url": "https://www.strava.com/activities/1000000003",
        "duration_minutes": 148,
        "distance_km": 57.65,
        "elevation_m": 814,
        "avg_hr": 141,
        "avg_speed_kmh": 23.4,
        "load_score": None,
    },
    {
        "date": date(2026, 4, 27),
        "name": "Easy Run",
        "activity_type": "run",
        "source": "strava",
        "strava_url": "https://www.strava.com/activities/1000000004",
        "duration_minutes": 38,
        "distance_km": 6.1,
        "elevation_m": 40,
        "avg_hr": 132,
        "load_score": None,
    },
    {
        "date": date(2026, 4, 26),
        "name": "Strength – Legs",
        "activity_type": "strength",
        "source": "strava",
        "strava_url": "https://www.strava.com/activities/1000000005",
        "duration_minutes": 70,
        "distance_km": None,
        "elevation_m": None,
        "avg_hr": 128,
        "weight_volume_kg": 6200,
        "load_score": None,
    },
    {
        "date": date(2026, 4, 25),
        "name": "Gravel Ride",
        "activity_type": "gravel_bike",
        "source": "strava",
        "strava_url": "https://www.strava.com/activities/1000000006",
        "duration_minutes": 195,
        "distance_km": 68.3,
        "elevation_m": 1240,
        "avg_hr": 138,
        "avg_speed_kmh": 21.0,
        "load_score": None,
    },
    {
        "date": date(2026, 4, 24),
        "name": "Swim",
        "activity_type": "swim",
        "source": "strava",
        "strava_url": "https://www.strava.com/activities/1000000007",
        "duration_minutes": 45,
        "distance_km": 1.8,
        "elevation_m": None,
        "avg_hr": 135,
        "load_score": None,
    },
    {
        "date": date(2026, 4, 30),
        "name": "Steps",
        "activity_type": "steps",
        "source": "garmin",
        "steps": 5800,
        "duration_minutes": 50,
        "distance_km": None,
        "elevation_m": None,
        "avg_hr": None,
        "load_score": None,
    },
    {
        "date": date(2026, 4, 29),
        "name": "Steps",
        "activity_type": "steps",
        "source": "garmin",
        "steps": 7200,
        "duration_minutes": 60,
        "distance_km": None,
        "elevation_m": None,
        "avg_hr": None,
        "load_score": None,
    },
    {
        "date": date(2026, 4, 28),
        "name": "Steps",
        "activity_type": "steps",
        "source": "garmin",
        "steps": 4100,
        "duration_minutes": 35,
        "distance_km": None,
        "elevation_m": None,
        "avg_hr": None,
        "load_score": None,
    },
]

# ── Body Composition ───────────────────────────────────────────────────────────

body_composition = {
    "weight_kg": 68.4,
    "weight_3day_avg_kg": 68.6,
    "body_fat_kg": 22.8,   # from last DEXA scan
    "lean_mass_kg": 46.0,  # from last DEXA scan
    "last_dexa_date": date(2026, 1, 1),
}

# ── Goals (Q2 2026: April–June) ────────────────────────────────────────────────

goals = {
    "quarter": "Q2 2026 (Apr–Jun)",
    # Accumulation goals (one-way: progress toward target from zero)
    "biking_distance_km": {
        "target": 1300,
        "progress": 312.0,
    },
    "biking_climbing_m": {
        "target": 13000,
        "progress": 4820,
    },
    "swim_distance_km": {
        "target": 26.0,
        "progress": 5.4,
    },
    # Two-way goals (baseline from end of Q1 2026, progress toward target)
    "road_bike_gap_kmh": {
        "baseline": 21.0,   # end of Q1 2026
        "target": 22.0,
        "progress": 23.4,   # avg of last 3 road rides; higher is better
        "higher_is_better": True,
    },
    "swim_pace_per_100m": {
        "baseline": "2:35", # end of Q1 2026; lower (faster) is better
        "target": "2:30",
        "progress": "2:28",
        "higher_is_better": False,
    },
    "back_squat_kg": {
        "baseline": 34.0,   # end of Q1 2026
        "target": 40.8,     # 90 lbs
        "progress": 34.0,
        "higher_is_better": True,
    },
    "weight_kg": {
        "baseline": 69.5,   # end of Q1 2026
        "target": 68.0,
        "progress": 68.6,
        "higher_is_better": False,
    },
    "body_fat_kg": {
        "baseline": 22.8,   # end of Q1 2026
        "target": 19.0,
        "progress": 22.8,
        "higher_is_better": False,
    },
    "lean_mass_kg": {
        "baseline": 46.0,   # end of Q1 2026
        "target": 47.0,
        "progress": 46.25,
        "higher_is_better": True,
    },
}
