#!/usr/bin/env python3
from flask import Flask, render_template, request, redirect, jsonify, session
from functools import wraps
import json
from pathlib import Path
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'  # Change this!
EVENTS_FILE = Path(__file__).parent / "event_tracker.json"
PARTICIPANTS_DIR = Path(__file__).parent / "participants_data"
PARTICIPANTS_DIR.mkdir(exist_ok=True)

DATABASE_URL = os.environ.get('DATABASE_URL')

# Database helper functions
def get_db_connection():
    if DATABASE_URL:
        try:
            return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor, connect_timeout=5)
        except:
            return None
    return None

def init_database():
    """Initialize database tables and migrate data"""
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cur = conn.cursor()
        
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
        
        # Migrate events from JSON if database is empty
        cur.execute('SELECT COUNT(*) FROM events')
        if cur.fetchone()['count'] == 0:
            try:
                with open(EVENTS_FILE) as f:
                    events = json.load(f)
                for event in events:
                    cur.execute('''
                        INSERT INTO events (event_name, coordinator, manager, start_date, end_date, 
                                          finals_date, status, participants, winner, notes)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (event_name) DO NOTHING
                    ''', (
                        event['Event'], event.get('Coordinator', ''), event.get('Manager', ''),
                        event.get('Start_Date', ''), event.get('End_Date', ''), event.get('Finals_Date', ''),
                        event.get('Status', 'Planned'), event.get('Participants', ''),
                        event.get('Winner', ''), event.get('Notes', '')
                    ))
                conn.commit()
            except:
                pass
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Database init error: {e}")

# Initialize database on startup
init_database()

# Admin users list
ADMINS = ['sharikan', 'abirajad', 'ramybabu', 'rammaka', 'saktgane', 'abhavara', 'jdpu', 'suhmohan', 'mutnur']  # Add admin usernames here

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'username' not in session or session['username'] not in ADMINS:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated

# Event type mapping
EVENT_TYPES = {
    'Carrom': 'pair', 'TT': 'pair', 'Snookers': 'pair', 'Foosball': 'pair', 'CWF': 'pair',
    'Solo Singing': 'solo', 'Solo Dance': 'solo', 'Chess': 'solo', 'Trash to Treasure': 'solo',
    'Painting': 'solo', 'Meme Creation': 'solo', 'Photography': 'solo', 'Reels': 'solo',
    'Group Singing': 'group', 'Group Dance': 'group', 'Tug of War': 'group', 
    'Seven Stones': 'group', 'Treasure Hunt': 'group'
}

def load_events():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute('SELECT * FROM events ORDER BY id')
            rows = cur.fetchall()
            cur.close()
            conn.close()
            
            events = []
            for row in rows:
                events.append({
                    'Event': row['event_name'],
                    'Coordinator': row['coordinator'],
                    'Manager': row['manager'],
                    'Start_Date': row['start_date'],
                    'End_Date': row['end_date'],
                    'Finals_Date': row['finals_date'],
                    'Status': row['status'],
                    'Participants': row['participants'],
                    'Winner': row['winner'],
                    'Notes': row['notes']
                })
            
            for event in events:
                event['event_type'] = EVENT_TYPES.get(event['Event'], 'solo')
            return events
        except:
            pass
    
    # Fallback to JSON file
    with open(EVENTS_FILE) as f:
        events = json.load(f)
    
    for event in events:
        event['event_type'] = EVENT_TYPES.get(event['Event'], 'solo')
    return events

def save_events(events):
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
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
            cur.close()
            conn.close()
            return
        except:
            pass
    
    # Fallback to JSON file
    events_to_save = []
    for event in events:
        event_copy = {k: v for k, v in event.items() if k != 'event_type'}
        events_to_save.append(event_copy)
    
    with open(EVENTS_FILE, 'w') as f:
        json.dump(events_to_save, f, indent=2)

def get_participants_file(idx):
    return PARTICIPANTS_DIR / f"event_{idx}.json"

def load_participants(idx):
    file = get_participants_file(idx)
    if file.exists():
        with open(file) as f:
            return json.load(f)
    return []

def save_participants(idx, participants):
    file = get_participants_file(idx)
    with open(file, 'w') as f:
        json.dump(participants, f, indent=2)
    
    # Auto-commit to git in production
    if os.environ.get('RENDER'):
        import subprocess
        try:
            subprocess.run(['git', 'add', str(file)], cwd=Path(__file__).parent, timeout=5)
            subprocess.run(['git', 'commit', '-m', f'Update participants for event {idx}'], 
                         cwd=Path(__file__).parent, timeout=5)
            subprocess.run(['git', 'push'], cwd=Path(__file__).parent, timeout=30)
        except:
            pass

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        if username in ADMINS:
            session['username'] = username
            return redirect('/dashboard')
        return render_template('login.html', error='Access denied. Admin only.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')

