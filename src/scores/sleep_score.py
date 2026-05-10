# GIT PUBLIC REPO

from collections import namedtuple
import numpy as np

# Control point on a piecewise-linear scoring curve: input value -> 0-100 score.
Point = namedtuple("Point", ["input", "score"])


def _interpolate(value, curve):
    """Piecewise linear interpolation along a list of Points (clamped at the ends)."""
    xs = [p.input for p in curve]
    ys = [p.score for p in curve]
    return round(float(np.interp(value, xs, ys)))


def _total_sleep_score(total_minutes, fns_minutes):
    """Score 0-100 based on total sleep as a fraction of Full Night Sleep target."""
    fns = fns_minutes
    # Below 40% of FNS = 0; at 40% = 10; at 120%+ = 100
    if total_minutes < 0.40 * fns:
        return 0
    curve = [
        Point(0.40 * fns,  10),
        Point(1.20 * fns, 100),
    ]
    return _interpolate(total_minutes, curve)


def _deep_sleep_score(deep_minutes, fns_minutes):
    """Score 0-100 based on deep sleep as a fraction of Full Night Sleep target."""
    fns = fns_minutes
    curve = [
        Point(0.00 * fns,   0),
        Point(0.15 * fns,  80),
        Point(0.25 * fns, 100),
        Point(0.30 * fns,  95),
        Point(1.00 * fns,   0),
    ]
    return _interpolate(deep_minutes, curve)


def _rem_sleep_score(rem_minutes, fns_minutes):
    """Score 0-100 based on REM sleep as a fraction of Full Night Sleep target."""
    fns = fns_minutes
    if rem_minutes > 0.50 * fns:
        return 0
    curve = [
        Point(0.000 * fns,   0),
        Point(0.100 * fns,  50),
        Point(0.200 * fns,  90),
        Point(0.225 * fns, 100),
        Point(0.250 * fns,  90),
        Point(0.500 * fns,  25),
    ]
    return _interpolate(rem_minutes, curve)


def _interruptions_score(interrupted_minutes):
    """Score 0-100 based on minutes of sleep interrupted."""
    if interrupted_minutes > 120:
        return 0
    curve = [
        Point(0,   100),
        Point(10,   90),
        Point(60,   50),
        Point(120,  25),
    ]
    return _interpolate(interrupted_minutes, curve)


def sleep_score(
    total_minutes,
    deep_minutes,
    rem_minutes,
    interrupted_minutes,
    fns_hours=8.5,
):
    """Compute the Sleep Score (0-100) from last night's sleep data.

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
