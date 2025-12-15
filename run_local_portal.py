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

from src.database.models import get_session, Client, Policy, Payment, PaymentStatus, PolicyStatus

ADMIN_HASH = 'pbkdf2:sha256:1000000$Q8loSbCXnQvZgCXz$ee8b167d28f37981fc8d18f8f7792c2bd4ffe4e620be3c0836b1e76d4967e651'
DEMO_HASH = 'pbkdf2:sha256:1000000$8YEdUiTYWTuy44Ox$d1d9f17b11850a7a615fd449540662dda8c94133767ec3947b91c2eaa4590134'

ADMIN = {
    'username': 'admin',
    'password': ADMIN_HASH
}

USERS = {
    'alex-law@hotmail.com': {'password': DEMO_HASH, 'client_id': 1},
    'mpitsakoupolina@yahoo.gr': {'password': DEMO_HASH, 'client_id': 2},
    'apoTTapo@gmail.com': {'password': DEMO_HASH, 'client_id': 3},
    'DAMIORDOESNTLIVE@hotmail.com': {'password': DEMO_HASH, 'client_id': 4},
    'voula.roukouna@sensorbeta.gr': {'password': DEMO_HASH, 'client_id': 5},
    'papadimitriou.vasilis@gmail.com': {'password': DEMO_HASH, 'client_id': 9},
    'GEORGE_SAXI@hotmail.com': {'password': DEMO_HASH, 'client_id': 10},
    'ioanna.myriokefalitaki@gmail.com': {'password': DEMO_HASH, 'client_id': 11},
    'charis_kouki@yahoo.gr': {'password': DEMO_HASH, 'client_id': 12},
    'apostolopoulos.i@pg.com': {'password': DEMO_HASH, 'client_id': 13},
    'dco@merit.gr': {'password': DEMO_HASH, 'client_id': 14},
    'marivilampou@hotmail.com': {'password': DEMO_HASH, 'client_id': 15},
    'eboulakakis@yahoo.gr': {'password': DEMO_HASH, 'client_id': 16},
    'secretary@sensorbeta.gr': {'password': DEMO_HASH, 'client_id': 17},
    'spanos17@otenet.gr': {'password': DEMO_HASH, 'client_id': 18},
    'mkousoulakou@gmail.com': {'password': DEMO_HASH, 'client_id': 19},
    'gavriilidisioannis1@gmail.com': {'password': DEMO_HASH, 'client_id': 21},
    'asimakopoulouroul@gmail.com': {'password': DEMO_HASH, 'client_id': 22},
    'p.vernardakis@gmail.com': {'password': DEMO_HASH, 'client_id': 23},
    'manosalex73@gmail.com': {'password': DEMO_HASH, 'client_id': 24},
    'info@sroom.gr': {'password': DEMO_HASH, 'client_id': 25},
    'd.doulkeridis@gmail.com': {'password': DEMO_HASH, 'client_id': 26},
    'christ154ian@yahoo.com': {'password': DEMO_HASH, 'client_id': 27},
    'jojoxan@gmail.com': {'password': DEMO_HASH, 'client_id': 29},
    'EIRINIZLN@hotmail.com': {'password': DEMO_HASH, 'client_id': 30},
    'stavroulakormpaki@hotmail.com': {'password': DEMO_HASH, 'client_id': 31},
    'bezerianose@gmail.com': {'password': DEMO_HASH, 'client_id': 32},
    'micsot2@gmail.com': {'password': DEMO_HASH, 'client_id': 33},
    'drnkatsios@hotmail.com': {'password': DEMO_HASH, 'client_id': 34},
    'elentig@hotmail.com': {'password': DEMO_HASH, 'client_id': 35},
    'chourmousis@gmail.com': {'password': DEMO_HASH, 'client_id': 37},
    'mdetsi@gmail.com': {'password': DEMO_HASH, 'client_id': 38},
    'logistirio1922@gmail.com': {'password': DEMO_HASH, 'client_id': 39},
    'anna.xanthopoulou.c@gmail.com': {'password': DEMO_HASH, 'client_id': 40},
    'kostisarvanitis@gmail.com': {'password': DEMO_HASH, 'client_id': 41}
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
    db_session = get_session()
    
    total_clients = db_session.query(Client).count()
    total_policies = db_session.query(Policy).count()
    active_policies = db_session.query(Policy).filter_by(status=PolicyStatus.ACTIVE).count()
    
    pending_payments = db_session.query(Payment).filter_by(status=PaymentStatus.PENDING).count()
    paid_payments = db_session.query(Payment).filter_by(status=PaymentStatus.PAID).count()
    overdue_payments = db_session.query(Payment).filter_by(status=PaymentStatus.OVERDUE).count()
    
    recent_clients = db_session.query(Client).order_by(Client.created_date.desc()).limit(5).all()
    
    db_session.close()
    
    return render_template('admin/dashboard.html',
                         total_clients=total_clients,
                         total_policies=total_policies,
                         active_policies=active_policies,
                         pending_payments=pending_payments,
                         paid_payments=paid_payments,
                         overdue_payments=overdue_payments,
                         recent_clients=recent_clients)

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




if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
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