@app.route('/')
def home():
    events = load_events()
    
    # Calculate stats
    total_events = len(events)
    
    # Count total participants
    total_participants = 0
    all_teams = set()
    for idx in range(len(events)):
        participants = load_participants(idx)
        total_participants += len(participants)
        for p in participants:
            all_teams.add(p.get('team_name', ''))
    
    # Calculate total matches (rough estimate)
    total_matches = 130 + 49 + 56  # Foosball + Tug of War + Seven Stones
    
    # Build team leaderboard
    team_stats = {}
    for idx in range(len(events)):
        participants = load_participants(idx)
        for p in participants:
            team = p.get('team_name', 'Unknown')
            if team not in team_stats:
                team_stats[team] = {'events': set(), 'participants': 0, 'wins': 0}
            team_stats[team]['events'].add(events[idx]['Event'])
            team_stats[team]['participants'] += 1
    
    leaderboard = []
    for team, stats in team_stats.items():
        leaderboard.append({
            'name': team,
            'events': len(stats['events']),
            'participants': stats['participants'],
            'wins': stats['wins'],
            'participation_rate': min(100, (len(stats['events']) / total_events) * 100)
        })
    
    leaderboard.sort(key=lambda x: (x['events'], x['participants']), reverse=True)
    
    # Today's events - check for matches scheduled today
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    today_events = []
    
    schedule_files = {
        'Carrom': 'carrom_schedule.json',
        'Chess': 'chess_schedule.json',
        'Foosball': 'foosball_day_schedule.json',
        'Snookers': 'snookers_schedule.json',
        'TT': 'tt_schedule.json',
        'Seven Stones': 'sevenstones_schedule.json',
        'Tug of War': 'tugofwar_schedule.json'
    }
    
    for idx, event in enumerate(events):
        event_name = event['Event']
        has_matches_today = False
        
        if event_name in schedule_files:
            schedule_file = Path(__file__).parent / schedule_files[event_name]
            if schedule_file.exists():
                try:
                    with open(schedule_file) as f:
                        schedule_data = json.load(f)
                    
                    # Check different schedule formats
                    if event_name == 'Foosball':
                        for day in schedule_data:
                            if day.get('date') == today:
                                has_matches_today = True
                                break
                    elif event_name == 'Carrom':
                        for day in schedule_data:
                            if day.get('date') == today:
                                has_matches_today = True
                                break
                    elif event_name in ['Seven Stones', 'Tug of War']:
                        for day in schedule_data:
                            if day.get('date') == today:
                                has_matches_today = True
                                break
                    else:
                        # Snookers, TT, Chess - flat list with dates
                        for match in schedule_data:
                            if match.get('date') == today:
                                has_matches_today = True
                                break
                except:
                    pass
        
        if has_matches_today:
            today_events.append({
                'name': event_name,
                'start_date': event.get('Start_Date', ''),
                'idx': idx
            })
    
    # Event progress
    all_events_progress = []
    for idx, event in enumerate(events):
        # Load schedule to count matches
        schedule_files = {
            'Foosball': 'foosball_schedule.json',
            'Tug of War': 'tug_of_war_schedule.json',
            'Seven Stones': 'seven_stones_schedule.json',
            'Carrom': 'carrom_schedule.json',
            'Chess': 'chess_schedule.json'
        }
        
        total_matches = 0
        completed_matches = 0
        
        event_name = event['Event']
        if event_name in schedule_files:
            schedule_file = Path(__file__).parent / schedule_files[event_name]
            if schedule_file.exists():
                with open(schedule_file) as f:
                    schedule = json.load(f)
                    total_matches = len(schedule)
            
            # Load results
            results_file = Path(__file__).parent / f"{event_name.lower().replace(' ', '_')}_results.json"
            if results_file.exists():
                with open(results_file) as f:
                    results = json.load(f)
                    completed_matches = len(results)
        
        progress = int((completed_matches / total_matches * 100)) if total_matches > 0 else 0
        
        all_events_progress.append({
            'name': event['Event'],
            'status': event['Status'],
            'progress': progress,
            'completed_matches': completed_matches,
            'total_matches': total_matches
        })
    
    # Upcoming events
    upcoming_events = []
    for idx, event in enumerate(events):
        if event['Status'] in ['Planned', 'In Progress']:
            upcoming_events.append({
                'name': event['Event'],
                'date': event.get('Start_Date', 'TBD'),
                'idx': idx
            })
    
    return render_template('home.html', 
                         total_events=total_events,
                         total_participants=total_participants,
                         total_teams=len(all_teams),
                         total_matches=total_matches,
                         leaderboard=leaderboard[:10],
                         today_events=today_events,
                         all_events=all_events_progress,
                         upcoming_events=upcoming_events[:5])

