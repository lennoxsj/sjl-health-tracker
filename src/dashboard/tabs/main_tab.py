import streamlit as st
from collections import defaultdict
from datetime import date
from src.scores.sleep_score import sleep_score
from src.scores.heart_breathing_score import heart_breathing_score
from src.scores.mettle_index import mettle_index, suggest_activities
from src.scores.activity_metrics import activity_load_score
from src.dashboard.utils import two_way_pct

_KG_TO_LBS = 2.20462


def _attach_rolling_strength_avgs(log):
    """
    For each strength activity in log, attach 'rolling_avg_volume_lbs' —
    the average weight volume (in lbs) of the 3 most recent prior workouts
    of the same strength_type.  Modifies activity dicts in-place.
    """
    strength_acts = sorted(
        [a for a in log if a.get("activity_type") == "strength"
         and a.get("strength_type") and a.get("weight_volume_kg") is not None],
        key=lambda a: a["date"],
    )
    type_history = defaultdict(list)  # strength_type -> list of past volume_lbs
    for act in strength_acts:
        stype = act["strength_type"]
        history = type_history[stype]
        if history:
            # 1, 2, or 3 prior workouts — average however many exist
            act["rolling_avg_volume_lbs"] = sum(history[-3:]) / min(len(history), 3)
        else:
            # No prior history — skip the volume bonus entirely
            act["rolling_avg_volume_lbs"] = None
        history.append(act["weight_volume_kg"] * _KG_TO_LBS)

SOURCE_LABELS = {
    "eight_sleep": "Eight Sleep",
    "oura": "Oura",
    "garmin": "Garmin",
}


def _arrow(current, reference, higher_is_better=True):
    if current > reference:
        return "↑" if higher_is_better else "↓"
    elif current < reference:
        return "↓" if higher_is_better else "↑"
    return "→"


def _fmt(minutes):
    h, m = divmod(int(minutes), 60)
    return f"{h}h {m:02d}m"


def _sources(source_list):
    return ", ".join(SOURCE_LABELS.get(s, s) for s in source_list)


