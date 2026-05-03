"""
Activity log processing: deduplication and steps adjustment.

Deduplication rule: Strava has precedence. Activities from other sources
(Garmin, Oura) are only included if no Strava activity covers the same event.
Matching is done by date and activity type; within ~30 minutes start time is
treated as the same event.

Steps: Daily step count from Garmin, minus steps taken during any specifically
recorded Running, Hiking, or Walking activities on that day.
"""

from datetime import timedelta

RECORDED_WALK_TYPES = {"run", "hike", "walk"}
STEPS_ACTIVITY_TYPE = "steps"

# Average steps per km for removing recorded activity steps from daily total
_STEPS_PER_KM = 1300


def deduplicate_activities(activities):
    """
    Remove duplicate activities, keeping the Strava record when duplicates exist.

    Args:
        activities: List of activity dicts. Each must have:
            - 'source': str (e.g. 'strava', 'garmin', 'oura')
            - 'start_time': datetime
            - 'activity_type': str
          Optional: any other fields.

    Returns:
        Deduplicated list of activity dicts.
    """
    strava = [a for a in activities if a["source"] == "strava"]
    others = [a for a in activities if a["source"] != "strava"]

    kept = list(strava)

    for activity in others:
        duplicate = any(
            activity["activity_type"] == s["activity_type"]
            and abs((activity["start_time"] - s["start_time"]).total_seconds()) < 1800
            for s in strava
        )
        if not duplicate:
            kept.append(activity)

    return sorted(kept, key=lambda a: a["start_time"], reverse=True)


def adjust_steps_for_recorded_activities(daily_steps, activities_on_day):
    """
    Subtract estimated steps for recorded Running, Hiking, and Walking activities
    from the raw Garmin daily step count to avoid double-counting.

    Args:
        daily_steps: Raw Garmin step count for the day (int).
        activities_on_day: List of activity dicts for the same day.
            Each dict should have 'activity_type' and optionally 'distance_km'.

    Returns:
        Adjusted step count (int, minimum 0).
    """
    steps_to_remove = 0
    for activity in activities_on_day:
        if activity["activity_type"] in RECORDED_WALK_TYPES:
            distance_km = activity.get("distance_km", 0) or 0
            steps_to_remove += int(distance_km * _STEPS_PER_KM)

    return max(0, daily_steps - steps_to_remove)
