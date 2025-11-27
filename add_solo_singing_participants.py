import json
from pathlib import Path

participants_dir = Path("participants_data")
participants_dir.mkdir(exist_ok=True)

solo_singing_participants = [
    {"serial_number": 1, "participant1_name": "Hamirth", "participant2_name": None, "team_name": "3P Team"},
    {"serial_number": 2, "participant1_name": "Abitha", "participant2_name": None, "team_name": "FBDA"},
    {"serial_number": 3, "participant1_name": "Kalaivani", "participant2_name": None, "team_name": "3papps"},
    {"serial_number": 4, "participant1_name": "Vignesh", "participant2_name": None, "team_name": "Sysapps"},
    {"serial_number": 5, "participant1_name": "Swarnali", "participant2_name": None, "team_name": "FBDA"},
    {"serial_number": 6, "participant1_name": "Bavadharani", "participant2_name": None, "team_name": "Vega"},
    {"serial_number": 7, "participant1_name": "Haripriya", "participant2_name": None, "team_name": "3p Apps"},
    {"serial_number": 8, "participant1_name": "Sangeetha", "participant2_name": None, "team_name": "Mobile"},
    {"serial_number": 9, "participant1_name": "Kirthiga", "participant2_name": None, "team_name": "Sysapps"},
    {"serial_number": 10, "participant1_name": "Mano priya", "participant2_name": None, "team_name": "Launcher"},
    {"serial_number": 11, "participant1_name": "Atshara", "participant2_name": None, "team_name": "3p Apps"},
]

# Solo Singing is event index 16
with open(participants_dir / "event_16.json", "w") as f:
    json.dump(solo_singing_participants, f, indent=2)

print(f"Added {len(solo_singing_participants)} Solo Singing participants!")
