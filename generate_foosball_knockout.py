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

# Generate knockout schedule
schedule = []
match_number = 1
current_date = datetime(2025, 12, 3)
time_slots = ["09:00 AM", "09:30 AM", "10:00 AM", "10:30 AM", "11:00 AM", "11:30 AM", 
              "12:00 PM", "12:30 PM", "02:00 PM", "02:30 PM", "03:00 PM", "03:30 PM",
              "04:00 PM", "04:30 PM", "05:00 PM", "05:30 PM"]

group_winners = []

# Phase 1: Within-group knockouts
for team_name, team_pairs in sorted(teams.items()):
    if len(team_pairs) == 1:
        group_winners.append(team_pairs[0])
        continue
    
    remaining = team_pairs[:]
    round_num = 1
    
    while len(remaining) > 1:
        next_round = []
        for i in range(0, len(remaining), 2):
            if i + 1 < len(remaining):
                schedule.append({
                    "match_number": match_number,
                    "date": current_date.strftime("%Y-%m-%d"),
                    "time": time_slots[len(schedule) % len(time_slots)],
                    "pair1_team": remaining[i]["team_name"],
                    "pair1_p1": remaining[i]["participant1_name"],
                    "pair1_p2": remaining[i]["participant2_name"],
                    "pair2_team": remaining[i+1]["team_name"],
                    "pair2_p1": remaining[i+1]["participant1_name"],
                    "pair2_p2": remaining[i+1]["participant2_name"],
                    "round": f"{team_name} - Round {round_num}",
                    "table": "Table 1"
                })
                match_number += 1
                next_round.append({"team_name": team_name, "participant1_name": "Winner", "participant2_name": f"Match {match_number-1}"})
                
                if len(schedule) % 8 == 0:
                    current_date += timedelta(days=1)
                    while current_date.weekday() >= 5:
                        current_date += timedelta(days=1)
            else:
                next_round.append(remaining[i])
        
        remaining = next_round
        round_num += 1
    
    if remaining:
        group_winners.append(remaining[0])

# Phase 2: Final knockout with group winners
remaining = group_winners[:]
round_num = 1

while len(remaining) > 1:
    next_round = []
    for i in range(0, len(remaining), 2):
        if i + 1 < len(remaining):
            schedule.append({
                "match_number": match_number,
                "date": current_date.strftime("%Y-%m-%d"),
                "time": time_slots[len(schedule) % len(time_slots)],
                "pair1_team": remaining[i]["team_name"],
                "pair1_p1": remaining[i]["participant1_name"],
                "pair1_p2": remaining[i]["participant2_name"],
                "pair2_team": remaining[i+1]["team_name"],
                "pair2_p1": remaining[i+1]["participant1_name"],
                "pair2_p2": remaining[i+1]["participant2_name"],
                "round": f"Finals - Round {round_num}",
                "table": "Table 1"
            })
            match_number += 1
            next_round.append({"team_name": "Finals", "participant1_name": "Winner", "participant2_name": f"Match {match_number-1}"})
            
            if len(schedule) % 8 == 0:
                current_date += timedelta(days=1)
                while current_date.weekday() >= 5:
                    current_date += timedelta(days=1)
        else:
            next_round.append(remaining[i])
    
    remaining = next_round
    round_num += 1

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

print(f"Generated {len(schedule)} knockout matches across {len(day_list)} days")
print(f"Group stage: {len([m for m in schedule if 'Finals' not in m['round']])} matches")
print(f"Finals stage: {len([m for m in schedule if 'Finals' in m['round']])} matches")
