#!/usr/bin/env python3
import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get('DATABASE_URL') or input("Enter DATABASE_URL: ")

conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
cur = conn.cursor()

cur.execute('SELECT * FROM participants WHERE event_idx = 10 ORDER BY serial_number')
rows = cur.fetchall()

print(f"\nFound {len(rows)} painting participants:")
for row in rows:
    print(f"  {row['serial_number']}. {row['participant1_name']} - {row['team_name']}")

cur.close()
conn.close()
