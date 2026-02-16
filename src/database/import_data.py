#!/usr/bin/env python3
import sys
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import Base, Client, Policy, Payment, PaymentStatus, PolicyStatus

def parse_date(x):
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return None
    s = str(x).strip()
    if not s or s.lower() in ("nan", "none"):
        return None

    # supports: 25/12/2025 or 2025-12-25
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s.split()[0], fmt).date()
        except Exception:
            pass
    return None

def to_float(x):
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return None
    s = str(x).strip()
    if not s or s.lower() in ("nan", "none"):
        return None
    # handle Greek decimal style if present
    s = s.replace(".", "").replace(",", ".") if "," in s else s
    try:
        return float(s)
    except Exception:
        return None

def import_from_csv(csv_path: str):
    db_url =  __import__("os").getenv("DATABASE_URL", "sqlite:///data/chi_portal_local.db")
    engine = create_engine(db_url)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    print("=" * 60)
    print("IMPORTING DATA TO DATABASE")
    print("=" * 60)
    print(f"CSV: {csv_path}")
    print(f"Records: {len(df)}")

    imported_policies = 0
    updated_policies = 0
    created_clients = 0
    created_payments = 0
    skipped = 0

    for idx, row in df.iterrows():
        # --- Client identity ---
        name = row.get("name")
        email = row.get("email")
        license_plate = row.get("license_plate")

        client_name = None
        if pd.notna(name) and str(name).strip() and str(name).strip().lower() != "unknown":
            client_name = str(name).strip()
        elif pd.notna(email) and str(email).strip():
            client_name = f"Client_{str(email).split('@')[0]}"
        elif pd.notna(license_plate) and str(license_plate).strip():
            client_name = f"Client_{str(license_plate).strip()}"
        else:
            skipped += 1
            continue

        client = session.query(Client).filter_by(name=client_name).first()
        if not client:
            client = Client(
                name=client_name,
                email=str(email).strip() if pd.notna(email) and str(email).strip() else None,
                phone=str(row.get("phone")).strip() if pd.notna(row.get("phone")) else None,
                address=str(row.get("address")).strip() if pd.notna(row.get("address")) else None,
                postal_code=str(row.get("postal_code")).strip() if pd.notna(row.get("postal_code")) else None,
                city=str(row.get("city")).strip() if pd.notna(row.get("city")) else None,
                tax_id=str(row.get("tax_id")).strip() if pd.notna(row.get("tax_id")) else None,
            )
            session.add(client)
            session.flush()
            created_clients += 1
        else:
            # light update
            if pd.notna(email) and str(email).strip():
                client.email = str(email).strip()
            if pd.notna(row.get("phone")) and str(row.get("phone")).strip():
                client.phone = str(row.get("phone")).strip()

        # --- Dates / Premium ---
        start_date = parse_date(row.get("coverage_start"))
        end_date = parse_date(row.get("coverage_end"))
        due_date = parse_date(row.get("due_date")) or start_date or end_date
        premium = to_float(row.get("premium"))

        policy_number = row.get("policy_number")
        policy_number = str(policy_number).strip() if pd.notna(policy_number) and str(policy_number).strip() else None

        provider = str(row.get("provider")).strip() if pd.notna(row.get("provider")) else None
        policy_type = str(row.get("policy_type")).strip() if pd.notna(row.get("policy_type")) else "OTHER"
        license_plate_val = str(license_plate).strip() if pd.notna(license_plate) and str(license_plate).strip() else None

        # --- Find existing policy ---
        policy = None
        if policy_number:
            policy = session.query(Policy).filter_by(policy_number=policy_number).first()

        if not policy and license_plate_val:
            policy = session.query(Policy).filter_by(client_id=client.id, license_plate=license_plate_val).first()

        if not policy:
            policy = Policy(
                client_id=client.id,
                policy_number=policy_number,
                policy_type=policy_type,
                provider=provider,
                license_plate=license_plate_val,
                premium=premium,
                start_date=start_date,
                expiration_date=end_date,
                status=PolicyStatus.ACTIVE,
            )
            session.add(policy)
            session.flush()
            imported_policies += 1
        else:
            changed = False
            if premium is not None and policy.premium != premium:
                policy.premium = premium
                changed = True
            if start_date and policy.start_date != start_date:
                policy.start_date = start_date
                changed = True
            if end_date and policy.expiration_date != end_date:
                policy.expiration_date = end_date
                changed = True
            if provider and policy.provider != provider:
                policy.provider = provider
                changed = True
            if policy_type and policy.policy_type != policy_type:
                policy.policy_type = policy_type
                changed = True
            if license_plate_val and policy.license_plate != license_plate_val:
                policy.license_plate = license_plate_val
                changed = True
            if changed:
                updated_policies += 1

        # --- Payment (pending) ---
        if premium is not None and due_date is not None:
            pay = session.query(Payment).filter_by(policy_id=policy.id, status=PaymentStatus.PENDING).first()
            if not pay:
                pay = Payment(policy_id=policy.id, amount=premium, due_date=due_date, status=PaymentStatus.PENDING)
                session.add(pay)
                created_payments += 1
            else:
                # keep it aligned
                if pay.amount != premium:
                    pay.amount = premium
                if pay.due_date != due_date:
                    pay.due_date = due_date

    session.commit()
    session.close()

    print("\n✓ Import complete!")
    print(f"  New clients: {created_clients}")
    print(f"  New policies: {imported_policies}")
    print(f"  Updated policies: {updated_policies}")
    print(f"  Created/updated pending payments: {created_payments}")
    print(f"  Skipped rows: {skipped}")
    print("=" * 60)

if __name__ == "__main__":
    csv_path = "data/processed/extracted_data.csv"
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
    import_from_csv(csv_path)
