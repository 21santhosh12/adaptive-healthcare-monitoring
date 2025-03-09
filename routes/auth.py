from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from config.config import users_collection, doctor_availability_collection
from utils.email_utils import generate_otp, send_admin_notification
from datetime import datetime, timedelta
from bson import ObjectId

auth_bp = Blueprint('auth', __name__)

# Store pending registrations with OTPs
pending_registrations = {}

@auth_bp.route('/signup/initiate', methods=['POST'])
def initiate_signup():
    data = request.get_json()
    
    # Check if user already exists
    if users_collection.find_one({'email': data['email']}):
        return jsonify({'error': 'Email already exists'}), 400
    
    # Generate OTP
    otp = generate_otp()
    
    # Store registration data temporarily with OTP
    pending_registrations[data['email']] = {
        'data': data,
        'otp': otp,
        'timestamp': datetime.utcnow()
    }
    
    # Send OTP to admin
    if send_admin_notification(data, otp):
        return jsonify({
            'message': 'Registration initiated. Please contact admin for OTP verification.',
            'email': data['email']
        })
    
    return jsonify({'error': 'Failed to send OTP notification'}), 500

@auth_bp.route('/signup/verify', methods=['POST'])
def verify_signup():
    data = request.get_json()
    email = data['email']
    submitted_otp = data['otp']
    
    # Check if registration is pending
    if email not in pending_registrations:
        return jsonify({'error': 'No pending registration found'}), 400
    
    registration = pending_registrations[email]
    
    # Check if OTP has expired (30 minutes validity)
    if datetime.utcnow() - registration['timestamp'] > timedelta(minutes=30):
        del pending_registrations[email]
        return jsonify({'error': 'OTP has expired. Please register again'}), 400
    
    # Verify OTP
    if submitted_otp != registration['otp']:
        return jsonify({'error': 'Invalid OTP'}), 400
    
    # Create new user
    user_data = registration['data']
    user = {
        'email': user_data['email'],
        'password': generate_password_hash(user_data['password']),
        'role': user_data['role'],
        'name': user_data['name'],
        'created_at': datetime.utcnow()
    }
    
    # Add doctor-specific fields if role is doctor
    if user_data['role'] == 'doctor':
        user.update({
            'qualification': user_data.get('qualification', ''),
            'specialization': user_data.get('specialization', 'general'),
            'experience': user_data.get('experience', 0)
        })
    
    users_collection.insert_one(user)
    
    # Clean up pending registration
    del pending_registrations[email]
    
    return jsonify({'message': 'User created successfully'}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = users_collection.find_one({'email': data['email']})
    
    if user and check_password_hash(user['password'], data['password']):
        session['user_id'] = str(user['_id'])
        
        # If user is a doctor, check if they've set their availability for today
        if user['role'] == 'doctor':
            current_date = datetime.now().strftime('%Y-%m-%d')
            availability = doctor_availability_collection.find_one({
                'doctor_id': str(user['_id']),
                'date': current_date
            })
            
            return jsonify({
                'message': 'Login successful',
                'user': {
                    'id': str(user['_id']),
                    'email': user['email'],
                    'role': user['role'],
                    'name': user['name'],
                    'needs_availability_check': not bool(availability)
                }
            })
        
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': str(user['_id']),
                'email': user['email'],
                'role': user['role'],
                'name': user['name']
            }
        })
    
    return jsonify({'error': 'Invalid credentials'}), 401

@auth_bp.route('/logout')
def logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'})

@auth_bp.route('/doctor/availability/status', methods=['POST'])
def set_doctor_status():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.get_json()
    is_available = data.get('is_available', False)
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    # Delete any existing availability for today
    doctor_availability_collection.delete_one({
        'doctor_id': session['user_id'],
        'date': current_date
    })
    
    if is_available:
        # Create new availability with default time slots
        availability = {
            'doctor_id': session['user_id'],
            'date': current_date,
            'is_available': True,
            'created_at': datetime.utcnow()
        }
        doctor_availability_collection.insert_one(availability)
        return jsonify({'message': 'Marked as available for today'})
    
    return jsonify({'message': 'Marked as unavailable for today'}) 