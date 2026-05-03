"""
Activity load scoring — bespoke point-based system.
See design/load_score_v2.md for the full specification.
"""

_KG_TO_LBS = 2.20462

# Activity types that have a steepness index (elevation / distance)
STEEPNESS_TYPES = {"road_bike", "gravel_bike", "mountain_bike", "run", "hike", "walk"}

# Activity types that get a grade-adjusted pace display
GRADE_ADJUSTED_PACE_TYPES = {"road_bike", "mountain_bike", "gravel_bike"}

CYCLING_TYPES = {"road_bike", "gravel_bike", "mountain_bike"}


def steepness_index(elevation_gain_m, distance_km):
    """
    Elevation gain (m) divided by distance (km), rounded to nearest whole number.
    Example: 814m / 57.65km = 14.
    """
    if not distance_km or distance_km <= 0:
        return None
    if not elevation_gain_m:
        return 0
    return round(elevation_gain_m / distance_km)


def grade_adjusted_pace(avg_speed_kmh, steepness):
    """
    Add 0.1 km/h per steepness point to average moving speed.
    Example: 25 km/h avg speed, steepness 14 → 26.4 km/h grade adjusted pace.
    """
    if steepness is None or avg_speed_kmh is None:
        return avg_speed_kmh
    return round(avg_speed_kmh + steepness * 0.1, 1)


def _hr_bonus(zones4plus_minutes, points_per_interval, interval_minutes):
    """Points from time spent above 80% max HR."""
    if zones4plus_minutes is None:
        return 0
    return (zones4plus_minutes / interval_minutes) * points_per_interval


def _pace_to_seconds(pace_str):
    """Convert 'M:SS' string to total seconds."""
    if not pace_str:
        return None
    try:
        parts = str(pace_str).split(":")
        return int(parts[0]) * 60 + int(parts[1])
    except (ValueError, IndexError):
        return None


def activity_load_score(
    duration_minutes,
    activity_type=None,
    distance_km=None,
    elevation_m=None,
    steps=None,
    zones4plus_minutes=None,
    max_hr=185,
    weight_volume_kg=None,        # stored in kg, converted internally to lbs
    rolling_avg_volume_lbs=None,  # rolling avg of previous 3 same-type workouts (lbs)
    strength_type=None,            # leg | push | pull | general
    swim_baseline_pace=None,       # "M:SS" per 100m
    avg_pace_per_100m=None,        # "M:SS" per 100m (computed from duration + distance)
):
    """
    Compute activity load score using a bespoke point-based system.
    Scores are uncapped — hard days genuinely score higher.

    See design/load_score_v2.md for full specification.
    """
    dur_hrs  = (duration_minutes or 0) / 60
    dist     = distance_km or 0
    si       = steepness_index(elevation_m or 0, dist) or 0

    # ── Road biking ────────────────────────────────────────────────────────────
    if activity_type == "road_bike":
        base = 20 * min(3, dur_hrs) + 25 * max(0, dur_hrs - 3)
        return round(base + si * dur_hrs + _hr_bonus(zones4plus_minutes, 1, 15))

    # ── Gravel biking ──────────────────────────────────────────────────────────
    if activity_type == "gravel_bike":
        base = 25 * min(2, dur_hrs) + 30 * max(0, dur_hrs - 2)
        return round(base + si * dur_hrs + _hr_bonus(zones4plus_minutes, 1, 15))

    # ── Mountain biking ────────────────────────────────────────────────────────
    if activity_type == "mountain_bike":
        base = 25 * min(2, dur_hrs) + 30 * max(0, dur_hrs - 2)
        return round(base + si * dur_hrs + _hr_bonus(zones4plus_minutes, 1, 15))

    # ── Running ────────────────────────────────────────────────────────────────
    if activity_type == "run":
        base = 8 * min(6, dist) + 10 * max(0, dist - 6)
        elev_bonus = (elevation_m or 0) / 15
        return round(base + elev_bonus + _hr_bonus(zones4plus_minutes, 2, 15))

    # ── Swimming ───────────────────────────────────────────────────────────────
    if activity_type == "swim":
        # 15 pts per 500m up to 2km, 20 pts per 500m beyond
        chunks_total = dist * 2          # number of 500m chunks
        chunks_base  = min(4, chunks_total)
        chunks_extra = max(0, chunks_total - 4)
        base = 15 * chunks_base + 20 * chunks_extra

        # Pace bonus: floor(seconds_faster / 10) pts per 100m swum
        pace_bonus = 0
        if swim_baseline_pace and avg_pace_per_100m:
            baseline_s = _pace_to_seconds(swim_baseline_pace)
            actual_s   = _pace_to_seconds(avg_pace_per_100m)
            if baseline_s and actual_s:
                seconds_faster = baseline_s - actual_s   # positive = faster
                increments = int(seconds_faster // 10)   # only full 10-sec intervals
                if increments > 0:
                    pace_bonus = increments * (dist * 10)  # pts × number of 100m

        return round(base + pace_bonus + _hr_bonus(zones4plus_minutes, 2, 15))

    # ── Walking and Hiking ─────────────────────────────────────────────────────
    if activity_type in ("walk", "hike"):
        base = 5 * min(8, dist) + 8 * max(0, dist - 8)
        elev_bonus = (elevation_m or 0) / 15
        return round(base + elev_bonus + _hr_bonus(zones4plus_minutes, 1, 15))

    # ── Rowing ─────────────────────────────────────────────────────────────────
    if activity_type == "row":
        base = 30 * min(2, dur_hrs) + 35 * max(0, dur_hrs - 2)
        return round(base + _hr_bonus(zones4plus_minutes, 2, 15))

    # ── Strength ───────────────────────────────────────────────────────────────
    if activity_type == "strength":
        base     = 30 * dur_hrs
        hr_pts   = zones4plus_minutes or 0   # 1 pt per minute above 80%

        # Volume bonus relative to rolling average of same type.
        # Only applies when there is prior history (rolling_avg_volume_lbs is not None).
        vol_bonus = 0
        if weight_volume_kg is not None and rolling_avg_volume_lbs is not None:
            vol_lbs = weight_volume_kg * _KG_TO_LBS
            avg_lbs = rolling_avg_volume_lbs
            excess  = max(0, vol_lbs - avg_lbs)
            if strength_type in ("leg", "pull"):
                vol_bonus = (excess / 1000) * 10
            elif strength_type in ("push", "general"):
                vol_bonus = (excess / 800) * 10

        return round(base + hr_pts + vol_bonus)

    # ── Steps ──────────────────────────────────────────────────────────────────
    if activity_type == "steps":
        return round((steps or 0) / 1000 * 2)

    # ── Yoga ───────────────────────────────────────────────────────────────────
    if activity_type == "yoga":
        return round(15 * dur_hrs + _hr_bonus(zones4plus_minutes, 3, 15))

    # ── Pilates ────────────────────────────────────────────────────────────────
    if activity_type == "pilates":
        return round(20 * dur_hrs + _hr_bonus(zones4plus_minutes, 3, 15))

    # ── Stretch / Mobility ─────────────────────────────────────────────────────
    if activity_type == "stretch_mobility":
        return round(5 * dur_hrs)

    # ── Misc / fallback ────────────────────────────────────────────────────────
    base = 20 * dur_hrs
    return round(base + _hr_bonus(zones4plus_minutes, 3, 10))
