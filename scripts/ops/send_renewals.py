#!/usr/bin/env python3
import sys
import os
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database.models import get_session, Client, Policy, Payment, PaymentStatus
import pandas as pd


def export_to_renewal_csv():
    session = get_session()
    
    today = datetime.now().date()
    
    pending_payments = session.query(Payment).filter(
        Payment.status == PaymentStatus.PENDING
    ).all()
    
    renewal_data = []
    
    for payment in pending_payments:
        policy = payment.policy
        client = policy.client
        
        days_until = (payment.due_date - today).days
        
        if 0 <= days_until <= 20:
            renewal_data.append({
                'client_name': client.name,
                'email': client.email or f'{client.name.replace(" ", "")}@example.com',
                'service_name': f'{policy.policy_type} - {policy.provider}',
                'expiration_date': payment.due_date.strftime('%Y-%m-%d'),
                'premium': policy.premium or '',
                'license_plate': policy.license_plate or '',
                'language': 'el'
            })
    
    if not renewal_data:
        print("No renewals due in the next 20 days")
        return False
    
    df = pd.DataFrame(renewal_data)
    
    renewal_system_path = '/Users/christosiatropoulos/Documents/chris /renewal invitations /renewal_system/renewal_system 2/renewal_system_v2/clients.csv'
    df.to_csv(renewal_system_path, index=False, encoding='utf-8-sig')
    
    print(f"✓ Exported {len(df)} renewals to renewal system")
    print("\nRenewal summary:")
    print(f"  Total clients: {len(df)}")
    print(f"  With email: {len(df[~df['email'].str.contains('@example.com')])}")
    print(f"  Without email: {len(df[df['email'].str.contains('@example.com')])}")
    
    session.close()
    return True


def send_renewals(dry_run=False):
    print("=" * 60)
    print("INTEGRATED RENEWAL WORKFLOW")
    print("=" * 60)
    
    print("\nStep 1: Exporting from database...")
    if not export_to_renewal_csv():
        return
    
    print("\nStep 2: Sending renewal emails...")
    renewal_system_dir = '/Users/christosiatropoulos/Documents/chris /renewal invitations /renewal_system/renewal_system 2/renewal_system_v2'
    
    if not os.path.exists(renewal_system_dir):
        print(f"Error: Renewal system not found at {renewal_system_dir}")
        return
    
    original_dir = os.getcwd()
    os.chdir(renewal_system_dir)
    
    cmd = 'python renewal_invitations_bilingual.py'
    if dry_run:
        cmd += ' --dry-run'
    
    print(f"Running: {cmd}\n")
    result = os.system(cmd)
    
    os.chdir(original_dir)
    
    if result == 0:
        print("\n✓ Renewal workflow complete!")
    else:
        print("\n✗ Error in renewal workflow")
    
    print("=" * 60)


if __name__ == "__main__":
    dry_run = '--dry-run' in sys.argv
    send_renewals(dry_run=dry_run)
