#!/usr/bin/env python3
"""
Script to send schedule emails from ftv-qs-felizzo@amazon.com
Uses a verified sender but sets From header to the mailing list
"""

import boto3
import json
from datetime import datetime
from pathlib import Path

def send_schedule_email(event_name, date, recipient_email, verified_sender='sharikan@amazon.com'):
    """
    Send schedule email using verified sender but displaying as ftv-qs-felizzo@amazon.com
    """
    
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
            elif event_name == 'Carrom':
                for day in schedule_data:
                    if day['date'] == date:
                        if 'table1' in day:
                            matches.extend(day['table1'])
                        if 'table2' in day:
                            matches.extend(day['table2'])
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
        print(f"No matches found for {event_name} on {date}")
        return False
    
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
    
    # Send email using SES
    ses_client = boto3.client('ses', region_name='us-east-1')
    
    try:
        response = ses_client.send_email(
            Source=f'FELIZZO 25 <{verified_sender}>',  # Use verified sender
            ReplyToAddresses=['ftv-qs-felizzo@amazon.com'],  # Replies go to mailing list
            Destination={
                'ToAddresses': [recipient_email]
            },
            Message={
                'Subject': {
                    'Data': f"FELIZZO'25: {event_name} Schedule - {date}",
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
        
        print(f"✓ Email sent successfully to {recipient_email}")
        print(f"  Message ID: {response['MessageId']}")
        return True
        
    except Exception as e:
        print(f"✗ Error sending email: {e}")
        return False


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 4:
        print("Usage: python send_email_direct.py <event_name> <date> <recipient_email>")
        print("Example: python send_email_direct.py Carrom 2025-11-24 user@amazon.com")
        sys.exit(1)
    
    event_name = sys.argv[1]
    date = sys.argv[2]
    recipient_email = sys.argv[3]
    
    send_schedule_email(event_name, date, recipient_email)
