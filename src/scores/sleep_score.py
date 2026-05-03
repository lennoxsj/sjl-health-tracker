def _interpolate(value, points):
    """Linear interpolation between a sorted list of (x, y) control points, clamped at ends."""
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


def _total_sleep_score(total_minutes, fns_minutes):
    """Score 0-100 based on total sleep as a fraction of Full Night Sleep target."""
    fns = fns_minutes
    points = [
        (0.40 * fns, 0),
        (0.40 * fns, 10),
        (1.20 * fns, 100),
    ]
    # Below 40% of FNS = 0; at 40% = 10; at 120%+ = 100
    if total_minutes < 0.40 * fns:
        return 0
    return _interpolate(total_minutes, points)


def _deep_sleep_score(deep_minutes, fns_minutes):
    """Score 0-100 based on deep sleep as a fraction of Full Night Sleep target."""
    fns = fns_minutes
    points = [
        (0.00 * fns, 0),
        (0.15 * fns, 80),
        (0.25 * fns, 100),
        (0.30 * fns, 95),
        (1.00 * fns, 0),
    ]
    return _interpolate(deep_minutes, points)


def _rem_sleep_score(rem_minutes, fns_minutes):
    """Score 0-100 based on REM sleep as a fraction of Full Night Sleep target."""
    fns = fns_minutes
    points = [
        (0.000 * fns, 0),
        (0.100 * fns, 50),
        (0.200 * fns, 90),
        (0.225 * fns, 100),
        (0.250 * fns, 90),
        (0.500 * fns, 25),
    ]
    if rem_minutes > 0.50 * fns:
        return 0
    return _interpolate(rem_minutes, points)


def _interruptions_score(interrupted_minutes):
    """Score 0-100 based on minutes of sleep interrupted."""
    points = [
        (0, 100),
        (10, 90),
        (60, 50),
        (120, 25),
    ]
    if interrupted_minutes > 120:
        return 0
    return _interpolate(interrupted_minutes, points)


def sleep_score(
    total_minutes,
    deep_minutes,
    rem_minutes,
    interrupted_minutes,
    fns_hours=8.5,
):
    """
    Compute the Sleep Score (0-100) from last night's sleep data.

    Args:
        total_minutes: Total time asleep in minutes.
        deep_minutes: Deep sleep in minutes.
        rem_minutes: REM sleep in minutes.
        interrupted_minutes: Sleep interruption in minutes.
        fns_hours: Full Night Sleep target in hours (default 8.5).

    Returns:
        dict with 'score' (int) and component scores and weights.
    """
    fns = fns_hours * 60

    if interrupted_minutes is not None:
        components = {
            "total_sleep":   {"score": _total_sleep_score(total_minutes, fns), "weight": 0.40},
            "deep_sleep":    {"score": _deep_sleep_score(deep_minutes, fns),   "weight": 0.25},
            "rem_sleep":     {"score": _rem_sleep_score(rem_minutes, fns),     "weight": 0.20},
            "interruptions": {"score": _interruptions_score(interrupted_minutes), "weight": 0.15},
        }
    else:
        # Interruptions unavailable (Eight Sleep not connected); redistribute weight
        components = {
            "total_sleep": {"score": _total_sleep_score(total_minutes, fns), "weight": 0.47},
            "deep_sleep":  {"score": _deep_sleep_score(deep_minutes, fns),   "weight": 0.29},
            "rem_sleep":   {"score": _rem_sleep_score(rem_minutes, fns),     "weight": 0.24},
            "interruptions": {"score": None, "weight": 0},
        }

    score = round(sum(c["score"] * c["weight"] for c in components.values() if c["score"] is not None))
    return {"score": score, "components": components}
