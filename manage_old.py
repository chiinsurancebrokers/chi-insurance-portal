#!/usr/bin/env python3
import sys
from datetime import datetime, timedelta
from src.database.models import get_session, Client, Policy, Payment, PaymentStatus, PolicyStatus


def show_status():
    session = get_session()
    total_policies = session.query(Policy).count()
    active_policies = session.query(Policy).filter_by(status=PolicyStatus.ACTIVE).count()
    total_payments = session.query(Payment).count()
    paid = session.query(Payment).filter_by(status=PaymentStatus.PAID).count()
    pending = session.query(Payment).filter_by(status=PaymentStatus.PENDING).count()
    overdue = session.query(Payment).filter_by(status=PaymentStatus.OVERDUE).count()
    
    print("=" * 60)
    print("CHI INSURANCE - PAYMENT STATUS DASHBOARD")
    print("=" * 60)
    print(f"\nPOLICIES")
    print(f"  Total: {total_policies}")
    print(f"  Active: {active_policies}")
    print(f"\nPAYMENTS")
    print(f"  Total: {total_payments}")
    if total_payments > 0:
        print(f"  ✓ Paid: {paid} ({paid/total_payments*100:.1f}%)")
        print(f"  ⏳ Pending: {pending} ({pending/total_payments*100:.1f}%)")
        print(f"  ⚠️  Overdue: {overdue} ({overdue/total_payments*100:.1f}%)")
    
    if overdue > 0:
        print(f"\n⚠️  WARNING: {overdue} payments are overdue!")
    
    today = datetime.now().date()
    upcoming = session.query(Payment).filter(
        Payment.status == PaymentStatus.PENDING,
        Payment.due_date <= today + timedelta(days=7)
    ).all()
    
    if upcoming:
        print(f"\n📅 UPCOMING (Next 7 days): {len(upcoming)}")
        for payment in upcoming[:5]:
            days_left = (payment.due_date - today).days
            print(f"    - {payment.policy.client.name}: €{payment.amount} ({days_left} days)")
    
    print("=" * 60)
    session.close()


def list_clients():
    session = get_session()
    clients = session.query(Client).all()
    print("=" * 60)
    print("ALL CLIENTS")
    print("=" * 60)
    for client in clients:
        print(f"\nID: {client.id}")
        print(f"Name: {client.name}")
        print(f"Email: {client.email or 'N/A'}")
        print(f"Policies: {len(client.policies)}")
    print(f"\nTotal: {len(clients)} clients")
    print("=" * 60)
    session.close()


def search_client(search_term):
    session = get_session()
    clients = session.query(Client).filter(Client.name.like(f'%{search_term}%')).all()
    print("=" * 60)
    print(f"SEARCH RESULTS for '{search_term}'")
    print("=" * 60)
    if not clients:
        print("No clients found")
    else:
        for client in clients:
            print(f"\nID: {client.id}")
            print(f"Name: {client.name}")
            print(f"Email: {client.email or 'N/A'}")
            print(f"Policies: {len(client.policies)}")
            for policy in client.policies:
                print(f"  - {policy.policy_type} | {policy.provider} | Expires: {policy.expiration_date}")
    print("=" * 60)
    session.close()


def edit_client(client_id):
    session = get_session()
    client = session.query(Client).filter_by(id=int(client_id)).first()
    if not client:
        print(f"Client ID {client_id} not found")
        return
    print("=" * 60)
    print(f"EDITING CLIENT: {client.name}")
    print("=" * 60)
    print("Leave blank to keep current, type 'null' to clear\n")
    print(f"Current Name: {client.name}")
    new_name = input("New Name: ").strip()
    if new_name and new_name != 'null':
        client.name = new_name
    print(f"Current Email: {client.email or 'N/A'}")
    new_email = input("New Email: ").strip()
    if new_email == 'null':
        client.email = None
    elif new_email:
        client.email = new_email
    print(f"Current Phone: {client.phone or 'N/A'}")
    new_phone = input("New Phone: ").strip()
    if new_phone == 'null':
        client.phone = None
    elif new_phone:
        client.phone = new_phone
    session.commit()
    print("\n✓ Client updated!")
    print("=" * 60)
    session.close()