@app.route('/event/<int:idx>')
@admin_required
def event_detail(idx):
    events = load_events()
    event = events[idx]
    event_name = event['Event']
    
    # Time slots
    time_slots = [
        '09:00 AM', '09:10 AM', '09:20 AM', '09:30 AM', '09:40 AM', '09:50 AM',
        '10:00 AM', '10:10 AM', '10:20 AM', '10:30 AM', '10:40 AM', '10:50 AM',
        '11:00 AM', '11:10 AM', '11:20 AM', '11:30 AM', '11:40 AM', '11:50 AM',
        '12:00 PM', '12:10 PM', '12:20 PM', '12:30 PM', '12:40 PM', '12:50 PM',
        '01:00 PM', '01:10 PM', '01:20 PM', '01:30 PM', '01:40 PM', '01:50 PM',
        '02:00 PM', '02:10 PM', '02:20 PM', '02:30 PM', '02:40 PM', '02:50 PM',
        '03:00 PM', '03:10 PM', '03:20 PM', '03:30 PM', '03:40 PM', '03:50 PM',
        '04:00 PM', '04:10 PM', '04:20 PM', '04:30 PM', '04:40 PM', '04:50 PM',
        '05:00 PM', '05:10 PM', '05:20 PM', '05:30 PM', '05:40 PM', '05:50 PM',
        '06:00 PM'
    ]
    
    # Initialize variables
    schedule = []
    winners = {}
    
    # Foosball uses day schedule format
    if event_name == 'Foosball':
        schedule_file = Path(__file__).parent / 'foosball_day_schedule.json'
        if schedule_file.exists():
            with open(schedule_file) as f:
                schedule = json.load(f)
        
        # Load winners from database
        conn = get_db_connection()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute('SELECT match_id, winner FROM match_results WHERE event_name = %s', (event_name,))
                for row in cur.fetchall():
                    winners[row[0]] = row[1]
                cur.close()
                conn.close()
            except:
                pass
        
        # Fallback to JSON file if no database results
        if not winners:
            results_file = Path(__file__).parent / 'foosball_results.json'
            if results_file.exists():
                with open(results_file) as f:
                    winners = json.load(f)
        
        # Load saved time slots from database
        saved_time_slots = {}
        conn = get_db_connection()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute('SELECT match_id, time_slot FROM time_slots WHERE event_name = %s', (event_name,))
                for row in cur.fetchall():
                    saved_time_slots[row[0]] = row[1]
                cur.close()
                conn.close()
            except:
                pass
        
        # Fallback to JSON file if no database
        if not saved_time_slots:
            time_slots_file = Path(__file__).parent / f'{event_name.lower().replace(" ", "_")}_time_slots.json'
            if time_slots_file.exists():
                with open(time_slots_file) as f:
                    saved_time_slots = json.load(f)
        
        # Merge saved time slots into schedule
        for day in schedule:
            for match in day['matches']:
                if match['match_id'] in saved_time_slots:
                    match['time_slot'] = saved_time_slots[match['match_id']]
        
        return render_template('event_detail.html', event=event, event_idx=idx,
                             schedule=schedule, winners=winners, time_slots=time_slots)
    
    # Other sports use date-based structure
    schedule_files = {
        'Carrom': 'carrom_schedule.json',
        'Chess': 'chess_schedule.json',
        'Snookers': 'snookers_schedule.json',
        'TT': 'tt_schedule.json',
        'Seven Stones': 'sevenstones_schedule.json',
        'Tug of War': 'tugofwar_schedule.json'
    }
    
    if event_name in schedule_files:
        schedule_file = Path(__file__).parent / schedule_files[event_name]
        if schedule_file.exists():
            try:
                with open(schedule_file) as f:
                    data = json.load(f)
                
                # Handle different formats
                if event_name in ['Carrom', 'Foosball']:
                    # These already have day-based structure with matches array
                    schedule = data
                elif event_name in ['Seven Stones', 'Tug of War']:
                    # These have group_a and group_b structure
                    for day in data:
                        matches = []
                        if 'group_a' in day:
                            matches.extend(day['group_a'])
                        if 'group_b' in day:
                            matches.extend(day['group_b'])
                        
                        schedule.append({
                            'date': day['date'],
                            'matches': matches
                        })
                else:
                    # Group by date for other events (Chess, Snookers, TT)
                    from collections import defaultdict
                    by_date = defaultdict(list)
                    for match in data:
                        if isinstance(match, dict) and 'date' in match:
                            by_date[match['date']].append(match)
                    
                    for date in sorted(by_date.keys()):
                        schedule.append({
                            'date': date,
                            'matches': by_date[date]
                        })
            except Exception as e:
                print(f"Error loading schedule for {event_name}: {e}")
                schedule = []
        
        # Load results from database first
        conn = get_db_connection()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute('SELECT match_id, winner FROM match_results WHERE event_name = %s', (event_name,))
                for row in cur.fetchall():
                    winners[row[0]] = row[1]
                cur.close()
                conn.close()
            except:
                pass
        
        # Fallback to JSON file if no database results
        if not winners:
            results_file = Path(__file__).parent / f"{event_name.lower().replace(' ', '_')}_results.json"
            if results_file.exists():
                with open(results_file) as f:
                    winners = json.load(f)
    
    # Load saved time slots from database
    saved_time_slots = {}
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute('SELECT match_id, time_slot FROM time_slots WHERE event_name = %s', (event_name,))
            for row in cur.fetchall():
                saved_time_slots[row[0]] = row[1]
            cur.close()
            conn.close()
        except:
            pass
    
    # Fallback to JSON file if no database
    if not saved_time_slots:
        time_slots_file = Path(__file__).parent / f'{event_name.lower().replace(" ", "_")}_time_slots.json'
        if time_slots_file.exists():
            with open(time_slots_file) as f:
                saved_time_slots = json.load(f)
    
    # Merge saved time slots into schedule
    for day in schedule:
        for match in day['matches']:
            if match['match_id'] in saved_time_slots:
                match['time_slot'] = saved_time_slots[match['match_id']]
    
    # Time slots
    time_slots = [
        '09:00 AM', '09:10 AM', '09:20 AM', '09:30 AM', '09:40 AM', '09:50 AM',
        '10:00 AM', '10:10 AM', '10:20 AM', '10:30 AM', '10:40 AM', '10:50 AM',
        '11:00 AM', '11:10 AM', '11:20 AM', '11:30 AM', '11:40 AM', '11:50 AM',
        '12:00 PM', '12:10 PM', '12:20 PM', '12:30 PM', '12:40 PM', '12:50 PM',
        '01:00 PM', '01:10 PM', '01:20 PM', '01:30 PM', '01:40 PM', '01:50 PM',
        '02:00 PM', '02:10 PM', '02:20 PM', '02:30 PM', '02:40 PM', '02:50 PM',
        '03:00 PM', '03:10 PM', '03:20 PM', '03:30 PM', '03:40 PM', '03:50 PM',
        '04:00 PM', '04:10 PM', '04:20 PM', '04:30 PM', '04:40 PM', '04:50 PM',
        '05:00 PM', '05:10 PM', '05:20 PM', '05:30 PM', '05:40 PM', '05:50 PM',
        '06:00 PM'
    ]
    
    return render_template('event_detail.html', event=event, event_idx=idx,
                         schedule=schedule, winners=winners, time_slots=time_slots)

