import os
import json
import psycopg2
from psycopg2.extras import Json

# Database connection
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:Stupefy$12345@db.kgrkjoonpgqrzawbonen.supabase.co:5432/postgres')

def setup_database():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Create tables
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
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS match_results (
            id SERIAL PRIMARY KEY,
            event_name VARCHAR(255) NOT NULL,
            match_id VARCHAR(255) NOT NULL,
            winner INTEGER,
            UNIQUE(event_name, match_id)
        )
    ''')
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS time_slots (
            id SERIAL PRIMARY KEY,
            event_name VARCHAR(255) NOT NULL,
            match_id VARCHAR(255) NOT NULL,
            time_slot VARCHAR(50),
            UNIQUE(event_name, match_id)
        )
    ''')
    
    conn.commit()
    print("✅ Database tables created successfully")
    
    # Migrate existing data
    migrate_events(cur, conn)
    migrate_results(cur, conn)
    
    cur.close()
    conn.close()

def migrate_events(cur, conn):
    try:
        with open('event_tracker.json') as f:
            events = json.load(f)
        
        for event in events:
            cur.execute('''
                INSERT INTO events (event_name, coordinator, manager, start_date, end_date, 
                                  finals_date, status, participants, winner, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (event_name) DO UPDATE SET
                    coordinator = EXCLUDED.coordinator,
                    manager = EXCLUDED.manager,
                    start_date = EXCLUDED.start_date,
                    end_date = EXCLUDED.end_date,
                    finals_date = EXCLUDED.finals_date,
                    status = EXCLUDED.status,
                    participants = EXCLUDED.participants,
                    winner = EXCLUDED.winner,
                    notes = EXCLUDED.notes
            ''', (
                event['Event'], event.get('Coordinator', ''), event.get('Manager', ''),
                event.get('Start_Date', ''), event.get('End_Date', ''), event.get('Finals_Date', ''),
                event.get('Status', 'Planned'), event.get('Participants', ''),
                event.get('Winner', ''), event.get('Notes', '')
            ))
        
        conn.commit()
        print(f"✅ Migrated {len(events)} events")
    except Exception as e:
        print(f"⚠️  Event migration: {e}")

def migrate_results(cur, conn):
    result_files = {
        'Foosball': 'foosball_results.json',
        'Carrom': 'carrom_results.json',
        'Chess': 'chess_results.json',
        'Tug of War': 'tug_of_war_results.json',
        'Seven Stones': 'seven_stones_results.json'
    }
    
    total = 0
    for event_name, filename in result_files.items():
        try:
            with open(filename) as f:
                results = json.load(f)
            
            for match_id, winner in results.items():
                cur.execute('''
                    INSERT INTO match_results (event_name, match_id, winner)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (event_name, match_id) DO UPDATE SET winner = EXCLUDED.winner
                ''', (event_name, match_id, winner))
                total += 1
            
            conn.commit()
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"⚠️  {event_name} results: {e}")
    
    print(f"✅ Migrated {total} match results")

if __name__ == '__main__':
    setup_database()
