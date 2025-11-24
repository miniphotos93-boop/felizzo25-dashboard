#!/usr/bin/env python3
import csv
from datetime import datetime
from pathlib import Path

CSV_FILE = Path(__file__).parent / "event_tracker.csv"

def load_events():
    with open(CSV_FILE) as f:
        return list(csv.DictReader(f))

def save_events(events):
    with open(CSV_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=events[0].keys())
        writer.writeheader()
        writer.writerows(events)

def show_status():
    events = load_events()
    print("\n=== Felizzo'25 Event Status ===\n")
    for i, e in enumerate(events, 1):
        print(f"{i}. {e['Event']}")
        print(f"   Status: {e['Status']}")
        print(f"   Owners: {e['Owners']}")
        if e['Start_Date']:
            print(f"   Start: {e['Start_Date']}")
        if e['Winner']:
            print(f"   Winner: {e['Winner']}")
        print()

def update_event():
    events = load_events()
    show_status()
    idx = int(input("Select event number: ")) - 1
    event = events[idx]
    
    print(f"\nUpdating: {event['Event']}")
    print("1. Update dates")
    print("2. Update status")
    print("3. Add participants")
    print("4. Add winner")
    choice = input("Choice: ")
    
    if choice == "1":
        event['Start_Date'] = input("Start date (YYYY-MM-DD): ") or event['Start_Date']
        event['End_Date'] = input("End date (YYYY-MM-DD): ") or event['End_Date']
        event['Finals_Date'] = input("Finals date (YYYY-MM-DD): ") or event['Finals_Date']
    elif choice == "2":
        event['Status'] = input("Status (Planned/In Progress/Completed): ")
    elif choice == "3":
        event['Participants'] = input("Number of participants: ")
    elif choice == "4":
        event['Winner'] = input("Winner name: ")
    
    save_events(events)
    print("✓ Updated!")

def generate_announcement():
    events = load_events()
    show_status()
    idx = int(input("Select event number: ")) - 1
    event = events[idx]
    
    print(f"\n=== Announcement Template ===\n")
    print(f"Subject: {event['Event']} - Felizzo'25\n")
    print(f"Hi Team,\n")
    print(f"We're excited to announce the {event['Event']} event as part of Felizzo'25!\n")
    print(f"📅 Date: {event['Start_Date'] or '[TBD]'}")
    print(f"👥 Event Owners: {event['Owners']}\n")
    print(f"Registration details and rules will be shared soon.")
    print(f"Stay tuned!\n")
    print(f"Felizzo'25 Organizing Team")

def show_dashboard():
    events = load_events()
    completed = sum(1 for e in events if e['Status'] == 'Completed')
    in_progress = sum(1 for e in events if e['Status'] == 'In Progress')
    planned = sum(1 for e in events if e['Status'] == 'Planned')
    
    print("\n=== Felizzo'25 Dashboard ===\n")
    print(f"Total Events: {len(events)}")
    print(f"✓ Completed: {completed}")
    print(f"⚡ In Progress: {in_progress}")
    print(f"📋 Planned: {planned}")
    print(f"\nProgress: {completed}/{len(events)} ({completed*100//len(events)}%)")

def main():
    while True:
        print("\n=== Felizzo'25 Event Manager ===")
        print("1. Show status")
        print("2. Update event")
        print("3. Generate announcement")
        print("4. Show dashboard")
        print("5. Exit")
        
        choice = input("\nChoice: ")
        
        if choice == "1":
            show_status()
        elif choice == "2":
            update_event()
        elif choice == "3":
            generate_announcement()
        elif choice == "4":
            show_dashboard()
        elif choice == "5":
            break

if __name__ == "__main__":
    main()
