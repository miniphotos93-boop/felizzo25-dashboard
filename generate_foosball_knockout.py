import json
from collections import defaultdict
from datetime import datetime, timedelta

# Load participants
with open("participants_data/event_4.json") as f:
    participants = json.load(f)

# Group by team
teams = defaultdict(list)
for p in participants:
    teams[p["team_name"]].append(p)

# Generate knockout schedule - only first round within each team
schedule = []
match_number = 1
current_date = datetime(2025, 12, 3)
time_slots = ["09:00 AM", "09:30 AM", "10:00 AM", "10:30 AM", "11:00 AM", "11:30 AM", 
              "12:00 PM", "12:30 PM", "02:00 PM", "02:30 PM", "03:00 PM", "03:30 PM",
              "04:00 PM", "04:30 PM", "05:00 PM", "05:30 PM"]

matches_today = 0

# Only first round knockouts within each team
for team_name, team_pairs in sorted(teams.items()):
    if len(team_pairs) <= 1:
        continue
    
    # Pair them up for first round only
    for i in range(0, len(team_pairs), 2):
        if i + 1 < len(team_pairs):
            schedule.append({
                "match_id": f"foosball_{match_number}",
                "match_number": match_number,
                "date": current_date.strftime("%Y-%m-%d"),
                "time": time_slots[matches_today % len(time_slots)],
                "pair1_team": team_pairs[i]["team_name"],
                "pair1_p1": team_pairs[i]["participant1_name"],
                "pair1_p2": team_pairs[i]["participant2_name"],
                "pair2_team": team_pairs[i+1]["team_name"],
                "pair2_p1": team_pairs[i+1]["participant1_name"],
                "pair2_p2": team_pairs[i+1]["participant2_name"],
                "round": f"{team_name} - Round 1",
                "table": "Table 1"
            })
            match_number += 1
            matches_today += 1
            
            if matches_today >= 8:
                current_date += timedelta(days=1)
                while current_date.weekday() >= 5:
                    current_date += timedelta(days=1)
                matches_today = 0

# Save schedule
with open("foosball_schedule.json", "w") as f:
    json.dump(schedule, f, indent=2)

# Create day-wise schedule
day_schedule = defaultdict(lambda: {"date": "", "matches": []})
for match in schedule:
    date = match["date"]
    if not day_schedule[date]["date"]:
        day_schedule[date]["date"] = date
    day_schedule[date]["matches"].append(match)

day_list = [day_schedule[date] for date in sorted(day_schedule.keys())]

with open("foosball_day_schedule.json", "w") as f:
    json.dump(day_list, f, indent=2)

print(f"Generated {len(schedule)} first-round knockout matches across {len(day_list)} days")
