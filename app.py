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

@app.route('/schedule/<int:idx>')
def schedule(idx):
    events = load_events()
    event = events[idx]
    
    schedule_file = Path(__file__).parent / 'foosball_day_schedule.json'
    
    if not schedule_file.exists():
        return "Schedule not found. Please generate the schedule first.", 404
    
    with open(schedule_file, 'r') as f:
        schedule_data = json.load(f)
    
    total_matches = sum(len(d['matches']) for d in schedule_data)
    
    return render_template('schedule.html', event_name=event['Event'], 
                         schedule=schedule_data, total_days=len(schedule_data),
                         total_matches=total_matches)

@app.route('/update-match-winner', methods=['POST'])
def update_match_winner():
    try:
        data = request.json
        match_id = data['match_id']
        winner = data['winner']
        
        results_file = Path(__file__).parent / 'foosball_results.json'
        
        # Load existing results or create new
        try:
            with open(results_file, 'r') as f:
                results = json.load(f)
        except:
            results = {}
        
        results[match_id] = winner
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
