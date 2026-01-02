#!/usr/bin/env python3
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps
import os

app = Flask(__name__, template_folder='app/templates')
app.secret_key = os.getenv('SECRET_KEY', 'chi-insurance-local-secret-2025')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

from src.database.models import get_session, Client, Policy, Payment, PaymentStatus, PolicyStatus, EmailQueue, EmailStatus

ADMIN_HASH = 'pbkdf2:sha256:1000000$Q8loSbCXnQvZgCXz$ee8b167d28f37981fc8d18f8f7792c2bd4ffe4e620be3c0836b1e76d4967e651'
DEMO_HASH = 'pbkdf2:sha256:1000000$8YEdUiTYWTuy44Ox$d1d9f17b11850a7a615fd449540662dda8c94133767ec3947b91c2eaa4590134'

ADMIN = {
    'username': 'admin',
    'password': ADMIN_HASH
}

USERS = {
    'alex-law@hotmail.com': {'password': DEMO_HASH, 'client_id': 1},
    'mpitsakoupolina@yahoo.gr': {'password': DEMO_HASH, 'client_id': 2},
    'apoTTapo@brevo.com': {'password': DEMO_HASH, 'client_id': 3},
    'DAMIORDOESNTLIVE@hotmail.com': {'password': DEMO_HASH, 'client_id': 4},
    'voula.roukouna@sensorbeta.gr': {'password': DEMO_HASH, 'client_id': 5},
    'papadimitriou.vasilis@brevo.com': {'password': DEMO_HASH, 'client_id': 9},
    'GEORGE_SAXI@hotmail.com': {'password': DEMO_HASH, 'client_id': 10},
    'ioanna.myriokefalitaki@brevo.com': {'password': DEMO_HASH, 'client_id': 11},
    'charis_kouki@yahoo.gr': {'password': DEMO_HASH, 'client_id': 12},
    'apostolopoulos.i@pg.com': {'password': DEMO_HASH, 'client_id': 13},
    'dco@merit.gr': {'password': DEMO_HASH, 'client_id': 14},
    'marivilampou@hotmail.com': {'password': DEMO_HASH, 'client_id': 15},
    'eboulakakis@yahoo.gr': {'password': DEMO_HASH, 'client_id': 16},
    'secretary@sensorbeta.gr': {'password': DEMO_HASH, 'client_id': 17},
    'spanos17@otenet.gr': {'password': DEMO_HASH, 'client_id': 18},
    'mkousoulakou@brevo.com': {'password': DEMO_HASH, 'client_id': 19},
    'gavriilidisioannis1@brevo.com': {'password': DEMO_HASH, 'client_id': 21},
    'asimakopoulouroul@brevo.com': {'password': DEMO_HASH, 'client_id': 22},
    'p.vernardakis@brevo.com': {'password': DEMO_HASH, 'client_id': 23},
    'manosalex73@brevo.com': {'password': DEMO_HASH, 'client_id': 24},
    'info@sroom.gr': {'password': DEMO_HASH, 'client_id': 25},
    'd.doulkeridis@brevo.com': {'password': DEMO_HASH, 'client_id': 26},
    'christ154ian@yahoo.com': {'password': DEMO_HASH, 'client_id': 27},
    'jojoxan@brevo.com': {'password': DEMO_HASH, 'client_id': 29},
    'EIRINIZLN@hotmail.com': {'password': DEMO_HASH, 'client_id': 30},
    'stavroulakormpaki@hotmail.com': {'password': DEMO_HASH, 'client_id': 31},
    'bezerianose@brevo.com': {'password': DEMO_HASH, 'client_id': 32},
    'micsot2@brevo.com': {'password': DEMO_HASH, 'client_id': 33},
    'drnkatsios@hotmail.com': {'password': DEMO_HASH, 'client_id': 34},
    'elentig@hotmail.com': {'password': DEMO_HASH, 'client_id': 35},
    'chourmousis@brevo.com': {'password': DEMO_HASH, 'client_id': 37},
    'mdetsi@brevo.com': {'password': DEMO_HASH, 'client_id': 38},
    'logistirio1922@brevo.com': {'password': DEMO_HASH, 'client_id': 39},
    'anna.xanthopoulou.c@brevo.com': {'password': DEMO_HASH, 'client_id': 40},
    'kostisarvanitis@brevo.com': {'password': DEMO_HASH, 'client_id': 41}
}

