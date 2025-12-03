#!/usr/bin/env python3
import json
import os
import psycopg2

DATABASE_URL = os.environ.get('DATABASE_URL')

participants = [
    {"serial_number": 1, "participant1_name": "Participant 1", "participant2_name": None, "team_name": "Team A"},
    {"serial_number": 2, "participant1_name": "Participant 2", "participant2_name": None, "team_name": "Team B"},
    {"serial_number": 3, "participant1_name": "Participant 3", "participant2_name": None, "team_name": "Team C"},
]

if DATABASE_URL:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    for p in participants:
        cur.execute('''
            INSERT INTO participants (event_idx, serial_number, participant1_name, participant2_name, team_name)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (event_idx, serial_number) DO UPDATE SET
                participant1_name = EXCLUDED.participant1_name,
                participant2_name = EXCLUDED.participant2_name,
                team_name = EXCLUDED.team_name
        ''', (10, p['serial_number'], p['participant1_name'], p['participant2_name'], p['team_name']))
    
    conn.commit()
    cur.close()
    conn.close()
    print("Migrated painting participants to database")
else:
    print("No DATABASE_URL found")