def render(data):
    sleep = data["last_night_sleep"]
    rolling_sleep = data["sleep_rolling"]
    bio = data["last_night_biometrics"]
    rolling_bio = data["rolling_7day_biometrics"]
    vo2 = data["vo2_max"]
    log = data["activity_log"]
    goals = data["goals"]
    fns = data["FNS_HOURS"]

    # ── Compute scores ─────────────────────────────────────────────────────────
    ss = sleep_score(
        total_minutes=sleep["total_minutes"],
        deep_minutes=sleep["deep_minutes"],
        rem_minutes=sleep["rem_minutes"],
        interrupted_minutes=sleep["interrupted_minutes"],
        fns_hours=fns,
    )
    hbs = heart_breathing_score(
        last_night_rhr=bio["rhr"],
        rolling_avg_rhr=rolling_bio["rhr"],
        hrv_ms=bio["hrv_ms"],
        breath_bpm=bio["breath_bpm"],
    )
    swim_baseline_pace = goals.get("swim_pace_per_100m", {}).get("baseline")
    _attach_rolling_strength_avgs(log)
    for activity in log:
        if activity.get("load_score") is None:
            activity["load_score"] = activity_load_score(
                duration_minutes=activity.get("duration_minutes", 0),
                activity_type=activity.get("activity_type"),
                distance_km=activity.get("distance_km"),
                elevation_m=activity.get("elevation_m"),
                steps=activity.get("steps"),
                zones4plus_minutes=activity.get("zones4plus_minutes"),
                weight_volume_kg=activity.get("weight_volume_kg"),
                rolling_avg_volume_lbs=activity.get("rolling_avg_volume_lbs"),
                strength_type=activity.get("strength_type"),
                swim_baseline_pace=swim_baseline_pace,
                avg_pace_per_100m=activity.get("avg_pace_per_100m"),
            )
    today = date.today()
    recent_loads = sorted(
        [a for a in log if (a.get("load_score") or 0) > 0 and a["date"] < today],
        key=lambda a: a["date"], reverse=True,
    )
    most_recent_load = sum(a["load_score"] for a in recent_loads if a["date"] == recent_loads[0]["date"]) if recent_loads else 0
    last_3_days = sorted({a["date"] for a in recent_loads})[-3:] if recent_loads else []
    three_day_load = (
        sum(a["load_score"] for a in recent_loads if a["date"] in last_3_days) / len(last_3_days)
        if last_3_days else 0
    )
    mi = mettle_index(sleep_score=ss["score"], heart_breathing_score=hbs["score"], three_day_avg_load=three_day_load)
    suggestions = suggest_activities(mi["score"], [a for a in log if a.get("activity_type") != "steps"])

    # ── Row 1: Mettle Index + Loads + Suggestions ──────────────────────────────
    c = mi["components"]
    score = mi["score"]
    colour = "🟢" if score >= 60 else ("🟠" if score >= 40 else ("🟡" if score >= 20 else "🔴"))

    col_mi, col_l1, col_l2, col_s1, col_s2 = st.columns(5)
    with col_mi:
        st.metric(label=f"{colour} Mettle Index", value=score, help="0 = rest, 100 = push hard")
        st.caption(
            f"Sleep: **{c['sleep_score']['points']}** (40%)  \n"
            f"Cardiorespiratory: **{c['heart_breathing_score']['points']}** (30%)  \n"
            f"Load: **{c['activity_load']['points']}** (30%)"
        )
    col_l1.metric("Yesterday's load", most_recent_load, help="Sum of load scores for most recent day")
    col_l2.metric("3-day avg load", f"{three_day_load:.0f}")
    for i, col in enumerate([col_s1, col_s2]):
        with col:
            if i < len(suggestions):
                a = suggestions[i]
                label = "Primary suggestion" if i == 0 else "Alternative suggestion"
                url = a.get("strava_url")
                link = f"[{a['name']}]({url})" if url else a["name"]
                st.markdown(f"**{label}**")
                st.markdown(f"{link} · load {a['load_score']}")
            elif i == 0:
                st.caption("Not enough activity history for suggestions yet.")

    st.divider()

    # ── Row 2: Sleep ───────────────────────────────────────────────────────────
    st.markdown("**Sleep**")
    s1, s2, s3, s4, s5 = st.columns(5)
    s1.metric("Sleep Score", f"{ss['score']} / 100")
    s2.metric("Total time asleep", _fmt(sleep["total_minutes"]))
    s3.metric("Deep", _fmt(sleep["deep_minutes"]),
              delta=f"3-night avg {_fmt(rolling_sleep['deep_minutes_avg'])}", delta_color="off")
    s4.metric("REM", _fmt(sleep["rem_minutes"]),
              delta=f"3-night avg {_fmt(rolling_sleep['rem_minutes_avg'])}", delta_color="off")
    interrupted = sleep.get("interrupted_minutes")
    s5.metric("Interruptions", f"{interrupted} min" if interrupted is not None else "— (Eight Sleep)")

    sc = ss["components"]
    interruptions_str = (
        f"Interruptions: {sc['interruptions']['score']} (15%)"
        if sc["interruptions"]["score"] is not None
        else "Interruptions: — (pending Eight Sleep)"
    )
    st.caption(f"Sources: {_sources(sleep['sources'])}")
    st.caption(
        f"Score — Total time asleep: {sc['total_sleep']['score']} (40%) · "
        f"Deep: {sc['deep_sleep']['score']} (25%) · "
        f"REM: {sc['rem_sleep']['score']} (20%) · "
        f"{interruptions_str}"
    )

    st.divider()

    # ── Row 3: Cardiorespiratory ───────────────────────────────────────────────
    st.markdown("**Cardiorespiratory**")
    rhr_arrow = _arrow(bio["rhr"],        rolling_bio["rhr"],        higher_is_better=False)
    hrv_arrow = _arrow(bio["hrv_ms"],     rolling_bio["hrv_ms"],     higher_is_better=True)
    br_arrow  = _arrow(bio["breath_bpm"], rolling_bio["breath_bpm"], higher_is_better=False)
    vo2_arrow = _arrow(vo2["current"],    vo2["one_month_ago"])
    optimal_br = 13 <= bio["breath_bpm"] <= 15

    h1, h2, h3, h4, h5 = st.columns(5)
    h1.metric("C-R Score", f"{hbs['score']} / 100")
    h2.metric("Resting HR", f"{bio['rhr']} bpm {rhr_arrow}",
              delta=f"7-day avg {rolling_bio['rhr']} bpm", delta_color="off")
    h3.metric("HRV", f"{bio['hrv_ms']} ms {hrv_arrow}",
              delta=f"7-day avg {rolling_bio['hrv_ms']} ms", delta_color="off")
    h4.metric("Breath Rate", f"{bio['breath_bpm']:.1f} {br_arrow}",
              delta="✓ Optimal" if optimal_br else "Outside 13–15",
              delta_color="normal" if optimal_br else "inverse")
    h5.metric("VO₂ Max", f"{vo2['current']:.1f} {vo2_arrow}",
              delta=f"vs {vo2['one_month_ago']:.1f} a month ago",
              delta_color="normal" if vo2["current"] >= vo2["one_month_ago"] else "inverse")

    hc = hbs["components"]
    st.caption(f"Sources: {_sources(bio['sources'])}")
    st.caption(
        f"Score — RHR: {hc['resting_heart_rate']['score']} (⅓) · "
        f"HRV: {hc['hrv']['score']} (⅓) · "
        f"Breath: {hc['breath_rate']['score']} (⅓)"
    )

    st.divider()

    # ── Row 4: Goals ───────────────────────────────────────────────────────────
    st.markdown(f"**Goal Progress — {goals['quarter']}**")
    g = goals

    all_goals = [
        ("Biking Distance", g['biking_distance_km']['progress'] / g['biking_distance_km']['target']),
        ("Biking Climbing", g['biking_climbing_m']['progress']  / g['biking_climbing_m']['target']),
        ("Swim Distance",   g['swim_distance_km']['progress']   / g['swim_distance_km']['target']),
        ("Road Bike GAP",   two_way_pct(g['road_bike_gap_kmh']['progress'],    g['road_bike_gap_kmh']['baseline'],    g['road_bike_gap_kmh']['target'],    higher_is_better=True)),
        ("Swim Pace",       two_way_pct(g['swim_pace_per_100m']['progress'],   g['swim_pace_per_100m']['baseline'],   g['swim_pace_per_100m']['target'])),
        ("Back Squat",      two_way_pct(g['back_squat_kg']['progress'],        g['back_squat_kg']['baseline'],        g['back_squat_kg']['target'],        higher_is_better=True)),
        ("Weight",          two_way_pct(g['weight_kg']['progress'],            g['weight_kg']['baseline'],            g['weight_kg']['target'],            higher_is_better=False)),
        ("Body Fat",        two_way_pct(g['body_fat_kg']['progress'],          g['body_fat_kg']['baseline'],          g['body_fat_kg']['target'],          higher_is_better=False)),
        ("Lean Mass",       two_way_pct(g['lean_mass_kg']['progress'],         g['lean_mass_kg']['baseline'],         g['lean_mass_kg']['target'],         higher_is_better=True)),
    ]

    col_l, col_r = st.columns(2)
    for i, (name, pct) in enumerate(all_goals):
        col = col_l if i % 2 == 0 else col_r
        with col:
            gc1, gc2 = st.columns([3, 4])
            gc1.caption(f"**{name}**")
            gc2.progress(min(1.0, max(0.0, pct)))
