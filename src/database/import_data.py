#!/usr/bin/env python3
import pandas as pd
from datetime import datetime
import os
import sys

os.chdir('/Users/christosiatropoulos/Documents/CHI_Insurance_Portal')
sys.path.insert(0, '/Users/christosiatropoulos/Documents/CHI_Insurance_Portal')

from src.database.models import init_db, get_session, Client, Policy, Payment, PaymentStatus, PolicyStatus


def import_from_csv(csv_path):
    engine, Session = init_db()
    session = Session()
    
    df = pd.read_csv(csv_path)
    
    print("=" * 60)
    print("IMPORTING DATA TO DATABASE")
    print("=" * 60)
    print(f"Records to import: {len(df)}")
    
    imported = 0
    updated = 0
    skipped = 0
    
    for idx, row in df.iterrows():
        name_value = row.get('name')
        
        if pd.isna(name_value) or str(name_value).strip() == '' or str(name_value) == 'Unknown':
            email_value = row.get('email')
            if pd.notna(email_value):
                client_name = f"Client_{email_value.split('@')[0]}"
            else:
                license_value = row.get('license_plate')
                if pd.notna(license_value):
                    client_name = f"Client_{license_value}"
                else:
                    print(f"  ⊘ Skipped row {idx+1}: No name, email, or license plate")
                    skipped += 1
                    continue
        else:
            client_name = str(name_value).strip()
        
        client = session.query(Client).filter_by(name=client_name).first()
        
        if not client:
            client = Client(
                name=client_name,
                email=row.get('email') if pd.notna(row.get('email')) else None,
                phone=row.get('phone') if pd.notna(row.get('phone')) else None,
                address=row.get('address') if pd.notna(row.get('address')) else None,
                postal_code=row.get('postal_code') if pd.notna(row.get('postal_code')) else None,
                city=row.get('city') if pd.notna(row.get('city')) else None,
                tax_id=str(row.get('tax_id')) if pd.notna(row.get('tax_id')) else None
            )
            session.add(client)
            session.flush()
            print(f"  + New client: {client_name}")
        else:
            if pd.notna(row.get('email')):
                client.email = row.get('email')
            if pd.notna(row.get('phone')):
                client.phone = row.get('phone')
            updated += 1
        
        policy_number = row.get('policy_number')
        if pd.notna(policy_number):
            policy = session.query(Policy).filter_by(policy_number=str(int(policy_number))).first()
        else:
            policy = None
        
        if not policy:
            start_date = None
            end_date = None
            due_date = None
            
            if pd.notna(row.get('coverage_start')):
                try:
                    start_date = datetime.strptime(row['coverage_start'], '%d/%m/%Y').date()
                except:
                    pass
            
            if pd.notna(row.get('coverage_end')):
                try:
                    end_date = datetime.strptime(row['coverage_end'], '%d/%m/%Y').date()
                except:
                    pass
            
            if pd.notna(row.get('due_date')):
                try:
                    due_date = datetime.strptime(row['due_date'], '%d/%m/%Y').date()
                except:
                    pass
            
            policy = Policy(
                client_id=client.id,
                policy_number=str(int(policy_number)) if pd.notna(policy_number) else None,
                provider=row.get('provider') if pd.notna(row.get('provider')) else None,
                policy_type=row.get('policy_type') if pd.notna(row.get('policy_type')) else 'OTHER',
                license_plate=row.get('license_plate') if pd.notna(row.get('license_plate')) else None,
                vehicle_model=row.get('vehicle_model') if pd.notna(row.get('vehicle_model')) else None,
                vehicle_year=int(row['vehicle_year']) if pd.notna(row.get('vehicle_year')) else None,
                premium=float(row['premium']) if pd.notna(row.get('premium')) else None,
                start_date=start_date,
                expiration_date=end_date,
                status=PolicyStatus.ACTIVE,
                payment_code=row.get('payment_code') if pd.notna(row.get('payment_code')) else None
            )
            session.add(policy)
            session.flush()
            
            if policy.premium and due_date:
                payment = Payment(
                    policy_id=policy.id,
                    amount=policy.premium,
                    due_date=due_date,
                    status=PaymentStatus.PENDING
                )
                session.add(payment)
            
            imported += 1
    
    session.commit()
    
    print(f"\n✓ Import complete!")
    print(f"  New clients/policies: {imported}")
    print(f"  Updated: {updated}")
    if skipped > 0:
        print(f"  Skipped: {skipped}")
    print("=" * 60)
    
    session.close()


if __name__ == "__main__":
    csv_path = 'data/processed/extracted_data.csv'
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
    
    import_from_csv(csv_path)
