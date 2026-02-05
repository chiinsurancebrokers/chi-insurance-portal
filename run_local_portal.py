#!/usr/bin/env python3
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps
import os

# ===============================
# LIFE / HEALTH PAYMENT RULES
# ===============================

LIFE_KEYWORDS = (
    "life", "health", "medical", "ipmi",
    "υγε", "υγεια", "ζω", "ζωης", "ιατρ"
)

LIFE_PAYMENT_DISCLAIMER_GR_HTML = """
<div style="border:1px solid #f0ad4e;padding:12px;border-radius:8px;
            background:#fff7e6;margin:12px 0;font-size:13px;">
  <strong>Σημαντική ενημέρωση (Συμβόλαια Ζωής / Υγείας):</strong><br>
  Για τα συμβόλαια Ζωής ή Υγείας, η πληρωμή πραγματοποιείται
  <strong>απευθείας προς την ασφαλιστική εταιρεία ή τον πάροχο</strong>.<br><br>
  Παρακαλούμε εξοφλήστε
  <strong>με τον τρόπο που ακολουθείτε έως σήμερα</strong>
  (π.χ. πάγια εντολή, κάρτα, RF),
  ή επικοινωνήστε με την ασφαλιστική εταιρεία σας για
  τα <strong>ορθά στοιχεία πληρωμής</strong>.
</div>
"""

NON_LIFE_BANK_ACCOUNTS_HTML = """
<table style="width:100%;border-collapse:collapse;font-size:13px;">
<tr style="background:#f5f5f5;">
  <td style="padding:8px;border:1px solid #ddd;"><strong>ALPHA BANK</strong></td>
  <td style="padding:8px;border:1px solid #ddd;">GR4801401340134002320003540</td>
</tr>
<tr>
  <td style="padding:8px;border:1px solid #ddd;"><strong>ΕΘΝΙΚΗ ΤΡΑΠΕΖΑ</strong></td>
  <td style="padding:8px;border:1px solid #ddd;">GR3901108910000089147029808</td>
</tr>
<tr style="background:#f5f5f5;">
  <td style="padding:8px;border:1px solid #ddd;"><strong>EUROBANK</strong></td>
  <td style="padding:8px;border:1px solid #ddd;">GR3302602210000370200676490</td>
</tr>
<tr>
  <td style="padding:8px;border:1px solid #ddd;"><strong>ΠΕΙΡΑΙΩΣ</strong></td>
  <td style="padding:8px;border:1px solid #ddd;">GR6201720890005089072164520</td>
</tr>
</table>
"""

def _is_life_health_text(text: str) -> bool:
    text = (text or "").lower()
    return any(k in text for k in LIFE_KEYWORDS)

def is_life_health_renewal(obj) -> bool:
    fields = (
        "line_of_business", "lob", "category",
        "policy_type", "product", "plan_name",
        "plan", "provider", "insurer", "notes", "type"
    )
    if isinstance(obj, dict):
        blob = " ".join(str(obj.get(f, "") or "") for f in fields)
    else:
        blob = " ".join(str(getattr(obj, f, "") or "") for f in fields)
    return _is_life_health_text(blob)

# ===============================
# APP INIT
# ===============================

app = Flask(__name__, template_folder='app/templates')
app.secret_key = os.getenv('SECRET_KEY', 'chi-insurance-local-secret-2025')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

from src.database.models import (
    get_session, Client, Policy, Payment,
    PaymentStatus, PolicyStatus,
    EmailQueue, EmailStatus
)
