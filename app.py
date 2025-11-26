#!/usr/bin/env python3
from flask import Flask, render_template, request, redirect, jsonify
import csv
import json
from pathlib import Path

app = Flask(__name__)
CSV_FILE = Path(__file__).parent / "event_tracker.csv"
PARTICIPANTS_DIR = Path(__file__).parent / "participants_data"
PARTICIPANTS_DIR.mkdir(exist_ok=True)

# Event type mapping
EVENT_TYPES = {
    'Carrom': 'pair', 'TT': 'pair', 'Snookers': 'pair', 'Foosball': 'pair', 'CWF': 'pair',
    'Solo Singing': 'solo', 'Solo Dance': 'solo', 'Chess': 'solo', 'Trash to Treasure': 'solo',
    'Painting': 'solo', 'Meme Creation': 'solo', 'Photography': 'solo', 'Reels': 'solo',
    'Group Singing': 'group', 'Group Dance': 'group', 'Tug of War': 'group', 
    'Seven Stones': 'group', 'Treasure Hunt': 'group'
}

def load_events():
    with open(CSV_FILE) as f:
        events = list(csv.DictReader(f))
        for event in events:
            event['event_type'] = EVENT_TYPES.get(event['Event'], 'solo')
        return events

def save_events(events):
    with open(CSV_FILE, 'w', newline='') as f:
        fieldnames = [k for k in events[0].keys() if k != 'event_type']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for event in events:
            row = {k: v for k, v in event.items() if k != 'event_type'}
            writer.writerow(row)

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

@app.route('/')
def dashboard():
    events = load_events()
    completed = sum(1 for e in events if e['Status'] == 'Completed')
    in_progress = sum(1 for e in events if e['Status'] == 'In Progress')
    planned = sum(1 for e in events if e['Status'] == 'Planned')
    return render_template('dashboard.html', events=events, completed=completed, 
                         in_progress=in_progress, planned=planned, total=len(events))

@app.route('/update/<int:idx>', methods=['GET', 'POST'])
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
        return redirect('/')
    return render_template('update.html', event=events[idx], idx=idx)

@app.route('/manage-participants/<int:idx>', methods=['GET', 'POST'])
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
        
        elif action == 'delete':
            serial = int(request.form.get('serial_number'))
            participants = [p for p in participants if p['serial_number'] != serial]
            save_participants(idx, participants)
        
        elif action == 'clear':
            save_participants(idx, [])
        
        return redirect(f'/manage-participants/{idx}')
    
    participants = load_participants(idx)
    return render_template('manage_participants.html', event=event, idx=idx, 
                         participants=participants, event_type=event_type)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
