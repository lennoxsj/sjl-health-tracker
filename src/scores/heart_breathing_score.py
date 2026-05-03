# GIT PUBLIC REPO

"""Calculates the Cardiovascular score which is used for the Mettle Index"""

def _interpolate(value, points):
    """Linear interpolation between a list of (x, y) points."""
    if value <= points[0][0]:
        return points[0][1]
    if value >= points[-1][0]:
        return points[-1][1]
    for i in range(len(points) - 1):
        x0, y0 = points[i]
        x1, y1 = points[i + 1]
        if x0 <= value <= x1:
            t = (value - x0) / (x1 - x0)
            return round(y0 + t * (y1 - y0))
    return points[-1][1]

def _rhr_score(last_night_rhr, rolling_avg_rhr):
    """Score 0-100 based on last night's RHR vs. 7-day rolling average.
    delta = last_night - rolling_avg (positive means elevated)"""
    delta = last_night_rhr - rolling_avg_rhr
    points = [
        (-30, 0),
        (-5,  100),
        (+5,  80),
        (+20, 0),
    ]
    return _interpolate(delta, points)


def _hrv_score(hrv_ms):
    """Score 0-100 based on last night's HRV in milliseconds."""
    if hrv_ms > 120:
        return 0
    points = [
        (0,   0),
        (60,  60),
        (70,  100),
        (90,  100),
        (120, 50),
    ]
    return _interpolate(hrv_ms, points)


def _breath_score(breath_bpm):
    """Score 0-100 based on last night's respiratory rate in breaths per minute."""
    if breath_bpm >= 40:
        return 0
    points = [
        (0,  0),
        (13, 100),
        (15, 100),
        (20, 80),
        (40, 0),
    ]
    return _interpolate(breath_bpm, points)


def heart_breathing_score(last_night_rhr, rolling_avg_rhr, hrv_ms, breath_bpm):
    """Compute the Heart and Breathing Score (0-100).

    Args:
        last_night_rhr: Last night's resting heart rate (bpm).
        rolling_avg_rhr: 7-day rolling average resting heart rate (bpm), matched to available sources.
        hrv_ms: Last night's HRV (milliseconds).
        breath_bpm: Last night's respiratory rate (breaths per minute).

    Returns:
        dict with 'score' (int) and component scores and weights.

    Now called Cardiorespiratory score-- need to update this throughout code."""
    components = {
        "resting_heart_rate": {"score": _rhr_score(last_night_rhr, rolling_avg_rhr), "weight": 1/3},
        "hrv":                {"score": _hrv_score(hrv_ms),                           "weight": 1/3},
        "breath_rate":        {"score": _breath_score(breath_bpm),                    "weight": 1/3},
    }

    score = round(sum(c["score"] * c["weight"] for c in components.values()))
    return {"score": score, "components": components}
