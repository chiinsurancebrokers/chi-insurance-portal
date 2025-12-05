#!/usr/bin/env python3
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__, template_folder='app/templates')
app.secret_key = os.getenv('SECRET_KEY', 'chi-insurance-local-secret-2025')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Παρακαλώ συνδεθείτε για να δείτε αυτή τη σελίδα.'

from src.database.models import get_session, Client, Policy, Payment, PaymentStatus

# User accounts - UPDATED with correct IDs
USERS = {
    'alex-law@hotmail.com': {
        'password': generate_password_hash('demo123'),
        'client_id': 1  # ΑΛΕΞΟΠΟΥΛΟΣ ΓΕΩΡΓΙΟΣ
    },
    'mpitsakoupolina@yahoo.gr': {
        'password': generate_password_hash('demo123'),
        'client_id': 2  # ΜΠΙΤΣΑΚΟΥ ΠΟΛΥΤΙΜΗ
    },
    'voula.roukouna@sensorbeta.gr': {
        'password': generate_password_hash('demo123'),
        'client_id': 5  # SENSORBETA
    },
    'papadimitriou.vasilis@gmail.com': {
        'password': generate_password_hash('demo123'),
        'client_id': 9  # ΠΑΠΑΔΗΜΗΤΡΙΟΥ
    },
    'mkousoulakou@gmail.com': {
        'password': generate_password_hash('demo123'),
        'client_id': 19  # ΚΟΥΣΟΥΛΑΚΟΥ
    }
}

class User(UserMixin):
    def __init__(self, email, client_id):
        self.id = email
        self.email = email
        self.client_id = client_id

@login_manager.user_loader
def load_user(email):
    if email in USERS:
        return User(email, USERS[email]['client_id'])
    return None

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if email in USERS and check_password_hash(USERS[email]['password'], password):
            user = User(email, USERS[email]['client_id'])
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Λάθος email ή κωδικός', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
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
    seen_payments = set()  # Track duplicates
    
    for policy in policies:
        payment = db_session.query(Payment).filter_by(
            policy_id=policy.id,
            status=PaymentStatus.PENDING
        ).first()
        
        if payment:
            # Create unique key to avoid duplicates
            payment_key = (policy.license_plate, payment.due_date, payment.amount)
            
            if payment_key not in seen_payments:
                seen_payments.add(payment_key)
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

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