@app.route('/dashboard')
@admin_required
def dashboard():
    events = load_events()
    completed = sum(1 for e in events if e['Status'] == 'Completed')
    in_progress = sum(1 for e in events if e['Status'] == 'In Progress')
    planned = sum(1 for e in events if e['Status'] == 'Planned')
    return render_template('dashboard.html', events=events, completed=completed, 
                         in_progress=in_progress, planned=planned, total=len(events))

@app.route('/update/<int:idx>', methods=['GET', 'POST'])
@admin_required
def update(idx):
    events = load_events()
    if request.method == 'POST':
        events[idx].update({
            'Start_Date': request.form.get('start_date'),
            'End_Date': request.form.get('end_date'),
            'Finals_Date': request.form.get('finals_date'),
            'Status': request.form.get('status'),
            'Participants': request.form.get('participants'),
            'Winner': request.form.get('winner'),
            'Notes': request.form.get('notes')
        })
        save_events(events)
        return redirect('/dashboard')
    return render_template('update.html', event=events[idx], idx=idx)

def clear_participants(event_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM participants WHERE event_id = ?', (event_id,))
    conn.commit()
    conn.close()

def get_scorecard_file(idx):
    return PARTICIPANTS_DIR / f"scorecard_{idx}.json"

def load_scorecard(idx):
    file = get_scorecard_file(idx)
    if file.exists():
        with open(file) as f:
            return json.load(f)
    return {"judges": ["Judge 1", "Judge 2", "Judge 3"], "rounds": {}, "faceoff": {}}

def save_scorecard(idx, scorecard):
    file = get_scorecard_file(idx)
    with open(file, 'w') as f:
        json.dump(scorecard, f, indent=2)

@app.route('/scorecard/<int:idx>', methods=['GET', 'POST'])
def scorecard(idx):
    events = load_events()
    event = events[idx]
    participants = load_participants(idx)
    scorecard_data = load_scorecard(idx)
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'save_judges':
            scorecard_data['judges'] = [
                request.form.get('judge1', 'Judge 1'),
                request.form.get('judge2', 'Judge 2'),
                request.form.get('judge3', 'Judge 3')
            ]
            save_scorecard(idx, scorecard_data)
        
        elif action == 'save_scores':
            round_num = request.form.get('round')
            participant_serial = request.form.get('participant_serial')
            judge_idx = int(request.form.get('judge_idx'))
            
            if round_num not in scorecard_data['rounds']:
                scorecard_data['rounds'][round_num] = {}
            
            if participant_serial not in scorecard_data['rounds'][round_num]:
                scorecard_data['rounds'][round_num][participant_serial] = {}
            
            judge_scores = {
                'technical': int(request.form.get('technical', 0)),
                'musicality': int(request.form.get('musicality', 0)),
                'choreography': int(request.form.get('choreography', 0)),
                'performance': int(request.form.get('performance', 0)),
                'stage_presence': int(request.form.get('stage_presence', 0))
            }
            
            scorecard_data['rounds'][round_num][participant_serial][f'judge_{judge_idx}'] = judge_scores
            save_scorecard(idx, scorecard_data)
        
        return redirect(f'/scorecard/{idx}')
    
    # Calculate aggregates
    aggregates = {}
    for p in participants:
        serial = str(p['serial_number'])
        total = 0
        for round_num in ['1', '2', '3']:
            if round_num in scorecard_data['rounds'] and serial in scorecard_data['rounds'][round_num]:
                round_scores = scorecard_data['rounds'][round_num][serial]
                for judge_scores in round_scores.values():
                    total += sum(judge_scores.values())
        aggregates[serial] = total
    
    # Get top 2 for faceoff
    top_2 = sorted(aggregates.items(), key=lambda x: x[1], reverse=True)[:2]
    
    return render_template('scorecard.html', event=event, idx=idx, 
                         participants=participants, scorecard=scorecard_data,
                         aggregates=aggregates, top_2=top_2)

@app.route('/manage-participants/<int:idx>', methods=['GET', 'POST'])
@admin_required
def manage_participants(idx):
    events = load_events()
    event = events[idx]
    event_type = event.get('event_type', 'solo')
    
    if request.method == 'POST':
        action = request.form.get('action')
        participants = load_participants(idx)
        
        if action == 'add':
            serial = request.form.get('serial_number')
            participant1 = request.form.get('participant1', '').strip()
            participant2 = request.form.get('participant2', '').strip() if event_type == 'pair' else None
            team = request.form.get('team_name', '').strip()
            
            if participant1 and team:
                if not serial:
                    serial = len(participants) + 1
                participants.append({
                    'serial_number': int(serial),
                    'participant1_name': participant1,
                    'participant2_name': participant2,
                    'team_name': team
                })
                save_participants(idx, participants)
                
                # Auto-regenerate Foosball schedule
                if event['Event'] == 'Foosball':
                    import subprocess
                    try:
                        subprocess.run(['python', 'generate_foosball_knockout.py'], 
                                     cwd=Path(__file__).parent, check=True)
                    except:
                        pass
        
        elif action == 'edit':
            serial = int(request.form.get('serial_number'))
            participant1 = request.form.get('participant1', '').strip()
            participant2 = request.form.get('participant2', '').strip() if event_type == 'pair' else None
            team = request.form.get('team_name', '').strip()
            
            for p in participants:
                if p['serial_number'] == serial:
                    p['participant1_name'] = participant1
                    p['participant2_name'] = participant2
                    p['team_name'] = team
                    break
            save_participants(idx, participants)
            
            # Auto-regenerate Foosball schedule
            if event['Event'] == 'Foosball':
                import subprocess
                try:
                    subprocess.run(['python', 'generate_foosball_knockout.py'], 
                                 cwd=Path(__file__).parent, check=True)
                except:
                    pass
        
        elif action == 'delete':
            serial = int(request.form.get('serial_number'))
            participants = [p for p in participants if p['serial_number'] != serial]
            save_participants(idx, participants)
            
            # Auto-regenerate Foosball schedule
            if event['Event'] == 'Foosball':
                import subprocess
                try:
                    subprocess.run(['python', 'generate_foosball_knockout.py'], 
                                 cwd=Path(__file__).parent, check=True)
                except:
                    pass
        
        elif action == 'clear':
            save_participants(idx, [])
        
        return redirect(f'/manage-participants/{idx}')
    
    participants = load_participants(idx)
    return render_template('manage_participants.html', event=event, idx=idx, 
                         participants=participants, event_type=event_type)

@app.route('/schedule/<int:idx>')
def schedule(idx):
    try:
        from itertools import combinations
        from datetime import datetime, timedelta
        
        events = load_events()
        event = events[idx]
        event_name = event['Event']
        
        # Handle Tug of War separately
        if event_name in ['Tug of War', 'Seven Stones']:
            participants = load_participants(idx)
            
            if not participants:
                return "No participants found. Please add participants first.", 404
            
            # Split into groups based on serial numbers
            group_a = [p for p in participants if p['serial_number'] <= 8]
            group_b = [p for p in participants if p['serial_number'] > 8]
            
            def generate_round_robin(teams, group_name):
                matches = []
                match_num = 1
                for i, j in combinations(range(len(teams)), 2):
                    team1 = teams[i]
                    team2 = teams[j]
                    matches.append({
                        'match_id': f"{group_name}_M{match_num}",
                        'match_number': match_num,
                        'group': group_name,
                        'team1_serial': team1['serial_number'],
                        'team1_name': team1['team_name'],
                        'team1_members': team1['participant1_name'],
                        'team2_serial': team2['serial_number'],
                        'team2_name': team2['team_name'],
                        'team2_members': team2['participant1_name']
                    })
                    match_num += 1
                return matches
            
            def distribute_matches_fairly(matches, matches_per_day):
                """Distribute matches so no team plays back-to-back on same day"""
                days = []
                remaining = matches.copy()
                
                while remaining:
                    day_matches = []
                    used_teams = set()
                    
                    # Try to fill the day without back-to-back matches
                    for match in remaining[:]:
                        team1 = match['team1_serial']
                        team2 = match['team2_serial']
                        
                        # Check if either team already played today
                        if team1 not in used_teams and team2 not in used_teams:
                            day_matches.append(match)
                            used_teams.add(team1)
                            used_teams.add(team2)
                            remaining.remove(match)
                            
                            if len(day_matches) >= matches_per_day:
                                break
                    
                    # If we couldn't fill the day, just add remaining matches
                    if not day_matches and remaining:
                        day_matches = remaining[:matches_per_day]
                        remaining = remaining[matches_per_day:]
                    
                    if day_matches:
                        days.append(day_matches)
                
                return days
            
            group_a_matches = generate_round_robin(group_a, "Group A")
            group_b_matches = generate_round_robin(group_b, "Group B")
            
            # Distribute matches fairly
            matches_per_day = 3  # 3 per group
            group_a_days = distribute_matches_fairly(group_a_matches, matches_per_day)
            group_b_days = distribute_matches_fairly(group_b_matches, matches_per_day)
            
            # Create day schedule
            start_date = datetime(2025, 11, 28)
            current_date = start_date
            day_schedule = []
            
            max_days = max(len(group_a_days), len(group_b_days))
            
            for day_idx in range(max_days):
                # Skip weekends
                while current_date.weekday() >= 5:
                    current_date += timedelta(days=1)
                
                group_a_day = group_a_days[day_idx] if day_idx < len(group_a_days) else []
                group_b_day = group_b_days[day_idx] if day_idx < len(group_b_days) else []
                
                # Add date to each match
                for match in group_a_day + group_b_day:
                    match['date'] = current_date.strftime('%Y-%m-%d')
                    match['day_name'] = current_date.strftime('%A, %B %d')
                
                day_schedule.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'day_name': current_date.strftime('%A, %B %d'),
                    'group_a': group_a_day,
                    'group_b': group_b_day
                })
                
                current_date += timedelta(days=1)
            
            total_matches = len(group_a_matches) + len(group_b_matches)
            
            # Load saved winners
            results_file = Path(__file__).parent / f"{event_name.lower().replace(' ', '')}_results.json"
            winners = {}
            if results_file.exists():
                with open(results_file, 'r') as f:
                    winners = json.load(f)
            
            template_name = 'tugofwar_schedule.html' if event_name == 'Tug of War' else 'sevenstones_schedule.html'
            return render_template(template_name, event_name=event_name,
                                 schedule=day_schedule, total_days=len(day_schedule),
                                 total_matches=total_matches, winners=winners)
        
        # Handle Carrom
        if event_name == 'Carrom':
            schedule_file = Path(__file__).parent / 'carrom_schedule.json'
            if not schedule_file.exists():
                return "Carrom schedule not found.", 404
            
            with open(schedule_file) as f:
                matches = json.load(f)
            
            # Group by date
            from collections import defaultdict
            by_date = defaultdict(list)
            for match in matches:
                by_date[match['date']].append(match)
            
            day_schedule = []
            for date in sorted(by_date.keys()):
                day_schedule.append({
                    'date': date,
                    'matches': by_date[date]
                })
            
            # Load results
            results_file = Path(__file__).parent / 'carrom_results.json'
            winners = {}
            if results_file.exists():
                with open(results_file) as f:
                    winners = json.load(f)
            
            return render_template('carrom_schedule.html', event_name=event_name,
                                 schedule=day_schedule, total_days=len(day_schedule),
                                 total_matches=len(matches), winners=winners)
        
        # Handle Chess
        if event_name == 'Chess':
            schedule_file = Path(__file__).parent / 'chess_schedule.json'
            if not schedule_file.exists():
                return "Chess schedule not found.", 404
            
            with open(schedule_file) as f:
                matches = json.load(f)
            
            # Group by date
            from collections import defaultdict
            by_date = defaultdict(list)
            for match in matches:
                by_date[match['date']].append(match)
            
            day_schedule = []
            for date in sorted(by_date.keys()):
                day_schedule.append({
                    'date': date,
                    'matches': by_date[date]
                })
            
            # Load results
            results_file = Path(__file__).parent / 'chess_results.json'
            winners = {}
            if results_file.exists():
                with open(results_file) as f:
                    winners = json.load(f)
            
            return render_template('chess_schedule.html', event_name=event_name,
                                 schedule=day_schedule, total_days=len(day_schedule),
                                 total_matches=len(matches), winners=winners)
        
        # Handle Foosball (existing code)
        participants = load_participants(idx)
        # Handle Foosball (existing code)
        participants = load_participants(idx)
        
        if not participants:
            return "No participants found. Please add participants first.", 404
        
        # Group by team
        teams = {}
        for pair in participants:
            team = pair.get('team_name', 'Unknown')
            if team not in teams:
                teams[team] = []
            teams[team].append(pair)
        
        # Separate large and small teams
        large_teams = {k: v for k, v in teams.items() if len(v) >= 4}
        small_teams = {k: v for k, v in teams.items() if len(v) < 4}
        
        # Generate matches
        all_matches = []
        match_counter = 1
        
        # Large teams
        for team, pairs in large_teams.items():
            matches = list(combinations(range(len(pairs)), 2))
            for i, j in matches:
                pair1 = pairs[i]
                pair2 = pairs[j]
                all_matches.append({
                    'match_id': f"{team}_M{match_counter}",
                    'match_number': match_counter,
                    'group': team,
                    'pair1_num': pair1.get('serial_number', 0),
                    'pair1_p1': pair1.get('participant1_name', ''),
                    'pair1_p2': pair1.get('participant2_name', ''),
                    'pair1_team': pair1.get('team_name', ''),
                    'pair2_num': pair2.get('serial_number', 0),
                    'pair2_p1': pair2.get('participant1_name', ''),
                    'pair2_p2': pair2.get('participant2_name', ''),
                    'pair2_team': pair2.get('team_name', '')
                })
                match_counter += 1
        
        # Combined small teams
        combined_group = []
        for team, pairs in small_teams.items():
            combined_group.extend(pairs)
        
        if combined_group:
            matches = list(combinations(range(len(combined_group)), 2))
            for i, j in matches:
                pair1 = combined_group[i]
                pair2 = combined_group[j]
                all_matches.append({
                    'match_id': f"COMBINED_M{match_counter}",
                    'match_number': match_counter,
                    'group': 'COMBINED_SMALL_TEAMS',
                    'pair1_num': pair1.get('serial_number', 0),
                    'pair1_p1': pair1.get('participant1_name', ''),
                    'pair1_p2': pair1.get('participant2_name', ''),
                    'pair1_team': pair1.get('team_name', ''),
                    'pair2_num': pair2.get('serial_number', 0),
                    'pair2_p1': pair2.get('participant1_name', ''),
                    'pair2_p2': pair2.get('participant2_name', ''),
                    'pair2_team': pair2.get('team_name', '')
                })
                match_counter += 1
        
        # Distribute across weekdays only (30 matches per day, 15 per table)
        start_date = datetime(2025, 12, 2)  # December 2nd
        matches_per_day = 30
        day_schedule = []
        
        current_date = start_date
        for day_num in range(0, len(all_matches), matches_per_day):
            # Skip weekends
            while current_date.weekday() >= 5:  # 5=Saturday, 6=Sunday
                current_date += timedelta(days=1)
            
            day_matches = all_matches[day_num:day_num + matches_per_day]
            
            # Split into two tables (15 each)
            table1_matches = day_matches[:15]
            table2_matches = day_matches[15:]
            
            # Add table assignment
            for match in table1_matches:
                match['table'] = 'Table 1'
                match['date'] = current_date.strftime('%Y-%m-%d')
                match['day_name'] = current_date.strftime('%A, %B %d')
            
            for match in table2_matches:
                match['table'] = 'Table 2'
                match['date'] = current_date.strftime('%Y-%m-%d')
                match['day_name'] = current_date.strftime('%A, %B %d')
            
            day_schedule.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'day_name': current_date.strftime('%A, %B %d'),
                'table1': table1_matches,
                'table2': table2_matches
            })
            
            current_date += timedelta(days=1)
        
        # Get unique teams for filter
        unique_teams = sorted(set(m['pair1_team'] for m in all_matches) | set(m['pair2_team'] for m in all_matches))
        
        total_matches = len(all_matches)
        
        # Load saved winners
        results_file = Path(__file__).parent / 'foosball_results.json'
        winners = {}
        if results_file.exists():
            with open(results_file, 'r') as f:
                winners = json.load(f)
        
        return render_template('schedule.html', event_name=event['Event'], 
                             schedule=day_schedule, total_days=len(day_schedule),
                             total_matches=total_matches, teams=unique_teams, winners=winners)
    except Exception as e:
        return f"Error generating schedule: {str(e)}", 500

