#!/usr/bin/env python3
import json
from pathlib import Path

participants = [
    {"serial_number": 1, "participant1_name": "Participant 1", "participant2_name": None, "team_name": "Team A"},
    {"serial_number": 2, "participant1_name": "Participant 2", "participant2_name": None, "team_name": "Team B"},
    {"serial_number": 3, "participant1_name": "Participant 3", "participant2_name": None, "team_name": "Team C"},
]

file_path = Path(__file__).parent / "participants_data" / "participants_10.json"
file_path.parent.mkdir(exist_ok=True)

with open(file_path, 'w') as f:
    json.dump(participants, f, indent=2)

print(f"Added {len(participants)} participants for Painting event")
