import json
from pathlib import Path

participants_dir = Path("participants_data")
participants_dir.mkdir(exist_ok=True)

solo_dance_participants = [
    {"serial_number": 1, "participant1_name": "Suriya", "participant2_name": None, "team_name": "3p Apps"},
    {"serial_number": 2, "participant1_name": "Shivaprasad", "participant2_name": None, "team_name": "MOD"},
    {"serial_number": 3, "participant1_name": "Abitha", "participant2_name": None, "team_name": "FBDA"},
    {"serial_number": 4, "participant1_name": "Kalaivani", "participant2_name": None, "team_name": "3p apps"},
    {"serial_number": 5, "participant1_name": "Sariga", "participant2_name": None, "team_name": "Discovery"},
    {"serial_number": 6, "participant1_name": "sarvaik", "participant2_name": None, "team_name": "Discovery"},
    {"serial_number": 7, "participant1_name": "Balu", "participant2_name": None, "team_name": "SDL"},
]

# Solo Dance is event index 14
with open(participants_dir / "event_14.json", "w") as f:
    json.dump(solo_dance_participants, f, indent=2)

print(f"Added {len(solo_dance_participants)} Solo Dance participants!")
