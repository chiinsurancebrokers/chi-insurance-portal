"""
CHI Insurance Portal — REST API Blueprint
Add to chi-insurance-portal Railway repo as chi_api_routes.py
Register in app.py with: from chi_api_routes import api_bp; app.register_blueprint(api_bp)

Endpoints:
  GET  /api/clients              → list all clients
  GET  /api/clients/<id>         → client + policies + payments
  GET  /api/policies             → all active policies
  GET  /api/policies/expiring    → expiring within ?days=30
  GET  /api/renewals             → renewal queue
  POST /api/client/<id>/portal   → trigger portal generation
  GET  /api/stats                → dashboard stats

Protected by X-API-Key header (set CHI_API_KEY env var on Railway).
"""

from flask import Blueprint, jsonify, request, current_app
import os
from datetime import datetime, date, timedelta
from functools import wraps

api_bp = Blueprint("api", __name__, url_prefix="/api")

# ── AUTH ──────────────────────────────────────────────────────────────────────
def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get("X-API-Key") or request.args.get("api_key","")
        expected = os.environ.get("CHI_API_KEY","")
        if not expected:
            return jsonify({"error": "CHI_API_KEY not configured on server"}), 500
        if key != expected:
            return jsonify({"error": "Invalid API key"}), 401
        return f(*args, **kwargs)
    return decorated

# ── HELPERS ───────────────────────────────────────────────────────────────────
def _policy_to_dict(p) -> dict:
    """Convert a Policy model instance to dict. Adapt field names to your model."""
    return {
        "id":           getattr(p,"id",None),
        "client_id":    getattr(p,"client_id",None),
        "type":         getattr(p,"policy_type", getattr(p,"type","")),
        "insurer":      getattr(p,"insurer", getattr(p,"insurance_company","")),
        "policy_number":getattr(p,"policy_number", getattr(p,"policy_no","")),
        "product":      getattr(p,"product", getattr(p,"product_name","")),
        "premium":      str(getattr(p,"premium", getattr(p,"premium_amount",""))),
        "currency":     getattr(p,"currency","EUR"),
        "expiry_date":  str(getattr(p,"expiry_date", getattr(p,"expiry",""))),
        "status":       getattr(p,"status","active"),
        "vehicle_plate":getattr(p,"license_plate", getattr(p,"vehicle_plate","")),
        "notes":        getattr(p,"notes",""),
    }

def _payment_to_dict(p) -> dict:
    return {
        "id":          getattr(p,"id",None),
        "date":        str(getattr(p,"payment_date", getattr(p,"date",""))),
        "amount":      str(getattr(p,"amount","")),
        "currency":    getattr(p,"currency","EUR"),
        "method":      getattr(p,"payment_method", getattr(p,"method","")),
        "status":      getattr(p,"status",""),
        "description": getattr(p,"description", getattr(p,"notes","")),
    }

def _client_to_dict(c, include_policies=False, include_payments=False) -> dict:
    d = {
        "id":    getattr(c,"id",None),
        "name":  getattr(c,"name", getattr(c,"client_name","")),
        "email": getattr(c,"email",""),
        "phone": getattr(c,"phone",""),
        "notes": getattr(c,"notes",""),
    }
    if include_policies:
        try:
            d["policies"] = [_policy_to_dict(p) for p in (c.policies or [])]
        except: d["policies"] = []
    if include_payments:
        try:
            d["payments"] = [_payment_to_dict(p) for p in (c.payments or [])]
        except: d["payments"] = []
    return d

def _get_db_models():
    """Import models — adapt to your actual model names."""
    try:
        # Try common import patterns for Flask apps
        from models import Client, Policy, Payment
        return Client, Policy, Payment
    except ImportError:
        try:
            from app import Client, Policy, Payment
            return Client, Policy, Payment
        except ImportError:
            try:
                from database import Client, Policy, Payment
                return Client, Policy, Payment
            except ImportError:
                return None, None, None

def _get_db():
    """Get db session — adapt to your app."""
    try:
        from models import db; return db
    except: pass
    try:
        from app import db; return db
    except: pass
    try:
        from database import db; return db
    except: return None

# ── ENDPOINTS ─────────────────────────────────────────────────────────────────
@api_bp.route("/health")
def health():
    return jsonify({"status":"ok","timestamp":datetime.now().isoformat()})

