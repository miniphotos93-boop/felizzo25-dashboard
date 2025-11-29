import json
from datetime import datetime, timedelta
from itertools import combinations
from collections import defaultdict

# Load chess participants
with open('participants_data/event_1.json') as f:
    participants = json.load(f)

# Group by team
teams = defaultdict(list)
for p in participants:
    teams[p['team_name']].append(p['participant1_name'])

# Generate matches
matches = []
match_id = 1

# Round-robin within each team (4+ players)
for team, players in teams.items():
    if len(players) >= 4:
        for p1, p2 in combinations(players, 2):
            matches.append({
                'match_id': f'{team.replace(" ", "_")}_M{match_id}',
                'team': team,
                'player1': p1,
                'player2': p2,
                'date': None,
                'winner': None
            })
            match_id += 1

# Combined group for teams with <4 players
small_teams_players = []
for team, players in teams.items():
    if len(players) < 4:
        for player in players:
            small_teams_players.append({'name': player, 'team': team})

if small_teams_players:
    for i, p1 in enumerate(small_teams_players):
        for p2 in small_teams_players[i+1:]:
            matches.append({
                'match_id': f'Combined_M{match_id}',
                'team': 'Combined',
                'player1': f"{p1['name']} ({p1['team']})",
                'player2': f"{p2['name']} ({p2['team']})",
                'date': None,
                'winner': None
            })
            match_id += 1

print(f"Total matches: {len(matches)}")

# Distribute matches across days (starting Nov 25, 2024)
start_date = datetime(2024, 11, 25)
matches_per_day = 6  # 3 matches per table, 2 tables
current_date = start_date
match_index = 0

# Track which players have played on each day
daily_players = defaultdict(set)

while match_index < len(matches):
    # Skip weekends
    if current_date.weekday() >= 5:
        current_date += timedelta(days=1)
        continue
    
    date_str = current_date.strftime('%Y-%m-%d')
    assigned_today = 0
    
    # Try to assign matches for this day
    for i in range(match_index, len(matches)):
        if assigned_today >= matches_per_day:
            break
        
        match = matches[i]
        p1 = match['player1'].split(' (')[0]  # Remove team suffix if present
        p2 = match['player2'].split(' (')[0]
        
        # Check if either player already played today
        if p1 not in daily_players[date_str] and p2 not in daily_players[date_str]:
            match['date'] = date_str
            daily_players[date_str].add(p1)
            daily_players[date_str].add(p2)
            assigned_today += 1
            
            # Swap this match to the current position
            matches[match_index], matches[i] = matches[i], matches[match_index]
            match_index += 1
    
    # If we couldn't assign any matches, move to next day
    if assigned_today == 0:
        match_index += 1
    
    current_date += timedelta(days=1)

# Save schedule
with open('chess_schedule.json', 'w') as f:
    json.dump(matches, f, indent=2)

print(f"Schedule created with {len(matches)} matches")
print(f"Days needed: {len(daily_players)}")
print(f"End date: {max(daily_players.keys())}")
