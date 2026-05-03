import os
from datetime import date, timedelta
from dotenv import load_dotenv
from garminconnect import Garmin

load_dotenv()

_TOKEN_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", ".garth")


def _get_api():
    """Return an authenticated Garmin API client using saved session tokens."""
    api = Garmin(os.environ["GARMIN_EMAIL"], os.environ["GARMIN_PASSWORD"])
    api.login(tokenstore=_TOKEN_PATH)
    return api


def fetch_sleep(days_back=30):
    """
    Fetch nightly sleep data from Garmin Connect.

    Returns list of dicts (newest first):
        day, total_minutes, deep_minutes, rem_minutes, rhr, hrv_ms
    """
    api   = _get_api()
    end   = date.today()
    start = end - timedelta(days=days_back)

    nights = []
    current = end
    while current >= start:
        try:
            raw   = api.get_sleep_data(current.isoformat())
            daily = raw.get("dailySleepDTO", {})
            total_s = daily.get("sleepTimeSeconds")

            if total_s and total_s > 1800:
                # RHR
                rhr_raw = api.get_rhr_day(current.isoformat())
                rhr_entries = (
                    rhr_raw.get("allMetrics", {})
                           .get("metricsMap", {})
                           .get("WELLNESS_RESTING_HEART_RATE", [])
                )
                rhr = round(rhr_entries[0]["value"]) if rhr_entries else None

                # HRV
                hrv_raw = api.get_hrv_data(current.isoformat())
                hrv = hrv_raw.get("hrvSummary", {}).get("lastNightAvg")

                nights.append({
                    "day":           current.isoformat(),
                    "total_minutes": round(total_s / 60),
                    "deep_minutes":  round((daily.get("deepSleepSeconds") or 0) / 60),
                    "rem_minutes":   round((daily.get("remSleepSeconds")  or 0) / 60),
                    "rhr":           rhr,
                    "hrv_ms":        hrv,
                })
        except Exception:
            pass
        current -= timedelta(days=1)

    return sorted(nights, key=lambda n: n["day"], reverse=True)


def fetch_steps(days_back=30):
    """
    Fetch daily step counts from Garmin Connect.

    Returns list of dicts (newest first): day, steps
    """
    api   = _get_api()
    end   = date.today()
    start = end - timedelta(days=days_back)

    results = []
    current = end
    while current >= start:
        try:
            stats = api.get_stats(current.isoformat())
            steps = stats.get("totalSteps")
            if steps is not None:
                results.append({"day": current.isoformat(), "steps": steps})
        except Exception:
            pass
        current -= timedelta(days=1)

    return sorted(results, key=lambda r: r["day"], reverse=True)


def fetch_weight(days_back=90):
    """
    Fetch weight readings from Garmin scale (total weight only).

    Returns list of dicts (newest first): day, weight_kg
    """
    api   = _get_api()
    end   = date.today()
    start = end - timedelta(days=days_back)

    try:
        raw      = api.get_weigh_ins(start.isoformat(), end.isoformat())
        entries  = raw.get("dailyWeightSummaries", [])
        results  = []
        for e in entries:
            latest = e.get("latestWeight", {})
            w = latest.get("weight")
            if w:
                results.append({
                    "day":       e["summaryDate"],
                    "weight_kg": round(w / 1000, 1),  # Garmin stores grams
                })
        return sorted(results, key=lambda r: r["day"], reverse=True)
    except Exception:
        return []


def fetch_vo2_max(days_back=90):
    """
    Fetch most recent VO2 max estimates from Garmin.
    Garmin only produces a value on days with qualifying activities.

    Returns list of dicts (newest first): day, vo2_max
    """
    api     = _get_api()
    end     = date.today()
    results = []

    for i in range(days_back):
        current = end - timedelta(days=i)
        try:
            raw = api.get_max_metrics(current.isoformat())
            if raw:
                vo2 = raw[0].get("generic", {}).get("vo2MaxPreciseValue")
                if vo2:
                    results.append({"day": current.isoformat(), "vo2_max": round(vo2, 1)})
        except Exception:
            pass

    return results