@api_bp.route("/stats")
@require_api_key
def stats():
    """Dashboard statistics."""
    Client, Policy, Payment = _get_db_models()
    if not Client:
        return jsonify({"error":"Models not found — check chi_api_routes.py import"}), 500
    try:
        today = date.today()
        in_30 = today + timedelta(days=30)
        in_90 = today + timedelta(days=90)
        total_clients  = Client.query.count()
        total_policies = Policy.query.count() if Policy else 0
        expiring_30    = Policy.query.filter(Policy.expiry_date <= in_30, Policy.expiry_date >= today).count() if Policy else 0
        expiring_90    = Policy.query.filter(Policy.expiry_date <= in_90, Policy.expiry_date >= today).count() if Policy else 0
        return jsonify({
            "total_clients":  total_clients,
            "total_policies": total_policies,
            "expiring_30_days": expiring_30,
            "expiring_90_days": expiring_90,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route("/clients")
@require_api_key
def clients():
    """List all clients."""
    Client, Policy, Payment = _get_db_models()
    if not Client: return jsonify({"error":"Models not found"}), 500
    try:
        search = request.args.get("search","").lower()
        q = Client.query
        if search:
            q = q.filter(Client.name.ilike(f"%{search}%"))
        all_clients = q.order_by(Client.name).all()
        return jsonify([_client_to_dict(c) for c in all_clients])
    except Exception as e:
        return jsonify({"error":str(e)}), 500

@api_bp.route("/clients/<int:client_id>")
@require_api_key
def client_detail(client_id):
    """Client detail with policies and payments."""
    Client, Policy, Payment = _get_db_models()
    if not Client: return jsonify({"error":"Models not found"}), 500
    try:
        c = Client.query.get_or_404(client_id)
        return jsonify(_client_to_dict(c, include_policies=True, include_payments=True))
    except Exception as e:
        return jsonify({"error":str(e)}), 500

@api_bp.route("/policies")
@require_api_key
def policies():
    """All active policies."""
    Client, Policy, Payment = _get_db_models()
    if not Policy: return jsonify({"error":"Models not found"}), 500
    try:
        insurer = request.args.get("insurer")
        ptype   = request.args.get("type")
        q = Policy.query
        if insurer: q = q.filter(Policy.insurer.ilike(f"%{insurer}%"))
        if ptype:   q = q.filter(Policy.policy_type == ptype)
        return jsonify([_policy_to_dict(p) for p in q.all()])
    except Exception as e:
        return jsonify({"error":str(e)}), 500

@api_bp.route("/policies/expiring")
@require_api_key
def expiring():
    """Policies expiring within ?days=N (default 30)."""
    Client, Policy, Payment = _get_db_models()
    if not Policy: return jsonify({"error":"Models not found"}), 500
    try:
        days   = int(request.args.get("days",30))
        today  = date.today()
        cutoff = today + timedelta(days=days)
        q = Policy.query.filter(
            Policy.expiry_date >= today,
            Policy.expiry_date <= cutoff
        ).order_by(Policy.expiry_date)
        result = []
        for p in q.all():
            d = _policy_to_dict(p)
            try:
                c = Client.query.get(p.client_id)
                d["client_name"] = getattr(c,"name","") if c else ""
                d["client_email"]= getattr(c,"email","") if c else ""
                d["client_phone"]= getattr(c,"phone","") if c else ""
            except: pass
            d["days_left"] = (p.expiry_date - today).days if p.expiry_date else None
            result.append(d)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error":str(e)}), 500

@api_bp.route("/renewals")
@require_api_key
def renewals():
    """Renewal queue grouped by urgency."""
    Client, Policy, Payment = _get_db_models()
    if not Policy: return jsonify({"error":"Models not found"}), 500
    try:
        today  = date.today()
        cutoff = today + timedelta(days=90)
        q = Policy.query.filter(
            Policy.expiry_date >= today,
            Policy.expiry_date <= cutoff
        ).order_by(Policy.expiry_date)
        urgent, soon, upcoming = [], [], []
        for p in q.all():
            d = _policy_to_dict(p)
            try:
                c = Client.query.get(p.client_id)
                d["client_name"] = getattr(c,"name","") if c else ""
            except: pass
            days = (p.expiry_date - today).days if p.expiry_date else 999
            d["days_left"] = days
            if days <= 7:    urgent.append(d)
            elif days <= 30: soon.append(d)
            else:            upcoming.append(d)
        return jsonify({"urgent":urgent,"soon":soon,"upcoming":upcoming,
                        "total": len(urgent)+len(soon)+len(upcoming)})
    except Exception as e:
        return jsonify({"error":str(e)}), 500
