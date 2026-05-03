# Garmin API Research: Available Health & Fitness Data

## Overview of Garmin's Developer APIs

Garmin offers two primary API systems for accessing health and fitness data:

### 1. Garmin Health API (Official — Business/Enterprise Only)
Part of the Garmin Connect Developer Program at developer.garmin.com. This is the sanctioned REST API for third-party companies to integrate Garmin data into their platforms. Access requires applying as a business developer, going through an approval process (typically 1–4 weeks), and signing a developer program agreement. There are no licensing fees, though commercial metric access may carry fees. Individual/personal developers without a formal company affiliation are generally not approved.

### 2. Unofficial / Reverse-Engineered API (Personal Use)
The open-source `python-garminconnect` library (PyPI: `garminconnect`) reverse-engineers Garmin Connect's internal web endpoints. It provides 131+ methods covering virtually all the same data types. This is widely used for personal automation, Home Assistant integrations, and self-hosted dashboards. It is not officially sanctioned — Garmin does not guarantee its stability, and they have previously rate-limited or blocked access. Projects like `garmy`, `garmin-api-handler`, and `GarminDB` follow the same approach.

---

## Target Biometrics (from Design Doc)

### Resting Heart Rate
- **Available: Yes**
- Provided via the **Dailies (Daily Summaries)** endpoint in the Health API.
- Field: `restingHeartRateInBeatsPerMinute` — daily average, typically calculated from overnight data.
- Also available through the unofficial API via daily stats endpoints.

### HRV (Heart Rate Variability)
- **Available: Yes** — with device caveats
- Garmin added a dedicated **HRV Summaries** endpoint to the Health API.
- Data is collected during the **overnight sleep window only**, not continuously.
- Key fields: `calendarDate`, `startTimeInSeconds`, `durationInSeconds`, `lastNight5MinHigh` (highest 5-min HRV overnight), and `hrvValues` (beat-by-beat array).
- Garmin also provides an **HRV Status** (proprietary wellness indicator: Balanced, Low, Unbalanced, Poor) available on supported devices.
- **Device caveat**: Only available on select recent devices — Forerunner 955, Fenix 7 series, Epix series, etc. Older/budget devices do not collect overnight HRV.

### Sleep Duration / Stages
- **Available: Yes — comprehensive**
- Dedicated **Sleep Summaries** endpoint with rich detail:
  - `durationInSeconds` — total sleep time
  - `deepSleepDurationInSeconds`
  - `lightSleepDurationInSeconds`
  - `remSleepInSeconds`
  - `awakeDurationInSeconds`
  - `unmeasurableSleepInSeconds`
  - Per-epoch sleep level timeline data for high-resolution analysis
  - Sleep Score — composite 0–100 score for supported devices
- Auto-detection quality varies by device generation.

### Weight / Body Composition
- **Available: Yes — very detailed**
- Dedicated **Body Composition Summaries** endpoint.
- Fields:
  - `weightInGrams`
  - `bodyMassIndex`
  - `bodyFatInPercent`
  - `muscleMassInGrams`
  - `boneMassInGrams`
  - `bodyWaterInPercent`
- Full body composition data requires a compatible Garmin smart scale (Index S2) or manual entry. Without a scale, only basic weight entries are available.

---

## Additional Useful Metrics

| Metric | API Endpoint / Type | Notes |
|---|---|---|
| **Steps / Distance / Calories** | Dailies | Core daily wellness summary |
| **Active vs. Total Calories** | Dailies | Distinguishes BMR from activity burn |
| **Floors Climbed** | Dailies | Elevation metric |
| **Stress Score** | Detailed Stress Summaries | 3-minute granularity, scored 1–100; low/medium/high/rest zones |
| **Body Battery** | Dailies / Stress Summaries | Garmin's proprietary energy reserve metric (0–100); derived from HRV, stress, sleep, and activity — highly relevant for readiness scoring |
| **SpO2 / Pulse Ox** | Pulse Ox Summaries | All-day monitoring averages and on-demand single measurements |
| **Respiration Rate** | Respiration Summaries | Per-minute recording; gaps during activity or when watch is removed |
| **VO2 Max** | User Metrics | Algorithmically estimated; separate values for running and cycling |
| **Fitness Age** | User Metrics | Garmin's estimated fitness age based on profile |
| **Training Status / Training Readiness** | User Metrics / Advanced Health | Available via unofficial API; includes load focus, recovery time |
| **Epoch (15-min Activity Blocks)** | Epochs | High-resolution all-day activity windows: steps, intensity, HR |
| **Activity Summaries** | Activities | Per-workout: sport type, duration, distance, avg/max HR, pace, cadence, power, elevation |
| **Activity Details** | Activity Details | Full GPS track + per-second sensor data for recorded workouts |
| **Move IQ Events** | Move IQ | Auto-detected activity bouts (walking, running, cycling) without user starting a workout |
| **Sleep Respiration** | Sleep / Respiration Summaries | Respiration rate during sleep; useful for sleep quality analysis |
| **Health Snapshot** | Health Snapshot Summaries | Spot-check combining HR, HRV, SpO2, respiration, stress in a single on-demand capture |
| **Blood Pressure** | Unofficial API | Requires compatible device or manual entry |
| **Hydration** | Unofficial API | Manual hydration logging data |