def delete_client(client_id):
    session = get_session()
    client = session.query(Client).filter_by(id=int(client_id)).first()
    if not client:
        print(f"Client ID {client_id} not found")
        session.close()
        return
    
    print("=" * 60)
    print(f"DELETE CLIENT: {client.name}")
    print("=" * 60)
    print(f"Email: {client.email}")
    print(f"Policies: {len(client.policies)}")
    for policy in client.policies:
        print(f"  - {policy.policy_type} | {policy.provider}")
    print("\nWARNING: This will delete client and all associated policies/payments")
    confirm = input("\nType 'DELETE' to confirm: ").strip()
    
    if confirm == 'DELETE':
        for policy in client.policies:
            for payment in policy.payments:
                session.delete(payment)
            session.delete(policy)
        session.delete(client)
        session.commit()
        print(f"\n✓ Client {client_id} deleted")
    else:
        print("\nCancelled")
    
    print("=" * 60)
    session.close()


def mark_paid(policy_number):
    session = get_session()
    policy = session.query(Policy).filter_by(policy_number=policy_number).first()
    if not policy:
        print(f"Policy {policy_number} not found")
        return
    payment = session.query(Payment).filter_by(policy_id=policy.id, status=PaymentStatus.PENDING).first()
    if payment:
        payment.status = PaymentStatus.PAID
        payment.payment_date = datetime.now().date()
        session.commit()
        print(f"✓ Marked as PAID: {policy.client.name} - €{payment.amount}")
    else:
        print(f"No pending payment for policy {policy_number}")
    session.close()


def mark_unpaid(policy_number):
    session = get_session()
    policy = session.query(Policy).filter_by(policy_number=policy_number).first()
    if not policy:
        print(f"Policy {policy_number} not found")
        return
    payment = session.query(Payment).filter_by(policy_id=policy.id, status=PaymentStatus.PAID).first()
    if payment:
        payment.status = PaymentStatus.PENDING
        payment.payment_date = None
        session.commit()
        print(f"✓ Marked as PENDING: {policy.client.name} - €{payment.amount}")
    else:
        print(f"No paid payment for policy {policy_number}")
    session.close()


def list_pending():
    session = get_session()
    payments = session.query(Payment).filter_by(status=PaymentStatus.PENDING).all()
    print("=" * 60)
    print("PENDING PAYMENTS")
    print("=" * 60)
    for payment in payments:
        policy = payment.policy
        client = policy.client
        days_left = (payment.due_date - datetime.now().date()).days
        print(f"\n{client.name}")
        print(f"  Policy: {policy.policy_number or 'N/A'} | {policy.policy_type}")
        print(f"  Amount: €{payment.amount}")
        print(f"  Due: {payment.due_date} ({days_left} days)")
    print(f"\nTotal: {len(payments)} pending")
    print("=" * 60)
    session.close()


def list_paid():
    session = get_session()
    payments = session.query(Payment).filter_by(status=PaymentStatus.PAID).all()
    print("=" * 60)
    print("PAID PAYMENTS")
    print("=" * 60)
    for payment in payments:
        policy = payment.policy
        client = policy.client
        print(f"\n{client.name}")
        print(f"  Policy: {policy.policy_number or 'N/A'} | {policy.policy_type}")
        print(f"  Amount: €{payment.amount}")
        print(f"  Paid: {payment.payment_date}")
    print(f"\nTotal: {len(payments)} paid")
    print("=" * 60)
    session.close()


