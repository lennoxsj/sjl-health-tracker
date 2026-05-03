import streamlit as st
import pandas as pd
from src.scores.activity_metrics import (
    steepness_index,
    grade_adjusted_pace,
    activity_load_score,
    CYCLING_TYPES,
    GRADE_ADJUSTED_PACE_TYPES,
)

ACTIVITY_LABELS = {
    "road_bike":    "Road Bike",
    "gravel_bike":  "Gravel Bike",
    "mountain_bike": "Mountain Bike",
    "run":          "Run",
    "hike":         "Hike",
    "walk":         "Walk",
    "swim":         "Swim",
    "row":          "Row",
    "strength":     "Strength",
    "misc":             "Workout",
    "yoga":             "Yoga",
    "pilates":          "Pilates",
    "stretch_mobility": "Stretch / Mobility",
    "steps":            "Steps",
}


def render(data):
    log = data["activity_log"]

    st.header("Activity Log")

    rows = []
    for a in sorted(log, key=lambda x: x["date"], reverse=True):
        load = a.get("load_score") or activity_load_score(
            duration_minutes       = a.get("duration_minutes", 0),
            activity_type          = a.get("activity_type"),
            distance_km            = a.get("distance_km"),
            elevation_m            = a.get("elevation_m"),
            zones4plus_minutes     = a.get("zones4plus_minutes"),
            weight_volume_kg       = a.get("weight_volume_kg"),
            rolling_avg_volume_lbs = a.get("rolling_avg_volume_lbs"),
            strength_type          = a.get("strength_type"),
            avg_pace_per_100m      = a.get("avg_pace_per_100m"),
        )

        atype = a.get("activity_type")
        si = (
            steepness_index(a["elevation_m"], a["distance_km"])
            if atype in CYCLING_TYPES and a.get("elevation_m") and a.get("distance_km")
            else None
        )
        gap = (
            grade_adjusted_pace(a["avg_speed_kmh"], si)
            if atype in GRADE_ADJUSTED_PACE_TYPES and a.get("avg_speed_kmh") and si is not None
            else None
        )

        dur = a.get("duration_minutes")
        dur_str = f"{int(dur) // 60}h {int(dur) % 60:02d}m" if dur else "—"

        z4 = a.get("zones4plus_minutes")
        rows.append({
            "Date": a["date"].strftime("%-d %b %Y"),
            "Type": ACTIVITY_LABELS.get(atype, atype),
            "Activity": a.get("name") or ACTIVITY_LABELS.get(atype, atype),
            "Duration": dur_str,
            "Distance": f"{a['distance_km']:.1f} km" if a.get("distance_km") else ("—" if atype != "steps" else f"{a.get('steps', 0):,} steps"),
            "Elevation": f"{a['elevation_m']:.0f} m" if a.get("elevation_m") else "—",
            "Steepness": str(si) if si is not None else "—",
            "GAP": f"{gap:.1f} km/h" if gap is not None else "—",
            "Avg HR": f"{a['avg_hr']} bpm" if a.get("avg_hr") else "—",
            "Zone 4+": f"{z4:.0f} min" if z4 is not None else "—",
            "Load": load,
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
