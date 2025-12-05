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

# FIXED: Correct client IDs
# User accounts - All clients with demo123 password
USERS = {
    'alex-law@hotmail.com': {
        'password': generate_password_hash('demo123'),
        'client_id': 1  # ΑΛΕΞΟΠΟΥΛΟΣ ΓΕΩΡΓΙΟΣ
    },
    'mpitsakoupolina@yahoo.gr': {
        'password': generate_password_hash('demo123'),
        'client_id': 2  # ΜΠΙΤΣΑΚΟΥ ΠΟΛΥΤΙΜΗ ΠΑΝΑΓΙ
    },
    'apoTTapo@gmail.com': {
        'password': generate_password_hash('demo123'),
        'client_id': 3  # ΑΠΟΣΤΟΛΟΥ ΚΩΝ/ΝΟΣ
    },
    'DAMIORDOESNTLIVE@hotmail.com': {
        'password': generate_password_hash('demo123'),
        'client_id': 4  # ΜΑΜΜΗ ΕΙΡΗΝΗ
    },
    'voula.roukouna@sensorbeta.gr': {
        'password': generate_password_hash('demo123'),
        'client_id': 5  # Client_voula.roukouna
    },
    'papadimitriou.vasilis@gmail.com': {
        'password': generate_password_hash('demo123'),
        'client_id': 9  # ΠΑΠΑΔΗΜΗΤΡΙΟΥ ΒΑΣΙΛΕΙΟΣ
    },
    'GEORGE_SAXI@hotmail.com': {
        'password': generate_password_hash('demo123'),
        'client_id': 10  # ΣΑΧΙΝΟΓΛΟΥ ΓΕΩΡΓΙΟΣ
    },
    'ioanna.myriokefalitaki@gmail.com': {
        'password': generate_password_hash('demo123'),
        'client_id': 11  # ΜΥΡΙΟΚΕΦΑΛΙΤΑΚΗ ΙΩΑΝΝΑ
    },
    'charis_kouki@yahoo.gr': {
        'password': generate_password_hash('demo123'),
        'client_id': 12  # ΚΟΥΚΗ ΧΑΡΙΚΛΕΙΑ
    },
    'apostolopoulos.i@pg.com': {
        'password': generate_password_hash('demo123'),
        'client_id': 13  # ΑΠΟΣΤΟΛΟΠΟΥΛΟΣ ΙΩΑΝΝΗΣ
    },
    'dco@merit.gr': {
        'password': generate_password_hash('demo123'),
        'client_id': 14  # ΟΥΤΟΠΟΥΛΟΣ ΔΗΜΗΤΡΙΟΣ
    },
    'marivilampou@hotmail.com': {
        'password': generate_password_hash('demo123'),
        'client_id': 15  # ΛΑΜΠΟΥ ΜΑΡΙΑ - ΠΑΡΑΣΚΕΥΗ
    },
    'eboulakakis@yahoo.gr': {
        'password': generate_password_hash('demo123'),
        'client_id': 16  # ΜΠΟΥΛΑΚΑΚΗΣ ΕΛΠΙΔΟΦΟΡΟΣ
    },
    'secretary@sensorbeta.gr': {
        'password': generate_password_hash('demo123'),
        'client_id': 17  # SENSORBETA-ΑΝΤΙΚΛΕΠΤΙΚΑ ΣΥΣΤΗΜΑΤΑ ΑΕ
    },
    'spanos17@otenet.gr': {
        'password': generate_password_hash('demo123'),
        'client_id': 18  # ΣΠΑΝΟΣ ΘΕΟΔΩΡΟΣ
    },
    'mkousoulakou@gmail.com': {
        'password': generate_password_hash('demo123'),
        'client_id': 19  # ΚΟΥΣΟΥΛΑΚΟΥ ΜΑΡΙΑ
    },
    'gavriilidisioannis1@gmail.com': {
        'password': generate_password_hash('demo123'),
        'client_id': 21  # ΓΑΒΡΙΗΛΙΔΗΣ ΙΩΑΝΝΗΣ
    },
    'asimakopoulouroul@gmail.com': {
        'password': generate_password_hash('demo123'),
        'client_id': 22  # ΑΣΗΜΑΚΟΠΟΥΛΟΥ ΣΤΑΥΡΟΥΛΑ
    },
    'p.vernardakis@gmail.com': {
        'password': generate_password_hash('demo123'),
        'client_id': 23  # ΒΕΡΝΑΡΔΑΚΗΣ ΠΑΝΑΓΙΩΤΗΣ
    },
    'manosalex73@gmail.com': {
        'password': generate_password_hash('demo123'),
        'client_id': 24  # ΑΛΕΞΑΝΔΡΗΣ ΕΜΜΑΝΟΥΗΛ
    },
    'info@sroom.gr': {
        'password': generate_password_hash('demo123'),
        'client_id': 25  # ΜΠΑΛΑΓΙΑΝΝΗ ΧΡΥΣΑΝΘΗ
    },
    'd.doulkeridis@gmail.com': {
        'password': generate_password_hash('demo123'),
        'client_id': 26  # ΔΟΥΛΚΕΡΙΔΗΣ ΔΗΜΗΤΡΙΟΣ
    },
    'christ154ian@yahoo.com': {
        'password': generate_password_hash('demo123'),
        'client_id': 27  # ΓΕΩΡΓΙΑΔΗΣ ΧΡΗΣΤΟΣ
    },
    'jojoxan@gmail.com': {
        'password': generate_password_hash('demo123'),
        'client_id': 29  # ΝΙΚΟΛΑΡΑΣ ΝΙΚΟΛΑΟΣ
    },
    'EIRINIZLN@hotmail.com': {
        'password': generate_password_hash('demo123'),
        'client_id': 30  # ΖΑΛΩΝΗ ΕΙΡΗΝΗ
    },
    'stavroulakormpaki@hotmail.com': {
        'password': generate_password_hash('demo123'),
        'client_id': 31  # ΚΑΜΠΕΤΣΟΣ ΣΤΥΛΙΑΝΟΣ
    },
    'bezerianose@gmail.com': {
        'password': generate_password_hash('demo123'),
        'client_id': 32  # ΜΠΕΖΕΡΙΑΝΟΣ ΕΥΑΓΓΕΛΟΣ
    },
    'micsot2@gmail.com': {
        'password': generate_password_hash('demo123'),
        'client_id': 33  # ΣΩΤΗΡΙΟΥ ΝΙΚΟΛΑΟΣ
    },
    'drnkatsios@hotmail.com': {
        'password': generate_password_hash('demo123'),
        'client_id': 34  # ΚΑΤΣΙΟΣ ΝΙΚΟΛΑΟΣ
    },
    'elentig@hotmail.com': {
        'password': generate_password_hash('demo123'),
        'client_id': 35  # ΤΗΓΑΝΗ ΕΛΕΝΗ
    },
    'chourmousis@gmail.com': {
        'password': generate_password_hash('demo123'),
        'client_id': 37  # ΧΟΥΡΜΟΥΣΗΣ ΔΗΜΗΤΡΙΟΣ
    },
    'mdetsi@gmail.com': {
        'password': generate_password_hash('demo123'),
        'client_id': 38  # ΔΕΤΣΗ ΜΑΡΙΑ-ΕΛΕΝΗ
    },
    'logistirio1922@gmail.com': {
        'password': generate_password_hash('demo123'),
        'client_id': 39  # ALTO ΕΠΙΧΕΙΡΗΜΑΤΙΚΕΣ ΛΥΣΕΙΣ ΤΡΟΦΟΔΟΣΙΑΣ
    },
    'anna.xanthopoulou.c@gmail.com': {
        'password': generate_password_hash('demo123'),
        'client_id': 40  # ΞΑΝΘΟΠΟΥΛΟΥ ΑΝΝΑ
    },
    'kostisarvanitis@gmail.com': {
        'password': generate_password_hash('demo123'),
        'client_id': 41  # ΑΡΒΑΝΙΤΗΣ ΚΩΝΣΤΑΝΤΙΝΟΣ
    }
}
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

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
