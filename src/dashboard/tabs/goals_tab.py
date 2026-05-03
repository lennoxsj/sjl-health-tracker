import streamlit as st
from src.dashboard.utils import two_way_pct


def _row(label, progress_str, pct, baseline_str=None, note=None):
    c1, c2, c3 = st.columns([2.5, 1.5, 4])
    c1.markdown(f"**{label}**")
    c2.markdown(progress_str)
    if baseline_str:
        c2.caption(baseline_str)
    c3.progress(min(1.0, max(0.0, pct)))
    if note:
        st.caption(note)


def render(data):
    g = data["goals"]
    fns = data["FNS_HOURS"]

    st.header(f"Goals — {g['quarter']}")

    # ── Biking ────────────────────────────────────────────────────────────────
    st.subheader("Biking")
    _row(
        "Distance (road, gravel, MTB)",
        f"{g['biking_distance_km']['progress']:.0f} / {g['biking_distance_km']['target']:.0f}km",
        g['biking_distance_km']['progress'] / g['biking_distance_km']['target'],
    )
    _row(
        "Climbing",
        f"{g['biking_climbing_m']['progress']:.0f} / {g['biking_climbing_m']['target']:.0f}m",
        g['biking_climbing_m']['progress'] / g['biking_climbing_m']['target'],
    )
    gb = g['road_bike_gap_kmh']
    _row(
        "Road Bike Grade Adjusted Pace",
        f"Recent {gb['progress']:.1f} km/h vs. target {gb['target']:.1f}",
        two_way_pct(gb['progress'], gb['baseline'], gb['target'], higher_is_better=True),
        baseline_str=f"Baseline {gb['baseline']:.1f}",
        note="GAP progress is average of last three road bike rides",
    )

    st.divider()

    # ── Swimming ──────────────────────────────────────────────────────────────
    st.subheader("Swimming")
    _row(
        "Distance",
        f"{g['swim_distance_km']['progress']:.1f} / {g['swim_distance_km']['target']:.1f}km",
        g['swim_distance_km']['progress'] / g['swim_distance_km']['target'],
    )
    sp = g['swim_pace_per_100m']
    _row(
        "100m Pace",
        f"Recent {sp['progress']} /100m vs. target {sp['target']}",
        two_way_pct(sp['progress'], sp['baseline'], sp['target']),
        baseline_str=f"Baseline {sp['baseline']}",
        note="Pace is average of last three swims",
    )

    st.divider()

    # ── Strength ──────────────────────────────────────────────────────────────
    st.subheader("Strength")
    sq = g['back_squat_kg']
    _row(
        "Back Squat (8+ reps)",
        f"Recent {sq['progress']:.1f} kg ({sq['progress'] * 2.205:.0f} lbs) vs. target {sq['target']:.1f} kg",
        two_way_pct(sq['progress'], sq['baseline'], sq['target'], higher_is_better=True),
        baseline_str=f"Baseline {sq['baseline']:.1f} kg",
        note="Heaviest set of 8+ reps this quarter",
    )

    st.divider()

    # ── Body Composition ──────────────────────────────────────────────────────
    st.subheader("Body Composition")
    wt = g['weight_kg']
    _row(
        "Weight",
        f"Recent {wt['progress']:.1f} kg vs. target {wt['target']:.1f} kg",
        two_way_pct(wt['progress'], wt['baseline'], wt['target'], higher_is_better=False),
        baseline_str=f"Baseline {wt['baseline']:.1f} kg",
        note="Average of last 3 Garmin scale readings",
    )
    bf = g['body_fat_kg']
    _row(
        "Body Fat",
        f"Recent {bf['progress']:.1f} kg vs. target {bf['target']:.1f} kg",
        two_way_pct(bf['progress'], bf['baseline'], bf['target'], higher_is_better=False),
        baseline_str=f"Baseline {bf['baseline']:.1f} kg",
        note="From DEXA scan (BodySpec)",
    )
    lm = g['lean_mass_kg']
    _row(
        "Lean Mass",
        f"Recent {lm['progress']:.1f} kg vs. target {lm['target']:.1f} kg",
        two_way_pct(lm['progress'], lm['baseline'], lm['target'], higher_is_better=True),
        baseline_str=f"Baseline {lm['baseline']:.1f} kg",
        note="From DEXA scan (BodySpec)",
    )

    st.divider()

    # ── Sleep ─────────────────────────────────────────────────────────────────
    st.subheader("Sleep")
    st.markdown(f"Full Night Sleep (FNS) target: **{fns} hrs**")
    st.caption("Used across all sleep scoring. Update in hard_code_data.py to change.")
