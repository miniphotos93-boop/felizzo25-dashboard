import json
from itertools import combinations
from datetime import datetime, timedelta
from pathlib import Path

def generate_schedule(event_name, event_idx, start_date_str, matches_per_day=30):
    # Load participants
    participants_file = Path(f"participants_data/event_{event_idx}.json")
    with open(participants_file) as f:
        pairs = json.load(f)
    
    print(f"\n{event_name}:")
    print(f"  Total pairs: {len(pairs)}")
    
    # Generate all possible matches (round-robin)
    all_matches = []
    match_num = 1
    
    for i, j in combinations(range(len(pairs)), 2):
        pair1 = pairs[i]
        pair2 = pairs[j]
        
        all_matches.append({
            'match_id': f"M{match_num}",
            'match_number': match_num,
            'date': '',  # Will be set during distribution
            'player1': f"{pair1['participant1_name']} & {pair1['participant2_name']}",
            'player2': f"{pair2['participant1_name']} & {pair2['participant2_name']}",
            'pair1_num': pair1['serial_number'],
            'pair1_team': pair1['team_name'],
            'pair2_num': pair2['serial_number'],
            'pair2_team': pair2['team_name']
        })
        match_num += 1
    
    print(f"  Total matches: {len(all_matches)}")
    
    # Distribute matches across days
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    schedule = []
    remaining_matches = all_matches.copy()
    day_num = 0
    
    while remaining_matches:
        current_date = start_date + timedelta(days=day_num)
        day_matches = []
        used_pairs = set()
        
        # Try to fill matches for the day without back-to-back
        for match in remaining_matches[:]:
            if len(day_matches) >= matches_per_day:
                break
            
            pair1_id = match['pair1_num']
            pair2_id = match['pair2_num']
            
            if pair1_id not in used_pairs and pair2_id not in used_pairs:
                match['date'] = current_date.strftime('%Y-%m-%d')
                day_matches.append(match)
                used_pairs.add(pair1_id)
                used_pairs.add(pair2_id)
                remaining_matches.remove(match)
        
        # Fill remaining slots if needed
        while len(day_matches) < matches_per_day and remaining_matches:
            match = remaining_matches.pop(0)
            match['date'] = current_date.strftime('%Y-%m-%d')
            day_matches.append(match)
        
        if day_matches:
            schedule.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'day_name': current_date.strftime('%A, %B %d'),
                'matches': day_matches
            })
            day_num += 1
    
    print(f"  Total days: {len(schedule)}")
    
    # Save schedule
    filename = f"{event_name.lower().replace(' ', '_')}_schedule.json"
    with open(filename, 'w') as f:
        json.dump(schedule, f, indent=2)
    
    print(f"  Saved to {filename}")

# Generate Snookers schedule (event 2)
generate_schedule('Snookers', 2, '2025-11-25', matches_per_day=30)

# Generate TT schedule (event 3)
generate_schedule('TT', 3, '2025-11-26', matches_per_day=30)

print("\nSchedules generated successfully!")
