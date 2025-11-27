import psycopg2
import json
import os

# Get database URL from environment
DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    print("DATABASE_URL not set, skipping database initialization")
    exit(0)

# Connect to database
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Create events table
cur.execute('''
    CREATE TABLE IF NOT EXISTS events (
        id SERIAL PRIMARY KEY,
        event_name VARCHAR(255) UNIQUE NOT NULL,
        coordinator VARCHAR(255),
        manager VARCHAR(255),
        start_date VARCHAR(50),
        end_date VARCHAR(50),
        finals_date VARCHAR(50),
        status VARCHAR(50),
        participants VARCHAR(50),
        winner VARCHAR(255),
        notes TEXT
    )
''')

# Load initial data from JSON
with open('event_tracker.json') as f:
    events = json.load(f)

# Insert events if table is empty
cur.execute('SELECT COUNT(*) FROM events')
if cur.fetchone()[0] == 0:
    for event in events:
        cur.execute('''
            INSERT INTO events (event_name, coordinator, manager, start_date, end_date, 
                              finals_date, status, participants, winner, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            event['Event'],
            event.get('Coordinator', ''),
            event.get('Manager', ''),
            event.get('Start_Date', ''),
            event.get('End_Date', ''),
            event.get('Finals_Date', ''),
            event.get('Status', 'Planned'),
            event.get('Participants', ''),
            event.get('Winner', ''),
            event.get('Notes', '')
        ))
    print(f"Inserted {len(events)} events")

conn.commit()
cur.close()
conn.close()
print("Database initialized successfully")
