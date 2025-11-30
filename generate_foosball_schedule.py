import json
from itertools import combinations
from datetime import datetime, timedelta
from pathlib import Path

# Load participants
participants_file = Path("participants_data/event_4.json")
with open(participants_file) as f:
    pairs = json.load(f)

print(f"Total pairs: {len(pairs)}")

# Generate all possible matches (round-robin)
all_matches = []
match_num = 1

for i, j in combinations(range(len(pairs)), 2):
    pair1 = pairs[i]
    pair2 = pairs[j]
    
    # Skip if same people (case-insensitive check)
    p1_names = f"{pair1['participant1_name']}_{pair1['participant2_name']}".lower()
    p2_names = f"{pair2['participant1_name']}_{pair2['participant2_name']}".lower()
    p2_names_rev = f"{pair2['participant2_name']}_{pair2['participant1_name']}".lower()
    
    if p1_names == p2_names or p1_names == p2_names_rev:
        continue
    
    all_matches.append({
        'match_id': f"M{match_num}",
        'match_number': match_num,
        'pair1_num': pair1['serial_number'],
        'pair1_p1': pair1['participant1_name'],
        'pair1_p2': pair1['participant2_name'],
        'pair1_team': pair1['team_name'],
        'pair2_num': pair2['serial_number'],
        'pair2_p1': pair2['participant1_name'],
        'pair2_p2': pair2['participant2_name'],
        'pair2_team': pair2['team_name'],
        'group': f"{pair1['team_name']} vs {pair2['team_name']}"
    })
    match_num += 1

print(f"Total matches generated: {len(all_matches)}")

# Distribute matches across days (30 matches per day)
matches_per_day = 30
start_date = datetime(2025, 11, 27)

schedule = []
remaining_matches = all_matches.copy()
day_num = 0

while remaining_matches:
    current_date = start_date + timedelta(days=day_num)
    day_matches = []
    used_pairs = set()
    
    # Try to fill 30 matches for the day
    for match in remaining_matches[:]:
        if len(day_matches) >= matches_per_day:
            break
        
        pair1_id = match['pair1_num']
        pair2_id = match['pair2_num']
        
        # Check if either pair already played today
        if pair1_id not in used_pairs and pair2_id not in used_pairs:
            day_matches.append(match)
            used_pairs.add(pair1_id)
            used_pairs.add(pair2_id)
            remaining_matches.remove(match)
    
    # If we couldn't fill 30 matches without conflicts, add remaining
    while len(day_matches) < matches_per_day and remaining_matches:
        match = remaining_matches.pop(0)
        day_matches.append(match)
    
    if day_matches:
        schedule.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'day_name': current_date.strftime('%A, %B %d'),
            'matches': day_matches
        })
        day_num += 1

print(f"Total days: {len(schedule)}")
for day in schedule[:3]:
    print(f"  {day['day_name']}: {len(day['matches'])} matches")

# Save schedule
with open('foosball_day_schedule.json', 'w') as f:
    json.dump(schedule, f, indent=2)

print("Foosball schedule generated successfully!")
