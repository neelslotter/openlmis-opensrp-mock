"""
OpenLMIS OAuth2 Authentication Mock Routes
"""
import uuid
import json
import os
from flask import Blueprint, request, jsonify

openlmis_auth = Blueprint('openlmis_auth', __name__)

# Load user data
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

def load_users():
    with open(os.path.join(DATA_DIR, 'users.json'), 'r') as f:
        return json.load(f)['users']

# In-memory token store (for mock purposes)
tokens = {}


@openlmis_auth.route('/api/oauth/token', methods=['POST'])
def get_token():
    """
    OAuth2 token endpoint.
    Accepts username/password and returns access token.
    """
    username = request.form.get('username') or request.json.get('username') if request.is_json else request.form.get('username')
    password = request.form.get('password') or request.json.get('password') if request.is_json else request.form.get('password')
    
    users = load_users()
    user = next((u for u in users if u['username'] == username and u['password'] == password), None)
    
    if not user:
        return jsonify({
            'error': 'invalid_grant',
            'error_description': 'Bad credentials'
        }), 401
    
    # Generate mock token
    access_token = str(uuid.uuid4())
    refresh_token = str(uuid.uuid4())
    
    tokens[access_token] = {
        'user_id': user['id'],
        'username': user['username'],
        'role': user['role']
    }
    
    return jsonify({
        'access_token': access_token,
        'token_type': 'bearer',
        'expires_in': 3600,
        'refresh_token': refresh_token,
        'referenceDataUserId': user['id']
    })


@openlmis_auth.route('/api/oauth/check_token', methods=['POST'])
def check_token():
    """Validate a token."""
    token = request.form.get('token') or (request.json.get('token') if request.is_json else None)
    
    if token in tokens:
        token_info = tokens[token]
        return jsonify({
            'user_name': token_info['username'],
            'referenceDataUserId': token_info['user_id'],
            'authorities': [token_info['role']]
        })
    
    return jsonify({'error': 'invalid_token'}), 401


@openlmis_auth.route('/api/users', methods=['GET'])
def list_users():
    """List all users."""
    users = load_users()
    # Remove passwords from response
    safe_users = [{k: v for k, v in u.items() if k != 'password'} for u in users]
    return jsonify(safe_users)


@openlmis_auth.route('/api/users/<user_id>', methods=['GET'])
def get_user(user_id):
    """Get a specific user by ID."""
    users = load_users()
    user = next((u for u in users if u['id'] == user_id), None)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Remove password from response
    safe_user = {k: v for k, v in user.items() if k != 'password'}
    return jsonify(safe_user)


def get_token_user(auth_header):
    """Helper to get user from Authorization header."""
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    token = auth_header.split(' ')[1]
    return tokens.get(token)