def add_policy_interactive():
    session = get_session()
    print("=" * 60)
    print("ADD NEW POLICY")
    print("=" * 60)
    client_name = input("Client Name: ").strip()
    if not client_name:
        print("Client name required!")
        return
    client = session.query(Client).filter_by(name=client_name).first()
    if not client:
        print(f"\n✓ Creating new client: {client_name}")
        email = input("Email: ").strip() or None
        phone = input("Phone: ").strip() or None
        client = Client(name=client_name, email=email, phone=phone)
        session.add(client)
        session.flush()
    else:
        print(f"✓ Found existing client: {client_name}")
    print("\n--- Policy Details ---")
    provider = input("Provider: ").strip()
    policy_type = input("Type (ΑΥΤΟΚΙΝΗΤΟ/ΖΩΗΣ/ΠΥΡΟΣ): ").strip()
    license_plate = input("License Plate: ").strip() or None
    premium = input("Premium: ").strip()
    due_date_str = input("Due Date (DD/MM/YYYY): ").strip()
    try:
        premium_float = float(premium)
        due_date = datetime.strptime(due_date_str, '%d/%m/%Y').date()
    except:
        print("Invalid format!")
        session.close()
        return
    policy = Policy(
        client_id=client.id, provider=provider, policy_type=policy_type,
        license_plate=license_plate, premium=premium_float,
        expiration_date=due_date, status=PolicyStatus.ACTIVE
    )
    session.add(policy)
    session.flush()
    payment = Payment(
        policy_id=policy.id, amount=premium_float,
        due_date=due_date, status=PaymentStatus.PENDING
    )
    session.add(payment)
    session.commit()
    print("\n✓ Policy added!")
    print("=" * 60)
    session.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("CHI Insurance Management")
        print("=" * 60)
        print("  python manage.py status")
        print("  python manage.py clients")
        print("  python manage.py pending")
        print("  python manage.py paid")
        print("  python manage.py search <name>")
        print("  python manage.py edit <id>")
        print("  python manage.py delete <id>")
        print("  python manage.py policies")
        print("  python manage.py delete-policy <id>")
        print("  python manage.py mark-paid <policy_num>")
        print("  python manage.py mark-unpaid <policy_num>")
        print("  python manage.py add-policy")
        print("=" * 60)
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "status":
        show_status()
    elif cmd == "pending":
        list_pending()
    elif cmd == "paid":
        list_paid()
    elif cmd == "clients":
        list_clients()
    elif cmd == "search" and len(sys.argv) > 2:
        search_client(sys.argv[2])
    elif cmd == "edit" and len(sys.argv) > 2:
        edit_client(sys.argv[2])
    elif cmd == "delete" and len(sys.argv) > 2:
        delete_client(sys.argv[2])
    elif cmd == "policies":
        list_policies()
    elif cmd == "delete-policy" and len(sys.argv) > 2:
        delete_policy(sys.argv[2])
    elif cmd == "mark-paid" and len(sys.argv) > 2:
        mark_paid(sys.argv[2])
    elif cmd == "mark-unpaid" and len(sys.argv) > 2:
        mark_unpaid(sys.argv[2])
    elif cmd == "add-policy":
        add_policy_interactive()
    else:
        print("Invalid command")


def list_policies():
    session = get_session()
    policies = session.query(Policy).all()
    print("=" * 60)
    print("ALL POLICIES")
    print("=" * 60)
    for policy in policies:
        print(f"\nPolicy ID: {policy.id}")
        print(f"Client: {policy.client.name}")
        print(f"Type: {policy.policy_type}")
        print(f"Provider: {policy.provider}")
        print(f"Expires: {policy.expiration_date}")
        print(f"Premium: €{policy.premium or 'N/A'}")
    print(f"\nTotal: {len(policies)} policies")
    print("=" * 60)
    session.close()


def delete_policy(policy_id):
    session = get_session()
    policy = session.query(Policy).filter_by(id=int(policy_id)).first()
    if not policy:
        print(f"Policy ID {policy_id} not found")
        session.close()
        return
    
    print("=" * 60)
    print(f"DELETE POLICY: {policy.id}")
    print("=" * 60)
    print(f"Client: {policy.client.name}")
    print(f"Type: {policy.policy_type}")
    print(f"Provider: {policy.provider}")
    print(f"Expires: {policy.expiration_date}")
    print(f"Payments: {len(policy.payments)}")
    print("\nWARNING: This will delete policy and associated payments")
    confirm = input("\nType 'DELETE' to confirm: ").strip()
    
    if confirm == 'DELETE':
        for payment in policy.payments:
            session.delete(payment)
        session.delete(policy)
        session.commit()
        print(f"\n✓ Policy {policy_id} deleted")
    else:
        print("\nCancelled")
    
    print("=" * 60)
    session.close()
