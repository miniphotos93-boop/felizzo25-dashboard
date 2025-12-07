#!/usr/bin/env python3
import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    print("DATABASE_URL not set. Please set it first.")
    exit(1)

conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
cur = conn.cursor()

cur.execute('''
    CREATE TABLE IF NOT EXISTS scorecards (
        id SERIAL PRIMARY KEY,
        event_idx INTEGER NOT NULL,
        scorecard_data JSONB NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(event_idx)
    )
''')

conn.commit()
cur.close()
conn.close()

print("Scorecard table created successfully!")
