#!/usr/bin/env python3
"""
Monthly Renewal Workflow Automation
1. Extract PDFs
2. Update database (smart merge)
3. Export consolidated data
4. Ready for sending renewals
"""

import os
import sys
from datetime import datetime
from pathlib import Path

def step1_extract_pdfs():
    print("=" * 60)
    print("STEP 1: EXTRACTING DATA FROM PDFs")
    print("=" * 60)
    
    result = os.system('python src/ocr/pdf_extractor.py data/raw_pdfs/')
    
    if result != 0:
        print("✗ PDF extraction failed!")
        return False
    
    print("\n✓ PDF extraction complete!")
    return True


def step2_smart_import():
    print("\n" + "=" * 60)
    print("STEP 2: SMART DATABASE UPDATE")
    print("=" * 60)
    
    import pandas as pd
    from src.database.models import get_session, Client, Policy, Payment, PaymentStatus, PolicyStatus
    
    session = get_session()
    
    csv_path = 'data/processed/extracted_data.csv'
    if not os.path.exists(csv_path):
        print("✗ No extracted data found!")
        return False
    
    df = pd.read_csv(csv_path)
    print(f"Processing {len(df)} records...")
    
    new_clients = 0
    updated_clients = 0
    new_policies = 0
    updated_policies = 0
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
                    print(f"  ⊘ Skipped row {idx+1}: No identifiable info")
                    skipped += 1
                    continue
        else:
            client_name = str(name_value).strip()
        
        # Find or create client
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
            new_clients += 1
            print(f"  + New client: {client_name}")
        else:
            # Update client info if new data available
            if pd.notna(row.get('email')) and not client.email:
                client.email = row.get('email')
                updated_clients += 1
            if pd.notna(row.get('phone')) and not client.phone:
                client.phone = row.get('phone')
        
        # Check for existing policy
        policy_number = row.get('policy_number')
        existing_policy = None
        
        if pd.notna(policy_number):
            existing_policy = session.query(Policy).filter_by(
                policy_number=str(int(policy_number))
            ).first()
        
        # Also check by license plate + provider for duplicate detection
        if not existing_policy and pd.notna(row.get('license_plate')):
            existing_policy = session.query(Policy).filter_by(
                client_id=client.id,
                license_plate=row.get('license_plate'),
                provider=row.get('provider')
            ).first()
        
        if existing_policy:
            # Update existing policy
            if pd.notna(row.get('premium')):
                existing_policy.premium = float(row['premium'])
            
            if pd.notna(row.get('coverage_end')):
                try:
                    new_exp = datetime.strptime(row['coverage_end'], '%d/%m/%Y').date()
                    if new_exp != existing_policy.expiration_date:
                        existing_policy.expiration_date = new_exp
                        
                        # Update payment due date too
                        payment = session.query(Payment).filter_by(
                            policy_id=existing_policy.id,
                            status=PaymentStatus.PENDING
                        ).first()
                        if payment:
                            payment.due_date = new_exp
                            payment.amount = existing_policy.premium
                        
                        updated_policies += 1
                        print(f"  ↻ Updated policy: {client_name} - {row.get('policy_type')}")
                except:
                    pass
        else:
            # Create new policy
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
                expiration_date=end_date or due_date,
                status=PolicyStatus.ACTIVE,
                payment_code=row.get('payment_code') if pd.notna(row.get('payment_code')) else None
            )
            session.add(policy)
            session.flush()
            
            if policy.premium and (due_date or end_date):
                payment = Payment(
                    policy_id=policy.id,
                    amount=policy.premium,
                    due_date=due_date or end_date,
                    status=PaymentStatus.PENDING
                )
                session.add(payment)
            
            new_policies += 1
            print(f"  + New policy: {client_name} - {row.get('policy_type')}")
    
    session.commit()
    
    print(f"\n✓ Database updated!")
    print(f"  New clients: {new_clients}")
    print(f"  Updated clients: {updated_clients}")
    print(f"  New policies: {new_policies}")
    print(f"  Updated policies: {updated_policies}")
    if skipped > 0:
        print(f"  Skipped: {skipped}")
    
    session.close()
    return True


def step3_export_consolidated():
    print("\n" + "=" * 60)
    print("STEP 3: EXPORTING CONSOLIDATED DATA")
    print("=" * 60)
    
    from src.database.models import get_session, Client, Policy, Payment, PaymentStatus
    import pandas as pd
    
    session = get_session()
    
    all_data = []
    
    # Get all active policies
    policies = session.query(Policy).filter_by(status='ACTIVE').all()
    
    for policy in policies:
        client = policy.client
        
        # Get pending payment if exists
        payment = session.query(Payment).filter_by(
            policy_id=policy.id,
            status=PaymentStatus.PENDING
        ).first()
        
        all_data.append({
            'client_name': client.name,
            'email': client.email or f'{client.name.replace(" ", "")}@example.com',
            'phone': client.phone or '',
            'service_name': f'{policy.policy_type} - {policy.provider}',
            'expiration_date': policy.expiration_date.strftime('%Y-%m-%d') if policy.expiration_date else '',
            'premium': policy.premium or '',
            'license_plate': policy.license_plate or '',
            'language': 'el'
        })
    
    df = pd.DataFrame(all_data)
    
    # Save consolidated file
    consolidated_path = 'data/processed/all_policies.csv'
    df.to_csv(consolidated_path, index=False, encoding='utf-8-sig')
    
    print(f"✓ Exported {len(df)} policies")
    print(f"  Saved to: {consolidated_path}")
    
    # Also update renewal system CSV
    renewal_csv = '/Users/christosiatropoulos/Documents/chris /renewal invitations /renewal_system/renewal_system 2/renewal_system_v2/clients.csv'
    df.to_csv(renewal_csv, index=False, encoding='utf-8-sig')
    print(f"  Updated renewal system CSV")
    
    session.close()
    return True


def step4_review():
    print("\n" + "=" * 60)
    print("STEP 4: REVIEW STATUS")
    print("=" * 60)
    
    os.system('python manage.py status')
    return True


def main():
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "MONTHLY RENEWAL WORKFLOW AUTOMATION" + " " * 13 + "║")
    print("╚" + "═" * 58 + "╝")
    
    print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Step 1: Extract PDFs
    if not step1_extract_pdfs():
        print("\n✗ Workflow stopped at Step 1")
        return
    
    # Step 2: Smart database update
    if not step2_smart_import():
        print("\n✗ Workflow stopped at Step 2")
        return
    
    # Step 3: Export consolidated
    if not step3_export_consolidated():
        print("\n✗ Workflow stopped at Step 3")
        return
    
    # Step 4: Review
    step4_review()
    
    print("\n" + "=" * 60)
    print("✓ MONTHLY WORKFLOW COMPLETE!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Review: python manage.py pending")
    print("  2. Send renewals: python send_renewals.py --dry-run")
    print("  3. Send live: python send_renewals.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