---

## Authentication

### Official Health API
- Uses **OAuth 1.0a** (not OAuth 2.0) — requires HMAC-SHA1 request signing, nonces, timestamps, and a multi-step token exchange.
- Flow: Partner registers → gets Consumer Key + Consumer Secret → user redirected to Garmin Connect to grant consent → access token returned.
- Tokens persist until user revokes access.
- Libraries like `requests-oauthlib` can handle the complexity.

### Unofficial API
- **Session-based cookie authentication** — logs in with Garmin Connect username/password via the `garth` library for SSO.
- No OAuth involved. Sensitive: credentials must be stored carefully; Garmin MFA can complicate automation.

---

## Data Architecture: Push vs. Pull (Official API)

- **Ping/Pull**: Garmin sends an HTTPS POST "ping" notification to a partner webhook URL when new data is available. The ping contains a callback URL to fetch the actual data. Near-real-time but requires two round trips.
- **Push**: Garmin sends the full summary data directly in the POST notification body. Simpler — no callback needed.

Both patterns available for Health API and Activity API.

---

## Rate Limits (Official API)

| Level | Requests/minute (partner) | Requests/day (per user) |
|---|---|---|
| Evaluation | 100 | 200 |
| Production | 6,000 | 6,000 |

- HTTP 429 returned when limits are exceeded.
- The unofficial API also triggers rate limiting from Garmin's web infrastructure — aggressive polling causes 429 errors.

---

## Data Freshness & Retention

- **Data freshness**: Data is only available after the user syncs their device (via mobile app or USB). No real-time streaming — data is batch-uploaded on sync. Most users sync once or a few times per day.
- **Retention**: The Health API retains user data for only **7 days** from upload. Push/ping notifications are queued for up to 7 days then dropped if not consumed.
- **Backfill**: Partners can request historical data up to **90 days** per request (multiple requests allowed). Backfill is asynchronous — data arrives via normal push/ping when ready.

---

## Notable Limitations & Caveats

1. **Device dependency**: Many advanced metrics (HRV status, overnight SpO2, advanced sleep stages, sleep score, respiration) require newer, higher-end devices (Fenix 7/8, Forerunner 955/965/165, Epix, Venu 3, etc.). Budget/older devices lack many of these sensors.

2. **Enterprise-only official access**: The Health API is explicitly for businesses. Solo developers or researchers without a formal company entity are unlikely to be approved. The developer forum confirms Garmin has rejected independent developers working on personal projects.

3. **No live/real-time data**: There is no WebSocket or streaming API. All data is sync-dependent.

4. **Unofficial API stability risk**: The reverse-engineered approach has broken multiple times when Garmin updated their web app or authentication flow. Garmin has also taken steps to limit third-party app access at various points.

5. **Body composition data quality**: Detailed body composition (fat %, muscle mass, etc.) is only as accurate as the measurement source — the Garmin Index S2 smart scale uses bioelectrical impedance, which has known accuracy limitations.

6. **HRV during activity**: HRV data has gaps during exercise since optical HR sensors can't reliably measure beat-to-beat variations during motion. The overnight-only approach for HRV status is by design.

7. **OAuth 1.0a complexity**: The older auth standard is a barrier for modern integrations compared to OAuth 2.0 bearer tokens.

---

## Recommendation for This Project

Given the personal-use nature of this project, the **unofficial `python-garminconnect` library** is the most practical path. It supports all four target biometrics (resting HR, HRV, sleep, weight) plus the additional metrics above. The key risks are stability (Garmin can break it) and rate limiting.

**Body Battery** is worth highlighting as a particularly relevant metric for readiness scoring — it is Garmin's own synthesis of HRV, stress, sleep quality, and activity into a 0–100 energy reserve score, and could serve as a useful input or cross-validation signal.

---

## Sources

- [Garmin Connect Developer Program – Health API](https://developer.garmin.com/gc-developer-program/health-api/)
- [Garmin Connect Developer Program – Overview](https://developer.garmin.com/gc-developer-program/)
- [HRV Summaries now available for Health API – Garmin Developer Blog](https://developerportal.garmin.com/blog/hrv-summaries-are-now-available-health-api)
- [Sleep Scores Available for Supported Devices – Garmin Developer Blog](https://developerportal.garmin.com/blog/sleep-scores-available-supported-devices)
- [Health Snapshot Summary Type – Garmin Developer Blog](https://developerportal.garmin.com/blog/new-health-api-summary-type-%E2%80%93-health-snapshot)
- [GitHub – cyberjunky/python-garminconnect](https://github.com/cyberjunky/python-garminconnect)
- [Garmin Sleep Summary Export Format – MyDataHelps](https://support.mydatahelps.org/garmin-sleep-summary-export-format)
- [Garmin Body Composition Summary Export Format – MyDataHelps](https://support.mydatahelps.org/garmin-body-composition-summary-export-format)
- [Garmin HRV Summary Export Format – MyDataHelps](https://support.mydatahelps.org/garmin-heart-rate-variability-summary-export-format)
- [Garmin Health API Data – Daily Summary – ilumivu](https://ilumivu.freshdesk.com/support/solutions/articles/9000258793-garmin-health-api-data-daily-summary)
- [Terra API – Garmin Integration](https://tryterra.co/integrations/garmin)
