#!/usr/bin/env python3
import os
import psycopg2

DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    print("DATABASE_URL not set")
    exit(1)

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Add new columns for rankings
cur.execute('''
    ALTER TABLE events 
    ADD COLUMN IF NOT EXISTS first_place VARCHAR(255),
    ADD COLUMN IF NOT EXISTS second_place VARCHAR(255),
    ADD COLUMN IF NOT EXISTS third_place VARCHAR(255)
''')

conn.commit()
cur.close()
conn.close()

print("✅ Added first_place, second_place, third_place columns to events table")
