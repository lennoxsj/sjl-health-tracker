# Initial design document for Sarah's health tracker
## What I want to build
Create a health dashboard that consolidates data from various wearables and third party sights, biometrics and sleep data. The dashboard should also have a list of recent activities with estimated load scores and indications of improvement or decline in performance. There should be an algorithm to compute a Mettle Index (my proprietary "Readiness Score"). Along with the Mettle Index, the dashboard should take into account personal goals and some other restrictions (e.g. ideal activity frequency and diversity) to suggest a workout for tomorrow with primary and secondary options. Code should be Python wherever possible, and C++ as an alternative. I want to be able to put the code in Github and I want anyone with access to my Github to be able to see the dashboard, but not to make changes. I'm not sure where to keep the data in order to allow Github viewers to see it. Data should be manually synced by me each morning after I have gotten out of bed (so we have sleep data). If I don't sync manually, it should automatically sync at 9:00am each day. I
## Layout
The primary tab on the dashboard should be titled "Sarah's health tracker" and should include:
- Progress vs. each quarterly goal
- Biometrics
- Mettle Index
- Activity suggestions
Other tabs should be:
- Activity log
- Goals
## Data sources
- Garmin Fēnix 8 
- Garmin scale: We should only use my total weight from this (not body fat percentage etc)
- Ōura ring
- Eight Sleep
- Karoo II Hammerhead bike computer
- Strava: My Fēnix 8 and Karoo II both sync to Strava
- MyFitBod: Does not sync anywhere. I record my strength workouts on my Fēnix 8 (so they sync to Strava). The Fēnix 8/Strava recordings will have heart rate data. MyFitBod will have volume of weight lifted data.
- BodySpec: I get DEXA scans that tell me my weight, kgs of body fat and kgs of lean mass. I think this might have to be entered manually. Start with 22kg of body fat and 40kg of lean mass.
## Activity log
This should be a separate tab that includes all my recorded activities. This is how I record activities:
- Road biking: Usually recorded in my Hammerhead Karoo II and syncs to Strava. Occasionally recorded on my Garmin Fēnix 8, which also syncs to Strava.
- Gravel biking: Same as road biking.
- Mountain biking: Garmin Fēnix 8 and synced to Strava.
- Running, Hiking and Walking (specifically recorded walks, not just walking around): Garmin Fēnix 8 and synced to Strava. My Ōura ring will often also catch these, but I usually forget to accept it as an activity so I'm not sure whether it ends up on the Ōura log. I don't think Ōura syncs to Strava.
- Rowing and Swimming: Garmin Fēnix 8 and synced to Strava.
- Strength training: Garmin Fēnix 8 and synced to Strava. Garmin will have heart rate data, but I use an app called MyFitBod to log workouts and that app has better data on what kind of workout (Legs, Push, Pull or All-Body for anything not labelled) and on load total volume of weight lifted which I'd like to include.
- Steps counter: We should have a line item each day as a steps counter that takes steps data from Garmin, but removes any steps taken during specifically recorded Running, Hiking and Walking activities.
- I want to include three additional data points that we will calculate for each (relevant) activity:
	- Steepness index: This applies to road biking, mountain biking and gravel biking. Divide Elevation Gain by Distance. Keep them in their own units and round to the nearest whole number. If my elevation Gain for a ride is 814m and my Distance is 57.65km, the score should be 14.
	- Grade adjusted pace for road biking and mountain biking: For each point in the Steepness index, add 0.1km/hour to the average moving speed.
	- Activity load score: Make this a placeholder for now with a random score between 0-100 assigned to each activity in the log. I need to work on the algorithm for the load score. Claude: If you think you can do a more educated job of than random, please assign a score between 0-100, with 100 being an extremely high activity load.
