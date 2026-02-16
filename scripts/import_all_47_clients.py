#!/usr/bin/env python3
"""
ONE-TIME IMPORT: Import all 47 clients from old renewal system
"""
import pandas as pd
from datetime import datetime
from src.database.models import get_session, Client, Policy, Payment, PaymentStatus, PolicyStatus

print("=" * 60)
print("IMPORTING 47 CLIENTS FROM OLD SYSTEM")
print("=" * 60)

old_csv = '/Users/christosiatropoulos/Documents/chris /renewal invitations /renewal_system/renewal_system 2/renewal_system_v2/clients_backup.csv'

session = get_session()

try:
    df = pd.read_csv(old_csv, encoding='utf-8')
    print(f"\nFound {len(df)} clients in old system\n")
except:
    print("Error: Could not find clients_backup.csv")
    print("Trying clients.csv instead...")
    old_csv = '/Users/christosiatropoulos/Documents/chris /renewal invitations /renewal_system/renewal_system 2/renewal_system_v2/clients.csv'
    df = pd.read_csv(old_csv, encoding='utf-8')
    print(f"\nFound {len(df)} clients\n")

imported = 0
updated = 0
skipped = 0

for idx, row in df.iterrows():
    client_name = row['client_name']
    email = row.get('email', '')
    
    if '@example.com' in str(email):
        email = None
    
    existing_client = session.query(Client).filter_by(name=client_name).first()
    
    if existing_client:
        expiration = pd.to_datetime(row['expiration_date']).date()
        
        existing_policy = None
        for policy in existing_client.policies:
            if policy.expiration_date == expiration:
                existing_policy = policy
                break
        
        if existing_policy:
            print(f"  ↻ {client_name} - policy already exists")
            skipped += 1
            continue
        else:
            client = existing_client
            print(f"  + Adding new policy to: {client_name}")
    else:
        client = Client(
            name=client_name,
            email=email
        )
        session.add(client)
        session.flush()
        print(f"  + New client: {client_name}")
        imported += 1
    
    expiration = pd.to_datetime(row['expiration_date']).date()
    
    # Fix Greek number format (1.019.86 -> 1019.86)
    premium = None
    if pd.notna(row.get('premium')) and str(row.get('premium')) != 'nan':
        try:
            premium_str = str(row['premium']).replace('.', '').replace(',', '.')
            premium = float(premium_str)
        except:
            premium = None
    
    license_plate = row.get('license_plate') if pd.notna(row.get('license_plate')) and str(row.get('license_plate')) != 'nan' else None
    
    service_parts = row['service_name'].split(' - ')
    if len(service_parts) >= 2:
        policy_type = service_parts[0]
        provider = ' - '.join(service_parts[1:])
    else:
        policy_type = row['service_name']
        provider = 'UNKNOWN'
    
    policy = Policy(
        client_id=client.id,
        provider=provider,
        policy_type=policy_type,
        license_plate=license_plate,
        premium=premium,
        expiration_date=expiration,
        status=PolicyStatus.ACTIVE
    )
    session.add(policy)
    session.flush()
    
    payment = Payment(
        policy_id=policy.id,
        amount=premium if premium else 0,
        due_date=expiration,
        status=PaymentStatus.PENDING
    )
    session.add(payment)
    updated += 1

session.commit()

print("\n" + "=" * 60)
print("✓ IMPORT COMPLETE!")
print("=" * 60)
print(f"  New clients: {imported}")
print(f"  New policies: {updated}")
print(f"  Skipped (duplicates): {skipped}")
print(f"  Total in database: {session.query(Client).count()} clients")
print(f"  Total policies: {session.query(Policy).count()} policies")
print("=" * 60)

session.close()
