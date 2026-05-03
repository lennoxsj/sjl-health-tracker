import random


# Control points for load → readiness curve (inverted U).
# load=0 (stale/detrained) and load>100 (overreaching) both score low.
# Peak readiness is around load 40-50 (well-trained, not fatigued).
_LOAD_READINESS_POINTS = [
    (0,   35),   # no recent training — stale
    (20,  70),   # light training
    (45, 100),   # optimal load — peak readiness
    (65,  75),   # moderately tired but still good
    (85,  40),   # fatigued
    (110, 10),   # overreaching
    (140,  0),   # excessive — needs rest
]


def _load_readiness(load):
    """Map 3-day avg load (uncapped) to a 0-100 readiness value via the inverted-U curve."""
    points = _LOAD_READINESS_POINTS
    if load <= points[0][0]:
        return points[0][1]
    if load >= points[-1][0]:
        return points[-1][1]
    for i in range(len(points) - 1):
        x0, y0 = points[i]
        x1, y1 = points[i + 1]
        if x0 <= load <= x1:
            t = (load - x0) / (x1 - x0)
            return y0 + t * (y1 - y0)
    return points[-1][1]


def mettle_index(sleep_score, heart_breathing_score, three_day_avg_load):
    """
    Compute the Mettle Index (0-100): readiness to train hard today.

    Load component uses an inverted-U curve — peak readiness at moderate
    load (~45), dropping off when you've done nothing (stale) or too much
    (overreaching). Load scores above 100 are handled gracefully.

    Args:
        sleep_score: Sleep Score (0-100).
        heart_breathing_score: Cardiorespiratory Score (0-100).
        three_day_avg_load: 3-day average activity load (uncapped).

    Returns:
        dict with 'score' (int) and component breakdown.
    """
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
    """
    Suggest activities whose load score is within +/-7 of the Mettle Index.

    Constraints:
      - Primary and alternative will not both be road_bike / gravel_bike.
      - Strength activities are excluded if the same strength_type (leg/push/pull)
        has been done in the last 3 days.

    Args:
        mettle_score: Today's Mettle Index (0-100).
        activity_log: List of dicts with at least 'name', 'load_score', and 'date'.
        n: Number of suggestions to return (default 2).

    Returns:
        List of up to n activity dicts. Fewer than n if not enough matches exist.
    """
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
