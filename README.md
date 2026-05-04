# Mettle Index — Sarah's Personal Health Tracker

I love my wearables and all the data they provide, but I became frustrated with not having an aggregator. My Personal Health Tracker, built in Python and Streamlit, is an attempt to consolidate some high use data, track goals and experiment with personal scoring algorithms. This repository contains the core scoring and data ingestion logic but as this is a personal project, the full dashboard, data pipeline, and configuration are not included in this repository.

## What is the Mettle Index?

The Mettle Index is a daily readiness score (0–100) that answers the question: *how hard should I train today?* 

It combines three components:

| Sleep Score | 40% weight | Oura / Garmin / Eight Sleep |
| Cardiorespiratory Score | 30% | Resting HR, HRV, breathing rate |
| Activity Load | 30% | Strava / Oura / Garmin |

The load component uses an inverted-U curve — a score of 0 means I'm stale from inactivity, a score of 100 means I'm overreaching. Peak readiness sits around a 3-day average load of ~45.

## Activity Load Scoring

Activities are scored using my bespoke point-based system rather than a generic formula. Each sport type has its own scoring logic based on duration, distance, elevation, heart rate zones, and (for strength training) volume relative to a rolling average.

See `src/scores/activity_metrics.py` for the full implementation. A few details about the scoring logic as well as a few scored examples are below:

## Gravel biking
25 points per hour of biking (road biking is only 20 points because gravel terrain is physically harder on my body regardless of steepness or speed)
30 points per hour after 2 hours (extra long rides are not scored linearly)
1 point per steepness index point per hour (steeper ride = higher load score)
1 point per 15 minutes in Zone 4+

## Swimming (open water in the Bay or Lake Tahoe)
15 points per 500m of swimming
20 points per 500m of swimming >2km (longer time in cold water is not scored linearly)
1 point per 10 seconds swum below baseline 100m swim pace (faster pace = pushing harder)
2 points per 15 minutes spent above 80% of max HR (this would likely mean sprinting, which may not show up in overall pace)

## Examples

```python
from src.scores.activity_metrics import activity_load_score

# Road bike — 3.5 hours, 814m elevation, 45 min in Zone 4+
score = activity_load_score(
    duration_minutes=210,
    activity_type="road_bike",
    distance_km=57.6,
    elevation_m=814,
    zones4plus_minutes=45,
)
# → 124

# Swim — 2km, pace 2:28/100m, baseline 2:35/100m
score = activity_load_score(
    duration_minutes=48,
    activity_type="swim",
    distance_km=2.0,
    avg_pace_per_100m="2:28",
    swim_baseline_pace="2:35",
)
# → 60

# Leg strength — 70 min, 11,662 lbs volume, rolling avg 6,576 lbs
score = activity_load_score(
    duration_minutes=70,
    activity_type="strength",
    strength_type="leg",
    weight_volume_kg=5290,           # I'm Australian, so there are quite a few metric/imperial conversions in this code
    rolling_avg_volume_lbs=6576,
    zones4plus_minutes=2,
)
# → 88
```

## Files in this repo

| File | Description |
|---|---|
| `src/scores/activity_metrics.py` | Activity load score calculations |
| `src/scores/mettle_index.py` | Mettle Index and activity suggestions |
| `src/scores/sleep_score.py` | Sleep score from staging data |
| `src/scores/heart_breathing_score.py` | Cardiorespiratory score from HRV, RHR, breathing rate |
| `src/ingest/strava.py` | Strava API integration |
| `src/ingest/activity_log.py` | Activity log utilities |