@app.route('/update-match-winner', methods=['POST'])
def update_match_winner():
    try:
        data = request.json
        match_id = data['match_id']
        winner = data['winner']
        event_name = data.get('event', 'Foosball')
        
        # Save to database
        conn = get_db_connection()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute('''
                    INSERT INTO match_results (event_name, match_id, winner)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (event_name, match_id) DO UPDATE SET winner = EXCLUDED.winner
                ''', (event_name, match_id, winner))
                conn.commit()
                cur.close()
                conn.close()
            except Exception as e:
                print(f"Database error: {e}")
        
        # Also save to dedicated JSON file
        results_file = Path(__file__).parent / f'{event_name.lower().replace(" ", "_")}_results.json'
        
        try:
            with open(results_file, 'r') as f:
                results = json.load(f)
        except:
            results = {}
        
        results[match_id] = winner
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Auto-commit in production
        if os.environ.get('RENDER'):
            import subprocess
            try:
                subprocess.run(['git', 'add', str(results_file)], cwd=Path(__file__).parent, timeout=5)
                subprocess.run(['git', 'commit', '-m', f'Update winner for {event_name}'], 
                             cwd=Path(__file__).parent, timeout=5)
                subprocess.run(['git', 'push'], cwd=Path(__file__).parent, timeout=30)
            except:
                pass
        
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/update-time-slot', methods=['POST'])
def update_time_slot():
    try:
        data = request.json
        event = data['event']
        match_id = data['match_id']
        time_slot = data['time_slot']
        
        # Save to database
        conn = get_db_connection()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute('''
                    INSERT INTO time_slots (event_name, match_id, time_slot)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (event_name, match_id) DO UPDATE SET time_slot = EXCLUDED.time_slot
                ''', (event, match_id, time_slot))
                conn.commit()
                cur.close()
                conn.close()
            except Exception as e:
                print(f"Database error: {e}")
        
        # Also save to dedicated JSON file
        time_slots_file = Path(__file__).parent / f'{event.lower().replace(" ", "_")}_time_slots.json'
        time_slots_data = {}
        if time_slots_file.exists():
            with open(time_slots_file) as f:
                time_slots_data = json.load(f)
        
        time_slots_data[match_id] = time_slot
        
        with open(time_slots_file, 'w') as f:
            json.dump(time_slots_data, f, indent=2)
        
        # Auto-commit in production
        if os.environ.get('RENDER'):
            import subprocess
            try:
                subprocess.run(['git', 'add', str(time_slots_file)], cwd=Path(__file__).parent, timeout=5)
                subprocess.run(['git', 'commit', '-m', f'Update time slot for {event}'], 
                             cwd=Path(__file__).parent, timeout=5)
                subprocess.run(['git', 'push'], cwd=Path(__file__).parent, timeout=30)
            except:
                pass
        
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/carrom/submit-score', methods=['POST', 'OPTIONS'])
def submit_carrom_score():
    """
    API endpoint to submit Carrom match winner
    
    Expected JSON format:
    {
        "match_id": "SDL_M1",
        "winner": 1
    }
    
    Where winner is:
    - 1 for Team 1 wins
    - 2 for Team 2 wins
    - 0 for Draw
    """
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response
    
    try:
        data = request.json
        print(f"[CARROM API] Received POST request: {data}")
        print(f"[CARROM API] Headers: {dict(request.headers)}")
        
        # Validate required fields
        if 'match_id' not in data or 'winner' not in data:
            response = jsonify({'status': 'error', 'message': 'Missing match_id or winner'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        match_id = data['match_id']
        winner = data['winner']
        
        # Validate winner value
        if winner not in [0, 1, 2]:
            response = jsonify({'status': 'error', 'message': 'Winner must be 0 (draw), 1 (team 1), or 2 (team 2)'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        # Save to carrom results (same format as foosball)
        results_file = Path(__file__).parent / 'carrom_results.json'
        try:
            with open(results_file, 'r') as f:
                results = json.load(f)
        except:
            results = {}
        
        results[match_id] = winner
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        result_text = 'Draw' if winner == 0 else f'Team {winner} wins'
        print(f"[CARROM API] Successfully saved: {match_id} -> {result_text}")
        
        response = jsonify({
            'status': 'success',
            'message': f'Result submitted: {result_text}',
            'match_id': match_id,
            'winner': winner
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        print(f"[CARROM API] Error: {str(e)}")
        response = jsonify({'status': 'error', 'message': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@app.route('/api/carrom/scores', methods=['GET'])
def get_carrom_scores():
    """Get all Carrom match winners"""
    try:
        results_file = Path(__file__).parent / 'carrom_results.json'
        if results_file.exists():
            with open(results_file, 'r') as f:
                results = json.load(f)
            return jsonify({'status': 'success', 'results': results})
        else:
            return jsonify({'status': 'success', 'results': {}})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/carrom/test', methods=['GET'])
def test_carrom_data():
    """Test endpoint to view all carrom match data"""
    try:
        # Load schedule
        schedule_file = Path(__file__).parent / 'carrom_schedule.json'
        results_file = Path(__file__).parent / 'carrom_results.json'
        
        schedule = []
        results = {}
        
        if schedule_file.exists():
            with open(schedule_file, 'r') as f:
                schedule = json.load(f)
        
        if results_file.exists():
            with open(results_file, 'r') as f:
                results = json.load(f)
        
        response = jsonify({
            'status': 'success',
            'total_matches': len(schedule),
            'completed_matches': len(results),
            'schedule': schedule[:10],  # First 10 matches
            'results': results
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        response = jsonify({'status': 'error', 'message': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@app.route('/font-preview')
def font_preview():
    return render_template('font_preview.html')

@app.route('/send-schedule-email', methods=['POST'])
@admin_required
def send_schedule_email():
    try:
        data = request.json
        event_name = data.get('event')
        date = data.get('date')
        sender_email = data.get('sender_email')
        recipient_email = data.get('recipient_email')
        
        if not all([event_name, date, sender_email, recipient_email]):
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
        
        # Load schedule for the event
        schedule_files = {
            'Carrom': 'carrom_schedule.json',
            'Chess': 'chess_schedule.json',
            'Foosball': 'foosball_day_schedule.json',
            'Snookers': 'snookers_schedule.json',
            'TT': 'tt_schedule.json',
            'Seven Stones': 'sevenstones_schedule.json',
            'Tug of War': 'tugofwar_schedule.json'
        }
        
        matches = []
        if event_name in schedule_files:
            schedule_file = Path(__file__).parent / schedule_files[event_name]
            if schedule_file.exists():
                with open(schedule_file) as f:
                    schedule_data = json.load(f)
                
                # Find matches for the specified date
                if event_name == 'Foosball':
                    for day in schedule_data:
                        if day['date'] == date:
                            matches = day['matches']
                            break
                elif event_name in ['Seven Stones', 'Tug of War']:
                    for day in schedule_data:
                        if day['date'] == date:
                            if 'group_a' in day:
                                matches.extend(day['group_a'])
                            if 'group_b' in day:
                                matches.extend(day['group_b'])
                            break
                else:
                    for match in schedule_data:
                        if match.get('date') == date:
                            matches.append(match)
        
        if not matches:
            return jsonify({'status': 'error', 'message': f'No matches found for {date}'}), 404
        
        # Create email content
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #00ffff;">{event_name} - Schedule for {date}</h2>
            <p>Total matches: {len(matches)}</p>
            <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                <thead>
                    <tr style="background: #1a0033; color: white;">
                        <th style="padding: 10px; border: 1px solid #ddd;">Match ID</th>
                        <th style="padding: 10px; border: 1px solid #ddd;">Team 1</th>
                        <th style="padding: 10px; border: 1px solid #ddd;">Team 2</th>
                        <th style="padding: 10px; border: 1px solid #ddd;">Time</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for match in matches:
            team1 = ''
            team2 = ''
            
            if 'team1_name' in match:
                team1 = f"{match['team1_name']}<br><small>{match.get('team1_members', '')}</small>"
                team2 = f"{match['team2_name']}<br><small>{match.get('team2_members', '')}</small>"
            elif 'pair1_team' in match:
                team1 = f"{match['pair1_team']}<br><small>{match['pair1_p1']} & {match['pair1_p2']}</small>"
                team2 = f"{match['pair2_team']}<br><small>{match['pair2_p1']} & {match['pair2_p2']}</small>"
            elif 'player1' in match:
                team1 = match['player1']
                team2 = match['player2']
            
            time_slot = match.get('time_slot', 'TBD')
            
            html_content += f"""
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;">{match['match_id']}</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{team1}</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{team2}</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{time_slot}</td>
                    </tr>
            """
        
        html_content += """
                </tbody>
            </table>
            <p style="margin-top: 20px; color: #666;">
                This is an automated email from FELIZZO'25 Dashboard.
            </p>
        </body>
        </html>
        """
        
        # Send email using AWS SES
        aws_region = os.getenv('AWS_REGION', 'us-east-1')
        
        # Create SES client
        ses_client = boto3.client('ses', region_name=aws_region)
        
        try:
            response = ses_client.send_email(
                Source=sender_email,
                Destination={
                    'ToAddresses': [recipient_email]
                },
                Message={
                    'Subject': {
                        'Data': f"{event_name} Schedule - {date}",
                        'Charset': 'UTF-8'
                    },
                    'Body': {
                        'Html': {
                            'Data': html_content,
                            'Charset': 'UTF-8'
                        }
                    }
                }
            )
            
            return jsonify({'status': 'success', 'message': f'Schedule sent to {recipient_email}'})
        
        except ClientError as e:
            error_msg = e.response['Error']['Message']
            return jsonify({'status': 'error', 'message': f'SES Error: {error_msg}'}), 500
    
    except Exception as e:
        print(f"Error sending email: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/clear-foosball-timeslots')
@admin_required
def clear_foosball_timeslots():
    try:
        # Clear from database
        conn = get_db_connection()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("DELETE FROM time_slots WHERE event_name = 'Foosball'")
                conn.commit()
                cur.close()
                conn.close()
            except Exception as e:
                print(f"Database error: {e}")
        
        # Clear JSON file
        time_slots_file = Path(__file__).parent / 'foosball_time_slots.json'
        if time_slots_file.exists():
            time_slots_file.unlink()
        
        return "Foosball time slots cleared successfully", 200
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
