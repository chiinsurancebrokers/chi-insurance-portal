from flask import Flask, request, jsonify
from flask_cors import CORS
import jwt
from datetime import datetime
from database import get_session, Client, Policy, Payment, PaymentStatus
import os

app = Flask(__name__)
CORS(app)

SECRET_KEY = os.getenv('JWT_SECRET', 'chi-insurance-secret-2025')

def verify_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except:
        return None

@app.route('/api/dashboard/stats', methods=['GET'])
def get_stats():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = verify_token(token)
    
    if not payload:
        return jsonify({'error': 'Unauthorized'}), 401
    
    session = get_session()
    client = session.query(Client).get(payload['client_id'])
    
    if not client:
        return jsonify({'error': 'Client not found'}), 404
    
    policies = session.query(Policy).filter_by(client_id=client.id).all()
    
    total_policies = len(policies)
    active_policies = sum(1 for p in policies if p.status.value == 'ACTIVE')
    
    # Pending payments
    pending_payments = []
    for policy in policies:
        payment = session.query(Payment).filter_by(
            policy_id=policy.id,
            status=PaymentStatus.PENDING
        ).first()
        
        if payment:
            days_until = (payment.due_date - datetime.now().date()).days
            pending_payments.append({
                'id': payment.id,
                'policy_type': policy.policy_type,
                'provider': policy.provider,
                'license_plate': policy.license_plate,
                'amount': float(payment.amount),
                'due_date': payment.due_date.strftime('%d/%m/%Y'),
                'days_until': days_until
            })
    
    pending_payments.sort(key=lambda x: x['days_until'])
    
    session.close()
    
    return jsonify({
        'client': {
            'name': client.name,
            'email': client.email
        },
        'stats': {
            'total_policies': total_policies,
            'active_policies': active_policies,
            'pending_payments': len(pending_payments)
        },
        'pending_payments': pending_payments[:5]
    })

@app.route('/api/dashboard/policies', methods=['GET'])
def get_policies():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = verify_token(token)
    
    if not payload:
        return jsonify({'error': 'Unauthorized'}), 401
    
    session = get_session()
    policies = session.query(Policy).filter_by(client_id=payload['client_id']).all()
    
    result = []
    for policy in policies:
        result.append({
            'id': policy.id,
            'policy_type': policy.policy_type,
            'provider': policy.provider,
            'license_plate': policy.license_plate,
            'premium': float(policy.premium) if policy.premium else None,
            'expiration_date': policy.expiration_date.strftime('%d/%m/%Y') if policy.expiration_date else None,
            'status': policy.status.value
        })
    
    session.close()
    return jsonify({'policies': result})

if __name__ == '__main__':
    app.run()
