#!/usr/bin/env python3
from flask import Flask, render_template, request, redirect, jsonify
import csv
from pathlib import Path

app = Flask(__name__)
CSV_FILE = Path(__file__).parent / "event_tracker.csv"

def load_events():
    with open(CSV_FILE) as f:
        return list(csv.DictReader(f))

def save_events(events):
    with open(CSV_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=events[0].keys())
        writer.writeheader()
        writer.writerows(events)

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
