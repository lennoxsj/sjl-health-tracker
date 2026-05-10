# GIT PUBLIC REPO

import random
from collections import namedtuple
import numpy as np

# Control point on the load → readiness curve: 3-day avg load -> readiness 0-100.
Point = namedtuple("Point", ["load", "readiness"])

# Inverted-U curve. load=0 (stale/detrained) and load>100 (overreaching) both
# score low. Peak readiness is around load 40-50 (well-trained, not fatigued).
_LOAD_READINESS_CURVE = [
    Point(  0,  35),   # no recent training — stale
    Point( 20,  70),   # light training
    Point( 45, 100),   # optimal load — peak readiness
    Point( 65,  75),   # moderately tired but still good
    Point( 85,  40),   # fatigued
    Point(110,  10),   # overreaching
    Point(140,   0),   # excessive — needs rest
]


def _load_readiness(load):
    """Map 3-day avg load (uncapped) to a 0-100 readiness value via the inverted-U curve."""
    xs = [p.load for p in _LOAD_READINESS_CURVE]
    ys = [p.readiness for p in _LOAD_READINESS_CURVE]
    return float(np.interp(load, xs, ys))


def mettle_index(sleep_score, heart_breathing_score, three_day_avg_load):
    """Compute the Mettle Index (0-100): readiness to train hard today.

    Load component uses an inverted-U curve — peak readiness at moderate
    load (~45), dropping off when I've been lazy or done too much
    (overreaching)..

    Args:
        sleep_score: Sleep Score (0-100).
        heart_breathing_score: Cardiorespiratory Score (0-100).
        three_day_avg_load: 3-day average activity load (uncapped).

    Returns:
        dict with 'score' (int) and component breakdown."""
    
    readiness        = _load_readiness(three_day_avg_load)

    sleep_points     = sleep_score * 0.40
    hb_points        = heart_breathing_score * 0.30
    load_points      = readiness * 0.30

    score = round(sleep_points + hb_points + load_points)

    return {
        "score": score,
        "components": {
            "sleep_score":           {"score": sleep_score,           "weight": 0.40, "points": round(sleep_points)},
            "heart_breathing_score": {"score": heart_breathing_score, "weight": 0.30, "points": round(hb_points)},
            "activity_load":         {"score": round(readiness),      "weight": 0.30, "points": round(load_points)},
        },
    }


_CYCLING_GROUP = {"road_bike", "gravel_bike"}


def suggest_activities(mettle_score, activity_log, n=2):
    """Suggest activities that have a load score within +/-7 of Mettle Index.

    Constraints:
      - Primary and alternative will not both be road_bike / gravel_bike.
      - Strength activities are excluded if the same strength_type (leg/push/pull)
        has been done in the last 3 days.

    Args:
        mettle_score: Today's Mettle Index (0-100).
        activity_log: List of dicts with at least 'name', 'load_score', and 'date'.
        n: Number of suggestions to return (default 2).

    Returns:
        List of up to n activity dicts. Fewer than n if not enough matches exist."""
    
    from datetime import date, timedelta

    today = date.today()
    cutoff = today - timedelta(days=3)

    # Strength types done in the last 3 days — block same type from suggestions
    recent_strength_types = {
        a["strength_type"]
        for a in activity_log
        if a.get("activity_type") == "strength"
        and a.get("strength_type")
        and (a["date"] if isinstance(a["date"], date) else date.fromisoformat(a["date"])) >= cutoff
    }

    def _candidates(window):
        return [
            a for a in activity_log
            if a.get("load_score") is not None
            and abs(a["load_score"] - mettle_score) <= window
            and not (
                a.get("activity_type") == "strength"
                and a.get("strength_type") in recent_strength_types
            )
        ]

    # Start tight, widen if needed to find at least 2 suggestions
    candidates = _candidates(7)
    if len(candidates) < 2:
        candidates = _candidates(15)
    if len(candidates) < 2:
        candidates = _candidates(25)

    if not candidates:
        return []

    primary = random.choice(candidates)
    suggestions = [primary]

    if n >= 2:
        primary_type = primary.get("activity_type")
        alt_candidates = [
            a for a in candidates
            if a is not primary
            and not (primary_type in _CYCLING_GROUP and a.get("activity_type") in _CYCLING_GROUP)
        ]
        if alt_candidates:
            suggestions.append(random.choice(alt_candidates))

    return suggestions
