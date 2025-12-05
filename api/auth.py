from flask import Flask, request, jsonify
from flask_cors import CORS
import jwt
import bcrypt
from datetime import datetime, timedelta
from database import get_session, User
import os

app = Flask(__name__)
CORS(app)

SECRET_KEY = os.getenv('JWT_SECRET', 'chi-insurance-secret-2025')

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email και κωδικός απαιτούνται'}), 400
    
    session = get_session()
    user = session.query(User).filter_by(email=email).first()
    
    if not user:
        return jsonify({'error': 'Λάθος email ή κωδικός'}), 401
    
    # Check password
    if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
        return jsonify({'error': 'Λάθος email ή κωδικός'}), 401
    
    # Update last login
    user.last_login = datetime.now()
    session.commit()
    
    # Generate JWT token
    token = jwt.encode({
        'user_id': user.id,
        'client_id': user.client_id,
        'exp': datetime.utcnow() + timedelta(days=7)
    }, SECRET_KEY, algorithm='HS256')
    
    session.close()
    
    return jsonify({
        'token': token,
        'user': {
            'id': user.id,
            'email': user.email,
            'client_id': user.client_id
        }
    })

@app.route('/api/auth/verify', methods=['GET'])
def verify():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        return jsonify({'error': 'Token required'}), 401
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return jsonify({'valid': True, 'user_id': payload['user_id']})
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401

if __name__ == '__main__':
    app.run()
