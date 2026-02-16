#!/usr/bin/env python3
"""
Fix incorrectly imported premiums
"""
from src.database.models import get_session, Policy
import pandas as pd

print("=" * 60)
print("FIXING PREMIUMS")
print("=" * 60)

# Read original CSV to get correct premiums
old_csv = '/Users/christosiatropoulos/Documents/chris /renewal invitations /renewal_system/renewal_system 2/renewal_system_v2/clients_backup.csv'

try:
    df = pd.read_csv(old_csv, encoding='utf-8')
except:
    old_csv = '/Users/christosiatropoulos/Documents/chris /renewal invitations /renewal_system/renewal_system 2/renewal_system_v2/clients.csv'
    df = pd.read_csv(old_csv, encoding='utf-8')

session = get_session()

fixed = 0
errors = 0

for idx, row in df.iterrows():
    client_name = row['client_name']
    expiration = pd.to_datetime(row['expiration_date']).date()
    
    # Find policy in database
    policies = session.query(Policy).join(Policy.client).filter(
        Policy.expiration_date == expiration
    ).all()
    
    found_policy = None
    for policy in policies:
        if policy.client.name == client_name:
            found_policy = policy
            break
    
    if not found_policy:
        continue
    
    # Parse premium correctly
    premium_str = str(row.get('premium', ''))
    
    if premium_str and premium_str != 'nan':
        try:
            # Count dots
            dot_count = premium_str.count('.')
            
            if dot_count == 0:
                # No dots, simple number
                correct_premium = float(premium_str.replace(',', '.'))
            elif dot_count == 1:
                # One dot - check if decimal or thousands
                parts = premium_str.split('.')
                if len(parts[1]) == 2:
                    # Two digits after dot = decimal (481.27)
                    correct_premium = float(premium_str)
                else:
                    # Not 2 digits = thousands separator (1.019)
                    correct_premium = float(premium_str.replace('.', '').replace(',', '.'))
            else:
                # Multiple dots = European format (1.019.86)
                correct_premium = float(premium_str.replace('.', '').replace(',', '.'))
            
            # Check if needs fixing
            if found_policy.premium and abs(found_policy.premium - correct_premium) > 1:
                print(f"  {client_name}")
                print(f"    Wrong: €{found_policy.premium}")
                print(f"    Correct: €{correct_premium}")
                
                found_policy.premium = correct_premium
                
                # Update payment amount too
                for payment in found_policy.payments:
                    payment.amount = correct_premium
                
                fixed += 1
        except Exception as e:
            print(f"  ✗ Error fixing {client_name}: {e}")
            errors += 1

session.commit()

print("\n" + "=" * 60)
print(f"✓ Fixed {fixed} premiums")
if errors > 0:
    print(f"✗ Errors: {errors}")
print("=" * 60)

session.close()
