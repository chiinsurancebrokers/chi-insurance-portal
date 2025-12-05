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
    else:
        print(f"  ✓ Paid: 0")
        print(f"  ⏳ Pending: 0")
        print(f"  ⚠️  Overdue: 0")
    
    if overdue > 0:
        print(f"\n⚠️  WARNING: {overdue} payments are overdue!")
        overdue_payments = session.query(Payment).filter_by(status=PaymentStatus.OVERDUE).limit(5).all()
        for payment in overdue_payments:
            print(f"    - {payment.policy.client.name}: €{payment.amount} (Due: {payment.due_date})")
    
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
        print(f"Phone: {client.phone or 'N/A'}")
        print(f"Policies: {len(client.policies)}")
    print(f"\nTotal: {len(clients)} clients")
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
    print("Leave blank to keep current value, type 'null' to clear")
    print()
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
    print(f"Current Address: {client.address or 'N/A'}")
    new_address = input("New Address: ").strip()
    if new_address == 'null':
        client.address = None
    elif new_address:
        client.address = new_address
    session.commit()
    print("\n✓ Client updated successfully!")
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
        print(f"No pending payment found for policy {policy_number}")
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
        print(f"No paid payment found for policy {policy_number}")
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
        print(f"  Policy #: {policy.policy_number}")
        print(f"  Type: {policy.policy_type}")
        print(f"  Amount: €{payment.amount}")
        print(f"  Due: {payment.due_date} ({days_left} days)")
    print(f"\nTotal: {len(payments)} pending payments")
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
        print(f"  Policy #: {policy.policy_number}")
        print(f"  Type: {policy.policy_type}")
        print(f"  Amount: €{payment.amount}")
        print(f"  Paid on: {payment.payment_date}")
    print(f"\nTotal: {len(payments)} paid payments")
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
    print("=" * 60)
    session.close()


def add_policy_interactive():
    session = get_session()
    print("=" * 60)
    print("ADD NEW POLICY (Interactive)")
    print("=" * 60)
    client_name = input("Client Name: ").strip()
    if not client_name:
        print("Client name required!")
        return
    client = session.query(Client).filter_by(name=client_name).first()
    if not client:
        print(f"\n✓ Creating new client: {client_name}")
        email = input("Email (optional): ").strip() or None
        phone = input("Phone (optional): ").strip() or None
        address = input("Address (optional): ").strip() or None
        client = Client(name=client_name, email=email, phone=phone, address=address)
        session.add(client)
        session.flush()
    else:
        print(f"✓ Found existing client: {client_name}")
    print("\n--- Policy Details ---")
    policy_number = input("Policy Number (optional): ").strip() or None
    provider = input("Provider: ").strip()
    policy_type = input("Policy Type (ΑΥΤΟΚΙΝΗΤΟ/ΖΩΗΣ/ΠΥΡΟΣ/OTHER): ").strip()
    license_plate = input("License Plate (if auto, optional): ").strip() or None
    premium = input("Premium (€): ").strip()
    due_date_str = input("Due Date (DD/MM/YYYY): ").strip()
    payment_code = input("Payment Code/RF (optional): ").strip() or None
    try:
        premium_float = float(premium)
        due_date = datetime.strptime(due_date_str, '%d/%m/%Y').date()
    except:
        print("Invalid premium or date format!")
        session.close()
        return
    policy = Policy(
        client_id=client.id, policy_number=policy_number, provider=provider,
        policy_type=policy_type, license_plate=license_plate, premium=premium_float,
        expiration_date=due_date, payment_code=payment_code, status=PolicyStatus.ACTIVE
    )
    session.add(policy)
    session.flush()
    payment = Payment(
        policy_id=policy.id, amount=premium_float, due_date=due_date, status=PaymentStatus.PENDING
    )
    session.add(payment)
    session.commit()
    print("\n✓ Policy added successfully!")
    print(f"  Client: {client_name}")
    print(f"  Provider: {provider}")
    print(f"  Premium: €{premium_float}")
    print(f"  Due: {due_date}")
    print("=" * 60)
    session.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("CHI Insurance Management System")
        print("=" * 60)
        print("Usage:")
        print("  python manage.py status                    - Payment dashboard")
        print("  python manage.py pending                   - List pending payments")
        print("  python manage.py paid                      - List paid payments")
        print("  python manage.py clients                   - List all clients")
        print("  python manage.py search <name>             - Search for client")
        print("  python manage.py edit <client_id>          - Edit client details")
        print("  python manage.py mark-paid <policy_num>    - Mark payment as paid")
        print("  python manage.py mark-unpaid <policy_num>  - Mark payment as unpaid")
        print("  python manage.py delete <client_id>         - Delete client")
" +
        "  python manage.py add-policy                - Add policy interactively")
        print("=" * 60)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "status":
        show_status()
    elif command == "pending":
        list_pending()
    elif command == "paid":
        list_paid()
    elif command == "clients":
        list_clients()
    elif command == "search" and len(sys.argv) > 2:
        search_client(sys.argv[2])
    elif command == "edit" and len(sys.argv) > 2:
        edit_client(sys.argv[2])
    elif command == "mark-paid" and len(sys.argv) > 2:
        mark_paid(sys.argv[2])
    elif command == "mark-unpaid" and len(sys.argv) > 2:
        mark_unpaid(sys.argv[2])
    elif command == "delete" and len(sys.argv) > 2:
        delete_client(sys.argv[2])
    elif command == "add-policy":
        add_policy_interactive()
    else:
        print("Invalid command. Use 'python manage.py' to see all commands.")


def delete_client(client_id):
    session = get_session()
    client = session.query(Client).filter_by(id=int(client_id)).first()
    if not client:
        print(f"Client ID {client_id} not found")
        session.close()
        return
    
        print("  python manage.py delete <client_id>         - Delete client")
    print(f"  Email: {client.email}")
    print(f"  Policies: {len(client.policies)}")
    confirm = input("Type 'yes' to confirm: ").strip()
    
    if confirm.lower() == 'yes':
        for policy in client.policies:
            for payment in policy.payments:
                session.delete(payment)
            session.delete(policy)
        session.delete(client)
        session.commit()
        print(f"✓ Client {client_id} deleted")
    else:
        print("Cancelled")
    
    session.close()
