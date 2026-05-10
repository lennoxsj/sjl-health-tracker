# GIT PUBLIC REPO

"""Calculates the Cardiorespiratory score which is used for the Mettle Index"""

from collections import namedtuple
import numpy as np

# Control point on a piecewise-linear scoring curve: input value -> 0-100 score.
Point = namedtuple("Point", ["input", "score"])


def _interpolate(value, curve):
    """Piecewise linear interpolation along a list of Points (clamped at the ends)."""
    xs = [p.input for p in curve]
    ys = [p.score for p in curve]
    return round(float(np.interp(value, xs, ys)))


def _rhr_score(last_night_rhr, rolling_avg_rhr):
    """Score 0-100 based on last night's RHR vs. 7-day rolling average.
    delta = last_night - rolling_avg (positive means elevated)"""
    delta = last_night_rhr - rolling_avg_rhr
    curve = [
        Point(-30,   0),
        Point( -5, 100),
        Point( +5,  80),
        Point(+20,   0),
    ]
    return _interpolate(delta, curve)


def _hrv_score(hrv_ms):
    """Score 0-100 based on last night's HRV in milliseconds."""
    if hrv_ms > 120:
        return 0
    curve = [
        Point(  0,   0),
        Point( 60,  60),
        Point( 70, 100),
        Point( 90, 100),
        Point(120,  50),
    ]
    return _interpolate(hrv_ms, curve)


def _breath_score(breath_bpm):
    """Score 0-100 based on last night's respiratory rate in breaths per minute."""
    if breath_bpm >= 40:
        return 0
    curve = [
        Point( 0,   0),
        Point(13, 100),
        Point(15, 100),
        Point(20,  80),
        Point(40,   0),
    ]
    return _interpolate(breath_bpm, curve)


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
