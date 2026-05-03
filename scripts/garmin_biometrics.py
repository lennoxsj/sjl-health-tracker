#!/usr/bin/env python3
"""
Pull daily biometrics from Garmin Connect using python-garminconnect.

Usage:
    python garmin_biometrics.py              # today
    python garmin_biometrics.py 2026-04-28   # specific date

Authentication:
    First run: set GARMIN_EMAIL and GARMIN_PASSWORD env vars.
    Tokens are saved to ~/.garth and reused on subsequent runs.
    If your account has MFA enabled, you'll be prompted at first login.

Output: JSON to stdout.

Install:
    pip install garminconnect
"""

import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

import garminconnect

TOKENSTORE = Path.home() / ".garth"


def _get_mfa() -> str:
    return input("Garmin MFA code: ")


def _get_client() -> garminconnect.Garmin:
    email = os.environ.get("GARMIN_EMAIL", "")
    password = os.environ.get("GARMIN_PASSWORD", "")
    client = garminconnect.Garmin(email=email, password=password, prompt_mfa=_get_mfa)
    try:
        client.login(str(TOKENSTORE))
    except Exception:
        if not email or not password:
            sys.exit(
                "Error: Set GARMIN_EMAIL and GARMIN_PASSWORD for first-time login."
            )
        client.login()
        client.garth.dump(str(TOKENSTORE))
    return client


def pull_biometrics(target_date: date) -> dict:
    client = _get_client()
    date_str = target_date.isoformat()
    result: dict = {"date": date_str, "source": "garmin"}

    # Daily stats — resting HR, active calories, steps, body battery
    try:
        stats = client.get_stats(date_str)
        result["resting_heart_rate_bpm"] = stats.get("restingHeartRate")
        result["active_calories_kcal"] = stats.get("activeKilocalories")
        result["total_calories_kcal"] = stats.get("totalKilocalories")
        result["steps"] = stats.get("totalSteps")
        result["body_battery_high"] = stats.get("bodyBatteryHighestValue")
        result["body_battery_low"] = stats.get("bodyBatteryLowestValue")
    except Exception as e:
        result["daily_stats_error"] = str(e)

    # HRV — overnight only; requires a supported device (Fenix 7/8, FR955/965, Epix, Venu 3+)
    try:
        hrv = client.get_hrv_data(date_str)
        summary = (hrv or {}).get("hrvSummary", {})
        if summary:
            result["hrv_weekly_avg_ms"] = summary.get("weeklyAvg")
            result["hrv_last_night_avg_ms"] = summary.get("lastNight")
            result["hrv_last_night_5min_high_ms"] = summary.get("lastNight5MinHigh")
            result["hrv_status"] = summary.get("status")  # BALANCED / LOW / UNBALANCED / POOR
    except Exception as e:
        result["hrv_error"] = str(e)

    # Sleep — duration + stage breakdown + sleep score
    try:
        sleep = client.get_sleep_data(date_str)
        dto = (sleep or {}).get("dailySleepDTO", {})
        result["sleep_total_seconds"] = dto.get("sleepTimeSeconds")
        result["sleep_deep_seconds"] = dto.get("deepSleepSeconds")
        result["sleep_light_seconds"] = dto.get("lightSleepSeconds")
        result["sleep_rem_seconds"] = dto.get("remSleepSeconds")
        result["sleep_awake_seconds"] = dto.get("awakeSleepSeconds")
        scores = dto.get("sleepScores") or {}
        result["sleep_score"] = (scores.get("overall") or {}).get("value")
        total = dto.get("sleepTimeSeconds") or 0
        if total > 0:
            result["sleep_deep_pct"] = round((dto.get("deepSleepSeconds") or 0) / total * 100, 1)
            result["sleep_rem_pct"] = round((dto.get("remSleepSeconds") or 0) / total * 100, 1)
    except Exception as e:
        result["sleep_error"] = str(e)

    # Weight / body composition — requires Garmin Index scale or manual entry for fat/muscle
    try:
        body = client.get_body_composition(date_str, date_str)
        entries = (body or {}).get("dateWeightList") or []
        if entries:
            latest = entries[-1]
            raw_weight = latest.get("weight")
            result["weight_kg"] = round(raw_weight / 1000, 2) if raw_weight else None
            result["body_fat_pct"] = latest.get("bodyFat")
            raw_muscle = latest.get("muscleMass")
            result["muscle_mass_kg"] = round(raw_muscle / 1000, 2) if raw_muscle else None
            result["bmi"] = latest.get("bmi")
    except Exception as e:
        result["body_composition_error"] = str(e)

    # SpO2 — requires all-day pulse ox enabled on device
    try:
        spo2 = client.get_spo2_data(date_str)
        if spo2:
            result["spo2_avg_pct"] = spo2.get("averageSpO2")
            result["spo2_lowest_pct"] = spo2.get("lowestSpO2")
    except Exception as e:
        result["spo2_error"] = str(e)

    # Respiration rate — resting and during sleep
    try:
        resp = client.get_respiration_data(date_str)
        if resp:
            result["respiration_avg_waking_brpm"] = resp.get("avgWakingRespirationValue")
            result["respiration_avg_sleep_brpm"] = resp.get("avgSleepRespirationValue")
            result["respiration_lowest_brpm"] = resp.get("lowestRespirationValue")
    except Exception as e:
        result["respiration_error"] = str(e)

    # VO2 max — algorithmic estimate updated after qualifying runs or rides
    try:
        metrics = client.get_max_metrics(date_str)
        if metrics and isinstance(metrics, list):
            m = metrics[0]
            generic = m.get("generic") or {}
            cycling = m.get("cycling") or {}
            result["vo2max_running"] = generic.get("vo2MaxPreciseValue")
            result["vo2max_cycling"] = cycling.get("vo2MaxPreciseValue")
    except Exception as e:
        result["vo2max_error"] = str(e)

    # Training load — activities from the past 7 days
    try:
        week_ago = (target_date - timedelta(days=7)).isoformat()
        activities = client.get_activities_by_date(week_ago, date_str) or []
        result["training_load_7d_activity_count"] = len(activities)
        if activities:
            latest = activities[0]
            result["last_activity_type"] = (latest.get("activityType") or {}).get("typeKey")
            result["last_activity_duration_seconds"] = latest.get("duration")
            result["last_activity_training_stress_score"] = latest.get("trainingStressScore")
            result["last_activity_aerobic_training_effect"] = latest.get("aerobicTrainingEffect")
            result["last_activity_anaerobic_training_effect"] = latest.get("anaerobicTrainingEffect")
            tss_total = sum(
                (a.get("trainingStressScore") or 0) for a in activities
            )
            result["training_stress_score_7d_sum"] = round(tss_total, 1)
    except Exception as e:
        result["training_load_error"] = str(e)

    return result


def main() -> None:
    if len(sys.argv) > 1:
        try:
            target_date = date.fromisoformat(sys.argv[1])
        except ValueError:
            sys.exit(f"Invalid date '{sys.argv[1]}'. Use YYYY-MM-DD format.")
    else:
        target_date = date.today()

    biometrics = pull_biometrics(target_date)
    print(json.dumps(biometrics, indent=2, default=str))


if __name__ == "__main__":
    main()