class User(UserMixin):
    def __init__(self, email, client_id=None, is_admin=False):
        self.id = email
        self.email = email
        self.client_id = client_id
        self.is_admin = is_admin

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Access denied', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@login_manager.user_loader
def load_user(email):
    if email == 'admin':
        return User('admin', is_admin=True)
    if email in USERS:
        return User(email, USERS[email]['client_id'])
    return None

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('email')
        password = request.form.get('password')
        
        # Check admin
        if username == ADMIN['username'] and check_password_hash(ADMIN['password'], password):
            user = User('admin', is_admin=True)
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        
        # Check client
        if username in USERS and check_password_hash(USERS[username]['password'], password):
            user = User(username, USERS[username]['client_id'])
            login_user(user)
            return redirect(url_for('dashboard'))
        
        flash('Λάθος στοιχεία σύνδεσης', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# CLIENT ROUTES
@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    db_session = get_session()
    client = db_session.query(Client).get(current_user.client_id)
    
    if not client:
        logout_user()
        db_session.close()
        return redirect(url_for('login'))
    
    policies = db_session.query(Policy).filter_by(client_id=client.id).all()
    
    total_policies = len(policies)
    active_policies = sum(1 for p in policies if p.status.value == 'ACTIVE')
    
    pending_payments = []
    for policy in policies:
        payment = db_session.query(Payment).filter_by(
            policy_id=policy.id,
            status=PaymentStatus.PENDING
        ).first()
        
        if payment:
            days_until = (payment.due_date - datetime.now().date()).days
            pending_payments.append({
                'policy': policy,
                'payment': payment,
                'days_until': days_until
            })
    
    pending_payments.sort(key=lambda x: x['days_until'])
    
    db_session.close()
    
    return render_template('dashboard.html',
                         client=client,
                         policies=policies,
                         total_policies=total_policies,
                         active_policies=active_policies,
                         pending_payments=pending_payments)

@app.route('/policies')
@login_required
def policies():
    db_session = get_session()
    client = db_session.query(Client).get(current_user.client_id)
    policies = db_session.query(Policy).filter_by(client_id=client.id).all()
    db_session.close()
    return render_template('policies.html', policies=policies, client=client)

@app.route('/payments')
@login_required
def payments():
    db_session = get_session()
    client = db_session.query(Client).get(current_user.client_id)
    
    all_payments = []
    for policy in client.policies:
        for payment in policy.payments:
            all_payments.append({
                'policy': policy,
                'payment': payment
            })
    
    all_payments.sort(key=lambda x: x['payment'].due_date, reverse=True)
    
    db_session.close()
    return render_template('payments.html', payments=all_payments, client=client)

# ADMIN ROUTES
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    from datetime import timedelta
    db_session = get_session()
    
    try:
        total_clients = db_session.query(Client).count()
        active_policies = db_session.query(Policy).filter_by(status=PolicyStatus.ACTIVE).count()
        pending_payments = db_session.query(Payment).filter_by(status=PaymentStatus.PENDING).count()
        
        # Expiring in next 30 days
        today = datetime.now().date()
        thirty_days = today + timedelta(days=30)
        expiring_soon = db_session.query(Policy).filter(
            Policy.expiration_date.between(today, thirty_days),
            Policy.status == PolicyStatus.ACTIVE
        ).count()
        
        stats = {
            'total_clients': total_clients,
            'active_policies': active_policies,
            'pending_payments': pending_payments,
            'expiring_soon': expiring_soon
        }
        
        return render_template('admin/dashboard.html', stats=stats)
    finally:
        db_session.close()

@app.route('/admin/clients')
@admin_required
def admin_clients():
    db_session = get_session()
    search = request.args.get('search', '')
    
    if search:
        clients = db_session.query(Client).filter(
            (Client.name.like(f'%{search}%')) | 
            (Client.email.like(f'%{search}%'))
        ).all()
    else:
        clients = db_session.query(Client).order_by(Client.name).all()
    
    # Load policy counts before closing session
    clients_data = []
    for client in clients:
        clients_data.append({
            'id': client.id,
            'name': client.name,
            'email': client.email,
            'phone': client.phone,
            'policy_count': len(client.policies)
        })
    
    db_session.close()
    return render_template('admin/clients.html', clients=clients_data, search=search)

@app.route('/admin/client/<int:client_id>')
@admin_required
def admin_client_detail(client_id):
    db_session = get_session()
    client = db_session.query(Client).get(client_id)
    policies = db_session.query(Policy).filter_by(client_id=client_id).all()
    
    all_payments = []
    for policy in policies:
        for payment in policy.payments:
            all_payments.append({'policy': policy, 'payment': payment})
    
    db_session.close()
    return render_template('admin/client_detail.html', client=client, policies=policies, payments=all_payments)

@app.route('/admin/payments')
@admin_required
def admin_payments():
    db_session = get_session()
    status_filter = request.args.get('status', 'all')
    
    if status_filter == 'all':
        payments = db_session.query(Payment).order_by(Payment.due_date.desc()).all()
    else:
        payments = db_session.query(Payment).filter_by(status=PaymentStatus[status_filter.upper()]).order_by(Payment.due_date.desc()).all()
    
    # Remove duplicates: group by client_id + policy_type + amount + due_date
    seen = set()
    payment_list = []
    
    for payment in payments:
        policy = db_session.query(Policy).get(payment.policy_id)
        client = db_session.query(Client).get(policy.client_id)
        
        # Create unique key
        key = (client.id, policy.policy_type, round(payment.amount, 2) if payment.amount else 0, payment.due_date)
        
        if key not in seen:
            seen.add(key)
            payment_list.append({
                'payment': payment,
                'policy': policy,
                'client': client
            })
    
    db_session.close()
    return render_template('admin/payments.html', payments=payment_list, status_filter=status_filter)

@app.route('/admin/payment/<int:payment_id>/update', methods=['POST'])
@admin_required
def admin_update_payment(payment_id):
    new_status = request.form.get('status')
    
    db_session = get_session()
    payment = db_session.query(Payment).get(payment_id)
    
    if payment:
        payment.status = PaymentStatus[new_status.upper()]
        if new_status.upper() == 'PAID':
            payment.payment_date = datetime.now().date()
        db_session.commit()
        flash(f'Payment status updated to {new_status}', 'success')
    
    db_session.close()
    return redirect(request.referrer or url_for('admin_payments'))


@app.route('/admin/client/add', methods=['GET', 'POST'])
@admin_required
def admin_add_client():
    if request.method == 'POST':
        db_session = get_session()
        
        client = Client(
            name=request.form.get('name'),
            email=request.form.get('email'),
            phone=request.form.get('phone'),
            address=request.form.get('address'),
            postal_code=request.form.get('postal_code'),
            city=request.form.get('city'),
            tax_id=request.form.get('tax_id')
        )
        
        db_session.add(client)
        db_session.commit()
        flash(f'Client {client.name} added successfully!', 'success')
        db_session.close()
        return redirect(url_for('admin_clients'))
    
    return render_template('admin/add_client.html')

@app.route('/admin/client/<int:client_id>/delete', methods=['POST'])
@admin_required
def admin_delete_client(client_id):
    db_session = get_session()
    client = db_session.query(Client).get(client_id)
    
    if client:
        # Delete all policies and payments
        for policy in client.policies:
            for payment in policy.payments:
                db_session.delete(payment)
            db_session.delete(policy)
        
        name = client.name
        db_session.delete(client)
        db_session.commit()
        flash(f'Client {name} deleted successfully!', 'success')
    
    db_session.close()
    return redirect(url_for('admin_clients'))


@app.route('/admin/payment/add', methods=['GET', 'POST'])
@admin_required
def admin_add_payment():
    db_session = get_session()
    
    if request.method == 'POST':
        payment = Payment(
            policy_id=int(request.form.get('policy_id')),
            amount=float(request.form.get('amount')),
            due_date=datetime.strptime(request.form.get('due_date'), '%Y-%m-%d').date(),
            status=PaymentStatus[request.form.get('status').upper()],
            notes=request.form.get('notes')
        )
        
        db_session.add(payment)
        db_session.commit()
        flash('Payment added successfully!', 'success')
        db_session.close()
        return redirect(url_for('admin_payments'))
    
    # GET: show form
    clients = db_session.query(Client).order_by(Client.name).all()
    client_id = request.args.get('client_id')
    
    policies = []
    if client_id:
        policies = db_session.query(Policy).filter_by(client_id=int(client_id)).all()
    
    db_session.close()
    return render_template('admin/add_payment.html', clients=clients, policies=policies, client_id=client_id)

@app.route('/admin/payment/<int:payment_id>/delete', methods=['POST'])
@admin_required
def admin_delete_payment(payment_id):
    db_session = get_session()
    payment = db_session.query(Payment).get(payment_id)
    
    if payment:
        db_session.delete(payment)
        db_session.commit()
        flash('Payment deleted successfully!', 'success')
    
    db_session.close()
    return redirect(url_for('admin_payments'))





@app.route('/admin/renewals')
@admin_required
def admin_renewals():
    """Show upcoming renewals and queue emails"""
    from datetime import timedelta
    db_session = get_session()
    
    try:
        today = datetime.now().date()
        # Get days filter from query param (default 30 days)
        days_ahead = request.args.get('days', 30, type=int)
        future_date = today + timedelta(days=days_ahead)
        
        # Filter by start_date (when payment is due)
        policies = db_session.query(Policy).filter(
            Policy.start_date.between(today, future_date),
            Policy.status == PolicyStatus.ACTIVE
        ).order_by(Policy.start_date).all()
        
        renewal_list = []
        for policy in policies:
            try:
                client = policy.client
                if not client:
                    continue
                
                payment = db_session.query(Payment).filter_by(
                    policy_id=policy.id,
                    status=PaymentStatus.PENDING
                ).first()
                
                if payment:
                    days_until = (policy.start_date - today).days
                    
                    # Check if already queued
                    queued = db_session.query(EmailQueue).filter_by(
                        policy_id=policy.id,
                        payment_id=payment.id
                    ).first()
                    
                    renewal_list.append({
                        'client': client,
                        'policy': policy,
                        'payment': payment,
                        'days_until': days_until,
                        'queued': queued is not None,
                        'sent': queued.status == EmailStatus.SENT if queued else False
                    })
            except Exception:
                continue
        
        return render_template('admin/renewals.html', renewals=renewal_list)
    finally:
        db_session.close()

@app.route('/admin/renewals/queue', methods=['POST'])
@admin_required
def admin_queue_emails():
    """Queue selected emails with agent selection (3P or CA)"""
    selected_ids = request.form.getlist('selected')
    
    if not selected_ids:
        flash('No emails selected', 'warning')
        return redirect(url_for('admin_renewals'))
    
    db_session = get_session()
    queued_count = 0
    
    try:
        for policy_id in selected_ids:
            policy = db_session.query(Policy).get(int(policy_id))
            if not policy:
                continue
            
            client = policy.client
            payment = db_session.query(Payment).filter_by(
                policy_id=policy.id,
                status=PaymentStatus.PENDING
            ).first()
            
            if not client or not client.email or not payment:
                continue
            
            # Check if already queued
            existing = db_session.query(EmailQueue).filter_by(
                policy_id=policy.id,
                payment_id=payment.id
            ).first()
            
            if existing:
                continue
            
            # Get agent selection for this policy (3p or ca)
            agent = request.form.get(f'agent_{policy_id}', '3p')
            
            # Generate email content with agent bank accounts
            has_greek = any(ord(char) > 127 for char in client.name)
            language = 'el' if has_greek else 'en'
            days_until = (policy.start_date - datetime.now().date()).days if policy.start_date else (payment.due_date - datetime.now().date()).days
            
            subject, body = generate_renewal_email(client, policy, payment, days_until, language, agent)
            
            # Queue email
            email = EmailQueue(
                client_id=client.id,
                policy_id=policy.id,
                payment_id=payment.id,
                recipient_email=client.email,
                subject=subject,
                body_html=body,
                status=EmailStatus.QUEUED
            )
            
            db_session.add(email)
            queued_count += 1
        
        db_session.commit()
        flash(f'Queued {queued_count} emails', 'success')
    except Exception as e:
        db_session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    finally:
        db_session.close()
    
    return redirect(url_for('admin_email_queue'))

@app.route('/admin/email-queue')
@admin_required
def admin_email_queue():
    """Show email queue"""
    db_session = get_session()
    
    try:
        emails = db_session.query(EmailQueue).order_by(EmailQueue.created_date.desc()).all()
        
        email_list = []
        for email in emails:
            email_list.append({
                'id': email.id,
                'client_name': email.client.name,
                'recipient': email.recipient_email,
                'subject': email.subject,
                'body_html': email.body_html,
                'status': email.status.value,
                'sent_at': email.sent_at,
                'error': email.error_message,
                'created': email.created_date
            })
        
        return render_template('admin/email_queue.html', emails=email_list)
    finally:
        db_session.close()

@app.route('/admin/email/send/<int:email_id>', methods=['POST'])
@admin_required
def admin_send_email(email_id):
    """Send a single queued email via Brevo"""
    import requests
    
    BREVO_API_KEY = os.getenv("BREVO_API_KEY")
    
    if not BREVO_API_KEY:
        flash("Email not configured - Add BREVO_API_KEY to Railway", "danger")
        return redirect(url_for("admin_email_queue"))
    
    db_session = get_session()
    
    try:
        email = db_session.query(EmailQueue).get(email_id)
        if not email:
            flash("Email not found", "danger")
            return redirect(url_for("admin_email_queue"))
        
        # Send via Brevo API
        recipient = email.recipient_email.strip() if email.recipient_email else ""
        
        headers = {
            "accept": "application/json",
            "api-key": BREVO_API_KEY,
            "content-type": "application/json"
        }
        
        payload = {
            "sender": {"name": "CHI Insurance", "email": "xiatropoulos@gmail.com"},
            "to": [{"email": recipient}],
            "subject": email.subject,
            "htmlContent": email.body_html
        }
        
        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code not in [200, 201]:
            raise Exception(f"Brevo API error: {response.text}")
        
        # Update status
        email.status = EmailStatus.SENT
        email.sent_at = datetime.now()
        db_session.commit()
        
        flash(f"Email sent to {email.recipient_email}", "success")
    except Exception as e:
        email.status = EmailStatus.FAILED
        email.error_message = str(e)
        db_session.commit()
        flash(f"Failed: {str(e)}", "danger")
    finally:
        db_session.close()
    
    return redirect(url_for("admin_email_queue"))

def generate_renewal_email(client, policy, payment, days_until, language, agent='3p'):
    """Generate email subject and body with bank accounts based on agent (3p or ca)"""
    from datetime import date
    
    # Seasonal greeting (Happy New Year until Feb 1st)
    today = date.today()
    show_new_year = today.month == 1 or (today.month == 2 and today.day == 1)
    
    # Bank accounts based on agent selection
    if agent == '3p':
        bank_info = """
    <h3 style="color: #1976d2;">Τραπεζικοί Λογαριασμοί</h3>
    <p style="font-size: 13px; color: #555;"><strong>ΔΙΚΑΙΟΥΧΟΣ: 3P INSURANCE AGENTS AE - ΑΦΜ 800478440</strong></p>
    <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
        <tr style="background: #f5f5f5;"><td style="padding: 8px; border: 1px solid #ddd;"><strong>ALPHA BANK</strong></td><td style="padding: 8px; border: 1px solid #ddd;">GR4801401340134002320003540</td></tr>
        <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>ΕΘΝΙΚΗ ΤΡΑΠΕΖΑ</strong></td><td style="padding: 8px; border: 1px solid #ddd;">GR3901108910000089147029808</td></tr>
        <tr style="background: #f5f5f5;"><td style="padding: 8px; border: 1px solid #ddd;"><strong>EUROBANK</strong></td><td style="padding: 8px; border: 1px solid #ddd;">GR3302602210000370200676490</td></tr>
        <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>ΠΕΙΡΑΙΩΣ</strong></td><td style="padding: 8px; border: 1px solid #ddd;">GR6201720890005089072164520</td></tr>
    </table>"""
    else:
        bank_info = """
    <h3 style="color: #1976d2;">Τραπεζικοί Λογαριασμοί</h3>
    <p style="font-size: 13px; color: #555;"><strong>ΔΙΚΑΙΟΥΧΟΣ: CA Insurance Agents - ΑΦΜ 800338387</strong></p>
    <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
        <tr style="background: #f5f5f5;"><td style="padding: 8px; border: 1px solid #ddd;"><strong>ALPHA BANK</strong></td><td style="padding: 8px; border: 1px solid #ddd;">GR4101401460146002320015029</td></tr>
        <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>EUROBANK</strong></td><td style="padding: 8px; border: 1px solid #ddd;">GR6802600270000300201693054</td></tr>
        <tr style="background: #f5f5f5;"><td style="padding: 8px; border: 1px solid #ddd;"><strong>ΕΘΝΙΚΗ ΤΡΑΠΕΖΑ</strong></td><td style="padding: 8px; border: 1px solid #ddd;">GR7301106690000066900657306</td></tr>
    </table>"""
    
    # Get start date
    start_date_str = policy.start_date.strftime('%d/%m/%Y') if policy.start_date else payment.due_date.strftime('%d/%m/%Y')
    
    if language == 'el':
        new_year_greeting = """
    <div style="background: linear-gradient(135deg, #1a237e 0%, #4a148c 100%); padding: 20px; border-radius: 10px; margin-bottom: 25px; text-align: center;">
        <h2 style="color: #ffffff; margin: 0; font-size: 20px; font-weight: bold;">🎉 Καλή Χρονιά 2026! 🎉</h2>
        <p style="color: #ffffff; margin: 10px 0 0 0; font-size: 14px;">Σας ευχόμαστε υγεία, ευτυχία και ευημερία!</p>
    </div>""" if show_new_year else ""
        
        subject = f"Ανανέωση Ασφαλιστηρίου - {policy.policy_type}"
        body = f"""<html><body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
<div style="max-width: 600px; margin: 0 auto; padding: 20px;">
    {new_year_greeting}
    <h2 style="color: #d32f2f;">Υπενθύμιση Ανανέωσης Ασφαλιστηρίου</h2>
    <p>Αγαπητή/έ <strong>{client.name}</strong>,</p>
    <p>Σας ενημερώνουμε ότι το ασφαλιστήριό σας πλησιάζει στην ημερομηνία πληρωμής.</p>
    <div style="background: #d4edda; padding: 15px; border-left: 4px solid #28a745; margin: 20px 0;">
        <strong><i>Αν η πληρωμή γίνεται μέσω πάγιας εντολής, δεν χρειάζεται να κάνετε καμία ενέργεια.</i></strong><br>
        <strong><i>Αν έχετε ήδη πληρώσει, παρακαλούμε αγνοήστε το παρόν μήνυμα.</i></strong>
    </div>
    <div style="background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0;">
        <strong>Υπολείπονται {days_until} {'ημέρα' if days_until == 1 else 'ημέρες'} μέχρι την πληρωμή</strong>
    </div>
    <h3 style="color: #1976d2;">Στοιχεία Ασφαλιστηρίου</h3>
    <table style="width: 100%; border-collapse: collapse;">
        <tr style="background: #f5f5f5;"><td style="padding: 10px; border: 1px solid #ddd;"><strong>Είδος:</strong></td><td style="padding: 10px; border: 1px solid #ddd;">{policy.policy_type}</td></tr>
        <tr><td style="padding: 10px; border: 1px solid #ddd;"><strong>Ασφαλιστική:</strong></td><td style="padding: 10px; border: 1px solid #ddd;">{policy.provider}</td></tr>
        {'<tr style="background: #f5f5f5;"><td style="padding: 10px; border: 1px solid #ddd;"><strong>Πινακίδα:</strong></td><td style="padding: 10px; border: 1px solid #ddd;">' + policy.license_plate + '</td></tr>' if policy.license_plate else ''}
        <tr><td style="padding: 10px; border: 1px solid #ddd;"><strong>Ασφάλιστρο:</strong></td><td style="padding: 10px; border: 1px solid #ddd;"><strong style="color: #d32f2f;">€{payment.amount:.2f}</strong></td></tr>
        <tr style="background: #f5f5f5;"><td style="padding: 10px; border: 1px solid #ddd;"><strong>Ημερομηνία Έναρξης:</strong></td><td style="padding: 10px; border: 1px solid #ddd;"><strong>{start_date_str}</strong></td></tr>
    </table>
    {bank_info}
    <p style="margin-top: 20px; font-size: 12px; color: #666;"><em>Για την άμεση και ορθή εξόφληση παρακαλούμε να αναγράψετε το ονοματεπώνυμό σας στην αιτιολογία της κατάθεσης.</em></p>
    <p style="margin-top: 30px;">Με εκτίμηση,<br><strong>CHI Insurance Brokers</strong></p>
</div></body></html>"""
    else:
        new_year_en = """
    <div style="background: linear-gradient(135deg, #1a237e 0%, #4a148c 100%); padding: 20px; border-radius: 10px; margin-bottom: 25px; text-align: center;">
        <h2 style="color: #ffd700; margin: 0; font-size: 24px;">🎉 Happy New Year 2026! 🎉</h2>
        <p style="color: #ffffff; margin: 10px 0 0 0;">Wishing you health, happiness and prosperity!</p>
    </div>""" if show_new_year else ""
        
        subject = f"Insurance Renewal - {policy.policy_type}"
        body = f"""<html><body style="font-family: Arial, sans-serif;">
<div style="max-width: 600px; margin: 0 auto; padding: 20px;">
    {new_year_en}
    <h2>Insurance Renewal Reminder</h2>
    <p>Dear <strong>{client.name}</strong>,</p>
    <p>Your insurance policy payment is approaching.</p>
    <p><strong>{days_until} days until payment</strong></p>
    <p><strong>Amount:</strong> €{payment.amount:.2f}<br><strong>Start Date:</strong> {start_date_str}</p>
    {bank_info}
    <p>Best regards,<br><strong>CHI Insurance Brokers</strong></p>
</div></body></html>"""
    
    return subject, body



@app.route('/admin/migrate-db')
@admin_required
def admin_migrate_db():
    """Create email_queue table if not exists"""
    from src.database.models import Base, get_engine
    try:
        engine = get_engine()
        Base.metadata.create_all(engine)
        flash('Database tables created successfully', 'success')
    except Exception as e:
        flash(f'Migration error: {str(e)}', 'danger')
    return redirect(url_for('admin_dashboard'))



@app.route('/admin/debug-env')
@admin_required
def admin_debug_env():
    """Debug environment variables"""
    import os
    resend_key = os.getenv('RESEND_API_KEY')
    
    debug_info = {
        'Has RESEND_API_KEY': resend_key is not None,
        'Key length': len(resend_key) if resend_key else 0,
        'Key starts with re_': resend_key.startswith('re_') if resend_key else False,
        'First 10 chars': resend_key[:10] if resend_key else 'NONE',
        'All env vars': list(os.environ.keys())
    }
    
    return f"<pre>{debug_info}</pre>"



@app.route('/admin/email/test', methods=['POST'])
@admin_required
def admin_test_email():
    """Send test email to admin via Brevo"""
    import requests
    
    try:
        BREVO_API_KEY = os.getenv("BREVO_API_KEY")
        
        headers = {
            "accept": "application/json",
            "api-key": BREVO_API_KEY,
            "content-type": "application/json"
        }
        
        payload = {
            "sender": {"name": "CHI Insurance", "email": "xiatropoulos@gmail.com"},
            "to": [{"email": "xiatropoulos@gmail.com"}],
            "subject": "Test Email from CHI Portal",
            "htmlContent": "<h2>Success!</h2><p>Brevo integration is working!</p>"
        }
        
        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            flash("Test email sent to xiatropoulos@gmail.com", "success")
        else:
            raise Exception(response.text)
    except Exception as e:
        flash(f"Test failed: {str(e)}", "danger")
    
    return redirect(url_for("admin_email_queue"))

@app.route('/admin/email-queue/clear', methods=['POST'])
@admin_required
def admin_clear_queue():
    """Clear all queued and failed emails"""
    db_session = get_session()
    
    try:
        deleted = db_session.query(EmailQueue).filter(
            EmailQueue.status.in_([EmailStatus.QUEUED, EmailStatus.FAILED])
        ).delete()
        
        db_session.commit()
        flash(f'Cleared {deleted} emails from queue', 'success')
    except Exception as e:
        db_session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    finally:
        db_session.close()
    
    return redirect(url_for('admin_email_queue'))



@app.route('/admin/csv-upload', methods=['GET', 'POST'])
@admin_required
def admin_csv_upload():
    """Upload and preview CSV changes"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file uploaded', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect(request.url)
        
        if not file.filename.endswith('.csv'):
            flash('Only CSV files allowed', 'danger')
            return redirect(request.url)
        
        # Save file temporarily
        import tempfile
        import os
        temp_path = os.path.join(tempfile.gettempdir(), file.filename)
        file.save(temp_path)
        
        # Parse and preview changes
        try:
            changes = parse_csv_changes(temp_path)
            session['csv_temp_path'] = temp_path
            session['csv_filename'] = file.filename
            return render_template('admin/csv_preview.html', changes=changes, filename=file.filename)
        except Exception as e:
            flash(f'Error parsing CSV: {str(e)}', 'danger')
            return redirect(request.url)
    
    return render_template('admin/csv_upload.html')

@app.route('/admin/csv-commit', methods=['POST'])
@admin_required
def admin_csv_commit():
    """Commit CSV changes to database"""
    temp_path = session.get('csv_temp_path')
    filename = session.get('csv_filename')
    
    if not temp_path:
        flash('No CSV data to commit', 'danger')
        return redirect(url_for('admin_csv_upload'))
    
    try:
        changes = parse_csv_changes(temp_path)
        result = commit_csv_changes(changes)
        
        flash(f'Success! Added {result["new"]} policies, Updated {result["updated"]}, Created {result["payments"]} payments', 'success')
        
        # Clean up
        import os
        if os.path.exists(temp_path):
            os.remove(temp_path)
        session.pop('csv_temp_path', None)
        session.pop('csv_filename', None)
        
    except Exception as e:
        flash(f'Error committing changes: {str(e)}', 'danger')
    
    return redirect(url_for('admin_csv_upload'))


def parse_csv_changes(filepath):
    """Parse CSV file - Production Report format from Greek insurance system"""
    from datetime import datetime
    
    db_session = get_session()
    
    # Try multiple encodings for Greek files
    encodings = ['utf-8-sig', 'utf-8', 'windows-1253', 'iso-8859-7', 'cp1253', 'latin1']
    file_content = None
    
    for enc in encodings:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                file_content = f.read()
            break
        except UnicodeDecodeError:
            continue
    
    if file_content is None:
        raise Exception('Could not decode file')
    
    lines = [l for l in file_content.split('\n') if l.strip()]
    
    # Find header row (skip title rows like "Παραγωγή;;;;;;")
    header_idx = 0
    for i, line in enumerate(lines):
        if 'Πελάτης' in line and 'Κλάδος' in line:
            header_idx = i
            break
    
    header_line = lines[header_idx]
    delimiter = ';'
    headers = [h.strip().strip('"') for h in header_line.split(delimiter)]
    
    print(f'DEBUG: Header found at line {header_idx + 1}')
    print(f'DEBUG: Headers: {headers[:8]}')
    
    changes = {
        'new_policies': [],
        'updated_policies': [],
        'unchanged': [],
        'new_clients': []
    }
    
    # Parse data rows
    for line_num, line in enumerate(lines[header_idx + 1:], start=1):
        if not line.strip() or line.startswith(';;;'):
            continue
        
        # Parse CSV row (handle quoted fields)
        values = []
        current = ''
        in_quotes = False
        for char in line:
            if char == '"':
                in_quotes = not in_quotes
            elif char == delimiter and not in_quotes:
                values.append(current.strip().strip('"'))
                current = ''
            else:
                current += char
        values.append(current.strip().strip('"'))
        
        # Create row dict
        row = {}
        for i, h in enumerate(headers):
            row[h] = values[i] if i < len(values) else ''
        
        # Extract data from Production Report format
        client_name = row.get('Πελάτης', '').strip()
        policy_number = row.get('Συμβόλαιο', '').strip()  # Policy number - unique identifier
        policy_type_raw = row.get('Κλάδος', '').strip()
        provider = row.get('Εταιρεία', '').strip()
        license_plate = row.get('Χαρακτ/κό', '').strip() or None
        premium_str = row.get('Μικτά', '0')
        start_str = row.get('Έναρξη', '')  # Start date - when payment is due
        expiry_str = row.get('Λήξη', '')   # Expiry date - when coverage ends
        
        if not client_name:
            continue
        
        # Clean license plate (skip invalid ones)
        if license_plate:
            # Invalid if: too long, contains keywords, or looks like a name (no digits)
            import re
            has_digits = bool(re.search(r'\d', license_plate))
            is_invalid = (
                len(license_plate) > 12 or 
                'ΜΕΤΑΦΟΡΑ' in license_plate or 
                'ΠΑΡΑΣΚΕΥΗ' in license_plate or
                not has_digits  # License plates must have numbers
            )
            if is_invalid:
                license_plate = None
        
        # Map Greek policy types to English
        type_map = {
            'ΖΩΗΣ': 'Life Insurance',
            'ΥΓΕΙΑΣ': 'Health Insurance', 
            'AYTOKINHTO': 'ΑΥΤΟΚΙΝΗΤΟ',
            'ΠΥΡΟΣ': 'Property Insurance',
            'ΠΥΡΟΣ-ΠΕΡΙΟΥΣΙΑΣ': 'Property Insurance'
        }
        policy_type = type_map.get(policy_type_raw, policy_type_raw)
        
        # Parse premium (Greek format: 1.234,56 -> 1234.56)
        try:
            # Remove thousands separator (.) then replace decimal separator (, -> .)
            clean_premium = premium_str.strip()
            if ',' in clean_premium:
                # Greek format: 1.234,56 or 234,56
                clean_premium = clean_premium.replace('.', '')  # Remove thousands sep
                clean_premium = clean_premium.replace(',', '.')  # Decimal sep
            premium = float(clean_premium) if clean_premium else 0.0
            # Sanity check: premiums over 50000 are likely parsing errors
            if premium > 50000:
                print(f'WARNING: Unusual premium {premium} for {client_name} - original: {premium_str}')
        except:
            premium = 0.0
        
        # Parse start date (Έναρξη - when payment is due)
        start_date = None
        if start_str:
            try:
                if '-' in start_str:
                    start_date = datetime.strptime(start_str.split()[0], '%Y-%m-%d').date()
                elif '/' in start_str:
                    start_date = datetime.strptime(start_str, '%d/%m/%Y').date()
            except:
                pass
        
        # Parse expiry date (Λήξη - when coverage ends)
        expiry_date = None
        if expiry_str:
            try:
                if '-' in expiry_str:
                    expiry_date = datetime.strptime(expiry_str.split()[0], '%Y-%m-%d').date()
                elif '/' in expiry_str:
                    expiry_date = datetime.strptime(expiry_str, '%d/%m/%Y').date()
            except:
                pass
        
        # Debug first 3 rows
        if line_num <= 3:
            print(f'DEBUG row {line_num}: {client_name} | {policy_type} | {provider} | {premium} | {expiry_date}')
        
        # Check if client exists in database (normalize name for matching)
        # Try exact match first
        client = db_session.query(Client).filter_by(name=client_name).first()
        
        # If not found, try normalized match (handle spaces around dashes)
        if not client:
            normalized_name = client_name.replace(' - ', '-').replace('- ', '-').replace(' -', '-').strip()
            client = db_session.query(Client).filter_by(name=normalized_name).first()
            
            # Also search all clients with normalized comparison
            if not client:
                for c in db_session.query(Client).all():
                    db_norm = c.name.replace(' - ', '-').replace('- ', '-').replace(' -', '-').strip()
                    if db_norm == normalized_name:
                        client = c
                        break
        
        if not client:
            changes['new_clients'].append({
                'name': client_name,
                'policy_number': policy_number,
                'policy_type': policy_type,
                'provider': provider,
                'license_plate': license_plate,
                'premium': premium,
                'start_date': start_date,
                'expiry_date': expiry_date
            })
            continue
        
        # Check if policy exists for this client (use policy_number as primary identifier)
        existing = None
        if policy_number:
            existing = db_session.query(Policy).filter_by(
                policy_number=policy_number
            ).first()
        
        # Fallback: check by license plate or type/provider
        if not existing and license_plate:
            existing = db_session.query(Policy).filter_by(
                client_id=client.id,
                license_plate=license_plate
            ).first()
        
        if not existing:
            existing = db_session.query(Policy).filter_by(
                client_id=client.id,
                policy_type=policy_type,
                provider=provider
            ).first()
        
        if not existing:
            # New policy for existing client
            changes['new_policies'].append({
                'client_name': client_name,
                'client_id': client.id,
                'policy_number': policy_number,
                'policy_type': policy_type,
                'provider': provider,
                'license_plate': license_plate,
                'premium': premium,
                'start_date': start_date,
                'expiry_date': expiry_date
            })
        elif existing.premium != premium or existing.expiration_date != expiry_date or existing.start_date != start_date:
            # Policy exists but needs update
            changes['updated_policies'].append({
                'client_name': client_name,
                'policy_id': existing.id,
                'policy_number': policy_number,
                'policy_type': policy_type,
                'license_plate': license_plate,
                'old_premium': existing.premium,
                'new_premium': premium,
                'old_start': existing.start_date,
                'new_start': start_date,
                'old_expiry': existing.expiration_date,
                'new_expiry': expiry_date
            })
        else:
            # Policy unchanged
            changes['unchanged'].append({
                'client_name': client_name,
                'policy_type': policy_type
            })
    
    print(f'DEBUG RESULTS: new_clients={len(changes["new_clients"])} (with policies), new_policies_for_existing_clients={len(changes["new_policies"])}, updated={len(changes["updated_policies"])}, unchanged={len(changes["unchanged"])}')
    
    db_session.close()
    return changes



def commit_csv_changes(changes):
    """Commit parsed changes to database"""
    from datetime import datetime
    db_session = get_session()
    
    stats = {'new': 0, 'updated': 0, 'payments': 0, 'clients': 0}
    
    try:
        # Create new clients
        for item in changes['new_clients']:
            client = Client(name=item['name'])
            db_session.add(client)
            db_session.flush()
            
            policy = Policy(
                client_id=client.id,
                policy_number=item.get('policy_number'),
                policy_type=item['policy_type'],
                provider=item['provider'],
                license_plate=item['license_plate'],
                premium=item['premium'],
                expiration_date=item['expiry_date'],
                start_date=item.get('start_date') or datetime.now().date(),
                status=PolicyStatus.ACTIVE
            )
            db_session.add(policy)
            db_session.flush()
            
            if item['expiry_date'] and item['premium']:
                payment = Payment(
                    policy_id=policy.id,
                    amount=item['premium'],
                    due_date=item['expiry_date'],
                    status=PaymentStatus.PENDING
                )
                db_session.add(payment)
                stats['payments'] += 1
            
            stats['clients'] += 1
            stats['new'] += 1
        
        # Add new policies
        for item in changes['new_policies']:
            policy = Policy(
                client_id=item['client_id'],
                policy_number=item.get('policy_number'),
                policy_type=item['policy_type'],
                provider=item['provider'],
                license_plate=item['license_plate'],
                premium=item['premium'],
                expiration_date=item['expiry_date'],
                start_date=item.get('start_date') or datetime.now().date(),
                status=PolicyStatus.ACTIVE
            )
            db_session.add(policy)
            db_session.flush()
            
            if item['expiry_date'] and item['premium']:
                payment = Payment(
                    policy_id=policy.id,
                    amount=item['premium'],
                    due_date=item['expiry_date'],
                    status=PaymentStatus.PENDING
                )
                db_session.add(payment)
                stats['payments'] += 1
            
            stats['new'] += 1
        
        # Update existing policies
        for item in changes['updated_policies']:
            policy = db_session.query(Policy).get(item['policy_id'])
            if policy:
                policy.premium = item['new_premium']
                policy.policy_number = item.get('policy_number') or policy.policy_number
                policy.start_date = item.get('new_start') or policy.start_date
                policy.expiration_date = item['new_expiry']
                
                # Update or create payment
                payment = db_session.query(Payment).filter_by(
                    policy_id=policy.id,
                    status=PaymentStatus.PENDING
                ).first()
                
                if payment:
                    payment.amount = item['new_premium']
                    payment.due_date = item['new_expiry']
                else:
                    payment = Payment(
                        policy_id=policy.id,
                        amount=item['new_premium'],
                        due_date=item['new_expiry'],
                        status=PaymentStatus.PENDING
                    )
                    db_session.add(payment)
                    stats['payments'] += 1
                
                stats['updated'] += 1
        
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        raise e
    finally:
        db_session.close()
    
    return stats



@app.route('/admin/policies')
@admin_required
def admin_policies():
    """View all policies"""
    db_session = get_session()
    
    try:
        search = request.args.get('search', '')
        
        if search:
            policies = db_session.query(Policy).join(Client).filter(
                Client.name.ilike(f'%{search}%')
            ).order_by(Policy.expiration_date).all()
        else:
            policies = db_session.query(Policy).order_by(Policy.expiration_date).all()
        
        policy_list = []
        for policy in policies:
            policy_list.append({
                'id': policy.id,
                'policy_number': policy.policy_number,
                'client_name': policy.client.name if policy.client else 'Unknown',
                'policy_type': policy.policy_type,
                'provider': policy.provider,
                'license_plate': policy.license_plate,
                'premium': policy.premium,
                'start_date': policy.start_date,
                'expiration_date': policy.expiration_date,
                'status': policy.status.value if policy.status else 'Unknown'
            })
        
        return render_template('admin/policies.html', policies=policy_list, search=search)
    finally:
        db_session.close()



@app.route('/admin/policy/<int:policy_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_policy(policy_id):
    """Edit policy"""
    db_session = get_session()
    
    try:
        policy = db_session.query(Policy).get(policy_id)
        if not policy:
            flash('Policy not found', 'danger')
            return redirect(url_for('admin_policies'))
        
        if request.method == 'POST':
            policy.policy_type = request.form.get('policy_type')
            policy.provider = request.form.get('provider')
            policy.license_plate = request.form.get('license_plate') or None
            
            premium_str = request.form.get('premium', '0').replace(',', '.')
            try:
                policy.premium = float(premium_str)
            except:
                policy.premium = 0.0
            
            start_date_str = request.form.get('start_date')
            if start_date_str:
                policy.start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            
            expiry_date_str = request.form.get('expiration_date')
            if expiry_date_str:
                policy.expiration_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
            
            status_str = request.form.get('status')
            if status_str:
                policy.status = PolicyStatus[status_str]
            
            db_session.commit()
            flash('Policy updated successfully', 'success')
            return redirect(url_for('admin_policies'))
        
        return render_template('admin/edit_policy.html', policy=policy)
    finally:
        db_session.close()

@app.route('/admin/policy/<int:policy_id>/delete', methods=['POST'])
@admin_required
def admin_delete_policy(policy_id):
    """Delete policy and associated payments"""
    db_session = get_session()
    
    try:
        policy = db_session.query(Policy).get(policy_id)
        if not policy:
            flash('Policy not found', 'danger')
            return redirect(url_for('admin_policies'))
        
        client_name = policy.client.name if policy.client else 'Unknown'
        
        # Delete associated payments first
        db_session.query(Payment).filter_by(policy_id=policy_id).delete()
        
        # Delete policy
        db_session.delete(policy)
        db_session.commit()
        
        flash(f'Policy for {client_name} deleted successfully', 'success')
    except Exception as e:
        db_session.rollback()
        flash(f'Error deleting policy: {str(e)}', 'danger')
    finally:
        db_session.close()
    
    return redirect(url_for('admin_policies'))


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

# =========================
# ADMIN PASSWORD LOGIN (TEMP)
# =========================
import os

ADMIN_ALLOWED_LOGINS = {"admin", "info@chiinsurancebrokers.com"}
# Works now with default, but can be overridden securely by env var:
# export CHI_ADMIN_PASSWORD="admin2025!"
ADMIN_PASSWORD = os.getenv("CHI_ADMIN_PASSWORD", "admin2025!")

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login_password_v2():
    if request.method == "POST":
        login_id = (request.form.get("login") or "").strip().lower()
        password = request.form.get("password") or ""

        if login_id in ADMIN_ALLOWED_LOGINS and password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            session["logged_in"] = True
            session["user_email"] = "info@chiinsurancebrokers.com"
            flash("Admin login successful", "success")
            return redirect("/admin/dashboard")

        flash("Invalid admin credentials", "danger")

    return render_template("admin_login.html")

@app.route("/admin-logout")
def admin_logout():

    app.run(debug=False, host='0.0.0.0', port=port)

@app.route('/admin/client/<int:client_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_client(client_id):
    db_session = get_session()
    client = db_session.query(Client).get(client_id)
    
    if not client:
        flash('Client not found', 'danger')
        db_session.close()
        return redirect(url_for('admin_clients'))
    
    if request.method == 'POST':
        client.name = request.form.get('name')
        client.email = request.form.get('email')
        client.phone = request.form.get('phone')
        client.address = request.form.get('address')
        client.postal_code = request.form.get('postal_code')
        client.city = request.form.get('city')
        client.tax_id = request.form.get('tax_id')
        
        db_session.commit()
        flash(f'Client {client.name} updated successfully!', 'success')
        db_session.close()
        return redirect(url_for('admin_client_detail', client_id=client_id))
    
    db_session.close()
    return render_template('admin/edit_client.html', client=client)


# ================================
# Clients & Policies 2025–2026 DB
# ================================
import sqlite3
from pathlib import Path

@app.route('/admin/clients-policies-2025-2026')
def admin_clients_policies_2025_2026():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))

    db_path = Path('data/processed/clients_policy_2025_2026.db')

    if not db_path.exists():
        return render_template(
            'admin/clients_policies_2025_2026.html',
            rows=[],
            q='',
            error=f"DB not found: {db_path}"
        )

    q = (request.args.get('q') or '').strip()

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    sql = "SELECT * FROM client_policy_2025_2026"
    params = []

    if q:
        sql += """
        WHERE
            [Επωνυμία] LIKE ? OR
            [Email] LIKE ? OR
            [Kινητό] LIKE ? OR
            [ΑΦΜ] LIKE ? OR
            [Συμβόλαιο] LIKE ?
        """
        params = [f"%{q}%"] * 5

    sql += " ORDER BY [Λήξη] ASC"
    rows = conn.execute(sql, params).fetchall()
    conn.close()

    return render_template(
        'admin/clients_policies_2025_2026.html',
        rows=rows,
        q=q,
        error=None
    )

# =========================
# ADMIN ACCESS CONFIG
# =========================
ADMIN_EMAILS = {
    "christos@chi-insurance.gr",
    "info@chi-insurance.gr"
}

@app.before_request
def set_admin_from_email():
    email = session.get("user_email")
    if email and email.lower() in ADMIN_EMAILS:
        session["admin_logged_in"] = True

# =========================
# FIX USER EMAIL IN SESSION
# =========================
@app.before_request
def fix_user_email_session():
    if session.get("logged_in"):
        email = session.get("user_email") or session.get("email")
        if email:
            session["user_email"] = email.lower()

# =========================
# TEMP DEV LOGIN (LOCAL)
# =========================
@app.route('/dev-login')
def dev_login():
    session['logged_in'] = True
    session['user_email'] = 'xiatropoulos@gmail.com'
    session['admin_logged_in'] = True
    return redirect('/admin/dashboard')
    session.pop("admin_logged_in", None)
    flash("Admin logged out", "info")
    return redirect("/")

# Shortcut: send users to admin password login page
@app.route("/admin")
def admin_shortcut():
    return redirect("/admin-login")

# =========================
# FIXED ADMIN LOGOUT ROUTE
# =========================
@app.route("/admin-logout-fixed")
def admin_logout_fixed():
    session.pop("admin_logged_in", None)
    flash("Admin logged out", "info")
    return redirect("/")

# =========================
# ADMIN LOGIN DEBUG (SAFE)
# =========================
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login_password():
    debug = {}

    if request.method == "POST":
        login_id = (request.form.get("login") or "").strip().lower()
        password = request.form.get("password") or ""

        debug["login_received"] = login_id
        debug["login_allowed"] = login_id in ADMIN_ALLOWED_LOGINS
        debug["password_length"] = len(password)
        debug["env_password_set"] = bool(os.getenv("CHI_ADMIN_PASSWORD"))
        debug["password_matches"] = password == ADMIN_PASSWORD

        if debug["login_allowed"] and debug["password_matches"]:
            session["admin_logged_in"] = True
            session["logged_in"] = True
            session["user_email"] = "info@chiinsurancebrokers.com"
            return redirect("/admin/dashboard")

    return render_template(
        "admin_login.html",
        debug=debug
    )

# =========================
# ADMIN LOGIN DEBUG PAGE (SAFE)
# =========================
@app.route("/admin-login-debug", methods=["GET", "POST"])
def admin_login_password_debug():
    debug = {}

    if request.method == "POST":
        login_id = (request.form.get("login") or "").strip().lower()
        password = request.form.get("password") or ""

        debug["login_received"] = login_id
        debug["login_allowed"] = login_id in ADMIN_ALLOWED_LOGINS
        debug["password_length"] = len(password)
        debug["env_password_set"] = bool(os.getenv("CHI_ADMIN_PASSWORD"))
        debug["password_matches"] = password == ADMIN_PASSWORD
        debug["allowed_logins"] = sorted(list(ADMIN_ALLOWED_LOGINS))

        if debug["login_allowed"] and debug["password_matches"]:
            session["admin_logged_in"] = True
            session["logged_in"] = True
            session["user_email"] = "info@chiinsurancebrokers.com"
            debug["login_success"] = True
            return redirect("/admin/dashboard")

        debug["login_success"] = False

    return render_template("admin_login_debug.html", debug=debug)

# =========================
# ADMIN LOGIN DEBUG v2 (STAYS ON PAGE)
# =========================
@app.route("/admin-login-debug2", methods=["GET", "POST"])
def admin_login_password_debug2():
    debug = {"note": "This page never redirects; it always shows debug JSON after POST."}

    if request.method == "POST":
        login_id = (request.form.get("login") or "").strip().lower()
        password = request.form.get("password") or ""

        debug["login_received"] = login_id
        debug["login_allowed"] = login_id in ADMIN_ALLOWED_LOGINS
        debug["allowed_logins"] = sorted(list(ADMIN_ALLOWED_LOGINS))

        debug["password_length"] = len(password)
        debug["env_password_set"] = bool(os.getenv("CHI_ADMIN_PASSWORD"))
        debug["admin_password_length"] = len(ADMIN_PASSWORD)
        debug["password_matches"] = (password == ADMIN_PASSWORD)

        if debug["login_allowed"] and debug["password_matches"]:
            session["admin_logged_in"] = True
            session["logged_in"] = True
            session["user_email"] = "info@chiinsurancebrokers.com"
            debug["login_success"] = True
        else:
            debug["login_success"] = False

    return render_template("admin_login_debug2.html", debug=debug)

# =========================
# Make /admin-login use the working debug2 logic
# =========================
@app.route("/admin-login-fixed")
def admin_login_fixed_redirect():
    return redirect("/admin-login-debug2")

# =========================
# Admin login v3 (redirects on success)
# =========================
@app.route("/admin-login-v3", methods=["GET", "POST"])
def admin_login_v3():
    debug = {}
    if request.method == "POST":
        login_id = (request.form.get("login") or "").strip().lower()
        password = request.form.get("password") or ""

        ok = (login_id in ADMIN_ALLOWED_LOGINS) and (password == ADMIN_PASSWORD)
        if ok:
            session["admin_logged_in"] = True
            session["logged_in"] = True
            session["user_email"] = "info@chiinsurancebrokers.com"
            return redirect("/admin/dashboard")

        debug = {"error": "Invalid admin credentials", "login_received": login_id}

    return render_template("admin_login_v3.html", debug=debug)

# =========================
# ADMIN SESSION SYNC PATCH
# =========================
def ensure_admin_session():
    if session.get("admin_logged_in"):
        session["is_admin"] = True
        session["role"] = "admin"
        session["user_role"] = "admin"
        session["admin"] = True

@app.before_request
def before_every_request():
    ensure_admin_session()

# =========================
# DB PATH OVERRIDE (LOCAL SAFE)
# =========================
from pathlib import Path

try:
    _BASE = Path(__file__).resolve().parent
    _DATA = _BASE / "data" / "processed"
    _DATA.mkdir(parents=True, exist_ok=True)

    # This is the MAIN DB the portal should use (clients/policies/payments)
    db_path = _DATA / "chi_portal.db"

    # If there is any older variable name used elsewhere, sync it too
    DB_PATH = str(db_path)
except Exception:
    pass

# =========================
# PORTAL DB (clients/policies/payments) - LOCAL
# =========================
from pathlib import Path
_BASE = Path(__file__).resolve().parent
_PORTAL_DB = _BASE / "data" / "processed" / "chi_portal.db"
_PORTAL_DB.parent.mkdir(parents=True, exist_ok=True)
db_path = _PORTAL_DB
DB_PATH = str(_PORTAL_DB)

# =========================
# DASHBOARD SAFE MODE (NO DB TABLES YET)
# =========================
from sqlalchemy.exc import OperationalError

_original_admin_dashboard = None
try:
    _original_admin_dashboard = admin_dashboard
except Exception:
    _original_admin_dashboard = None

@app.route('/admin/dashboard-safe')
@admin_required
def admin_dashboard_safe():
    try:
        return _original_admin_dashboard()
    except Exception as e:
        # show empty stats rather than 500
        stats = {
            "total_clients": 0,
            "total_policies": 0,
            "total_payments": 0,
            "error": str(e)
        }
        return render_template('admin/dashboard.html', stats=stats)
