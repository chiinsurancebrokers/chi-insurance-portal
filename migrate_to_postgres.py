#!/usr/bin/env python3
"""
Migrate SQLite data to PostgreSQL (Supabase)
"""
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

print("=" * 60)
print("MIGRATING SQLITE → POSTGRESQL (SUPABASE)")
print("=" * 60)

# Get Supabase URL
supabase_url = input("\nPaste Supabase PostgreSQL URL: ").strip()

if not supabase_url.startswith('postgresql://'):
    print("Error: Invalid PostgreSQL URL")
    sys.exit(1)

# SQLite source
sqlite_engine = create_engine('sqlite:///data/database/chi_insurance.db')
SQLiteSession = sessionmaker(bind=sqlite_engine)

# PostgreSQL target
postgres_engine = create_engine(supabase_url)
PostgresSession = sessionmaker(bind=postgres_engine)

sqlite_session = SQLiteSession()
postgres_session = PostgresSession()

try:
    # Import models
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from src.database.models import Client, Policy, Payment
    
    # Migrate Clients
    print("\n📋 Migrating clients...")
    clients = sqlite_session.query(Client).all()
    
    client_map = {}
    
    for old_client in clients:
        new_client = Client(
            name=old_client.name,
            email=old_client.email,
            phone=old_client.phone,
            address=old_client.address,
            postal_code=old_client.postal_code,
            city=old_client.city,
            tax_id=old_client.tax_id
        )
        postgres_session.add(new_client)
        postgres_session.flush()
        
        client_map[old_client.id] = new_client.id
        print(f"  ✓ {old_client.name}")
    
    print(f"  Total: {len(clients)} clients")
    
    # Migrate Policies
    print("\n📄 Migrating policies...")
    policies = sqlite_session.query(Policy).all()
    
    policy_map = {}
    
    for old_policy in policies:
        new_policy = Policy(
            client_id=client_map[old_policy.client_id],
            policy_number=old_policy.policy_number,
            provider=old_policy.provider,
            policy_type=old_policy.policy_type,
            license_plate=old_policy.license_plate,
            vehicle_model=old_policy.vehicle_model,
            vehicle_year=old_policy.vehicle_year,
            premium=old_policy.premium,
            start_date=old_policy.start_date,
            expiration_date=old_policy.expiration_date,
            status=old_policy.status,
            payment_code=old_policy.payment_code
        )
        postgres_session.add(new_policy)
        postgres_session.flush()
        
        policy_map[old_policy.id] = new_policy.id
    
    print(f"  Total: {len(policies)} policies")
    
    # Migrate Payments
    print("\n💰 Migrating payments...")
    payments = sqlite_session.query(Payment).all()
    
    for old_payment in payments:
        new_payment = Payment(
            policy_id=policy_map[old_payment.policy_id],
            amount=old_payment.amount,
            payment_date=old_payment.payment_date,
            due_date=old_payment.due_date,
            status=old_payment.status,
            payment_method=old_payment.payment_method,
            notes=old_payment.notes
        )
        postgres_session.add(new_payment)
    
    print(f"  Total: {len(payments)} payments")
    
    # Commit all
    postgres_session.commit()
    
    print("\n" + "=" * 60)
    print("✅ MIGRATION COMPLETE!")
    print("=" * 60)
    print(f"✓ Clients: {len(clients)}")
    print(f"✓ Policies: {len(policies)}")
    print(f"✓ Payments: {len(payments)}")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    postgres_session.rollback()
finally:
    sqlite_session.close()
    postgres_session.close()