- For all activities, I want to make sure we don't include duplicates, so Strava should have precedence, but we can fill data gaps in where necessary. 
## Goals
A tab for me to input quarterly goals for activity frequency for each of my activities, and a few more specific metrics (below). It should have a progress field.
- Distance (i.e. kilometres ridden and elevation climbed in biking). Progress should accumulate over the quarter from data pulled into the activities log. For the current quarter (April-June 2026), set this to 1,300km of distance and 13,000 meters of climbing. This can be achieved through any mix of road biking, gravel biking and mountain biking. 
- Grade adjusted pace for road biking. Progress should be the average grade adjusted pace for the last three road bike rides. Set this to 22km/hour for now.
- Distance and 100m pace for swimming. Progress should accumulate over the quarter from data pulled into the activities log. Pace should be the average 100m pace for the last three swims. For the current quarter, set this to 26km of distance and 2:30/100m pace.
- Back squat weight for 8 reps. Progress should be the heaviest I have lifted for 8 (or more) back squats in the quarter, not necessarily the most recent time I did a backsquat. For the current quarter, set this to 90 pounds.
- Body composition: Specific weight goal with progress recorded as my average weight at the last three recordings in Garmin. Body fat in kilograms: Specific goal with progress recorded manually from my DEXA scans. Lean mass: Specific goal with progress recorded manually from my DEXA scans which I get at BodySpec. For the current quarter, set this to 68kg of weight, 19kg of body fat, 41kg lean mass.
- Sleep: Full night's sleep (FNS) -- this should be a slider between 7-10 hours. Set to 8.5 hours to start.
## Biometrics
- Resting heart rate: This should be last night's and an arrow indicating whether it was above/below 7-day rolling average. Average of Eight Sleep, Garmin and Ōura data. Average data sources should match the source(s) of last night's data, i.e. if we only have Eight Sleep data for last night because I didn't wear my Ōura or Garmin, we should only use Eight Sleep data for the 7-night average too.
- HRV (overnight): This should be last night's and an arrow indicating whether it was above/below 7-day rolling average. Average of Eight Sleep, Garmin and Ōura data. Average data sources should match the source(s) of last night's data, i.e. if we only have Eight Sleep data for last night because I didn't wear my Ōura or Garmin, we should only use Eight Sleep data for the 7-night average too.
- Breath rate: From Eight Sleep. This should be last night's and an arrow indicating whether it was above/below 7-day rolling average, and whether it was in the optimal range.
- Heart and Breathing Score:
	- Equal weight to most recent resting heart rate, HRV and respiratory rate/breath rate. For each metric, anything between two levels should be calculated linearly and rounded to the nearest whole point (lowest score = 0, highest score = 100). Note that low scores can be achieved with numbers that are too low and numbers that are too high.
	- Resting heart rate:
		- Last night's data -30bpm or more vs. 7-day rolling average: 0
		- Last night's data -5bpm vs. 7-day rolling average: 100
		- Last night's data +5bpm vs. 7-day rolling average: 80
		- Last night's data +20bpm or more vs. 7-day rolling average: 0
	- HRV (last night's data):
		- 0ms: 0
		- 60ms: 60
		- 70-90ms: 100
		- 120ms: 50
		- More than 120ms: 0
	- Breath (last night's data):
		- 0bpm: 0
		- 13-15bpm: 100
		- 20bpm: 80
		- 40bpm or more: 0
- Recent activity load: Most recent, as well as rolling 3-day average. This should come from data in the activity log. For example, if I do a short run (example load score of 15) plus a lifting session (example load score of 55) and my steps for that day count as a load score of 10, then the most recent "recent activity load" should be 80.
- VO2 max estimate: Data from Garmin. This should be current and also an up/down arrow vs. data from a month ago.
- Sleep data:
	- Total time asleep: Average of Eight Sleep, Ōura and Garmin. If one ore more sources is not available, average only what is available.
	- Deep sleep (minutes): Average of Eight Sleep, Ōura and Garmin. If one ore more sources is not available, average only what is available. Include last night's data and also the rolling 3-night average. Average data sources should match the source(s) of last night's data, i.e. if we only have Eight Sleep data for last night because I didn't wear my Ōura or Garmin, we should only use Eight Sleep data for the 3-night average too.
	- REM sleep (minutes): Average of Eight Sleep, Ōura and Garmin. If one ore more sources is not available, average only what is available. Include last night's data and also the rolling 3-night average. Average data sources should match the source(s) of last night's data, i.e. if we only have Eight Sleep data for last night because I didn't wear my Ōura or Garmin, we should only use Eight Sleep data for the 3-night average too.
	- Sleep interruptions: Eight Sleep metric
	- Sleep score: Let's calculate this as a score between 0-100 with the following specifics:
		- Total time asleep: 40% weight
			- Less than 40% of FNS: 0
			- 40% of FNS: 10
			- 120% of FNS or more: 100 points
			- Anything between two levels should be calculated linearly and rounded to the nearest whole point (lowest score = 0, highest score = 100).
		- Deep sleep: 25% weight
			- 0% of FNS: 0
			- 15% of FNS: 80
			- 25% of FNS: 100
			- 30% of FNS: 95
			- 100% of FNS: 0
			- Anything between two levels should be calculated linearly and rounded to the nearest whole point (lowest score = 0, highest score = 100). Please note that a lower score can be achieved by too little OR too much deep sleep. 
		- REM sleep: 20% weight
			- 0% of FNS: 0
			- 10% of FNS: 50
			- 20% of FNS: 90
			- 22.5% of FNS: 100
			- 25% of FNS: 90
			- 50% of FNS: 25
			- More than 50% of FNS: 0
			- Anything between two levels should be calculated linearly and rounded to the nearest whole point (lowest score = 0, highest score = 100). Please note that a lower score can be achieved by too little OR too much REM sleep. 
		- Sleep interruptions: 15% weight
			- 0 minutes: 100
			- 10 minutes: 90
			- 60 minutes: 50
			- 120 minutes: 25
			- More than 120 minutes: 0
			- Anything between two levels should be calculated linearly and rounded to the nearest whole point (lowest score = 0, highest score = 100).
		- We should show the weights on the dashboard near the score.

## Mettle Index and activity suggestions
We should compute a Mettle Index between 0 and 100 for the day. It should take into account:
- Sleep Score: 40% weight
	- Higher score = better, so if Sleep Score = 100, 100 x 40% = 40 points should be assigned to the Mettle Index.
- Heart and Breathing Score: 30% weight
	- Higher score = better, so if Heart and Breathing Score = 100, 100 x 30% = 30 points should be assigned to the Mettle Index.
- Recent activity load: 30%
	- Use 3-day average for this, not just yesterday's activity load
	- Higher score = worse. If the 3-day average activity load is 100, we should assign 0. If the 3-day average activity load is 0, we should assign 100 x 30% = 30 points.
- Activity suggestions:
	- Once we have a Mettle Index, the dashboard should suggest two activities that have an activity load score within +/- 7 points of the Mettle Index. For example, if my Mettle Index is 70, the dashboard should make a sublist of any activities in my log with an activity load between 63 and 77, and should suggest two of them at random. We don't need to keep the sublist anywhere.
## Future plans (v3)
- Machine Learning: Incorporate actual performance during activities into Mettle Index
- Cycle tracking and impact: Incorporate hormonal fluctuations into Mettle Index
- Include goal progress into activity suggestions
- Minutes in zone 5, 6, 7 per week to be included in Mettle Index.