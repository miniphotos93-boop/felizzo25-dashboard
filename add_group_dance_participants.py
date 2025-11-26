import json
from pathlib import Path

participants_dir = Path("participants_data")
participants_dir.mkdir(exist_ok=True)

group_dance_participants = [
    {"serial_number": 1, "participant1_name": "Suriya, hamirth and team", "participant2_name": None, "team_name": "3p Apps"},
    {"serial_number": 2, "participant1_name": "Kalaivani, elavarasan, Atshara and team", "participant2_name": None, "team_name": "3p Apps"},
    {"serial_number": 3, "participant1_name": "Sariga, vijaylakshmi, saravaka karthik, balaji, deepak", "participant2_name": None, "team_name": "Discovery"},
    {"serial_number": 4, "participant1_name": "Muthumeenal, aarthi, sangeetha, swetha and kalpana", "participant2_name": None, "team_name": "Sysapps"},
    {"serial_number": 5, "participant1_name": "Abitha, Anchana, chareeshma, subash and vignesh", "participant2_name": None, "team_name": "Discovery"},
    {"serial_number": 6, "participant1_name": "Adhi, harish, murali, vedha, sathish, kanimozhi, hari, akash, bhava", "participant2_name": None, "team_name": "Vega"},
    {"serial_number": 7, "participant1_name": "Vanisha and team", "participant2_name": None, "team_name": "SDL"},
]

# Group Dance is event index 15
with open(participants_dir / "event_15.json", "w") as f:
    json.dump(group_dance_participants, f, indent=2)

print(f"Added {len(group_dance_participants)} Group Dance participants!")
