from flask import Flask, render_template, redirect, url_for, session, jsonify
from routes.auth import auth_bp
from routes.appointments import appointments_bp
from routes.recommendations import recommendations_bp
from config.config import DATABASE_CONFIG, users_collection
from bson import ObjectId
import os
import signal
import sys

app = Flask(__name__)

def signal_handler(sig, frame):
    print('Shutting down gracefully...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Configure Flask app
app.config['SECRET_KEY'] = os.urandom(24)
app.config['MONGO_URI'] = DATABASE_CONFIG['MONGO_URI']
app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 minutes session lifetime

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(appointments_bp)
app.register_blueprint(recommendations_bp)

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/verify-session')
def verify_session():
    if 'user_id' not in session:
        return jsonify({'valid': False})
    
    # Check if user still exists in database
    user = users_collection.find_one({'_id': ObjectId(session['user_id'])})
    if not user:
        session.clear()
        return jsonify({'valid': False})
    
    return jsonify({'valid': True})

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # Get user details
    user = users_collection.find_one({'_id': ObjectId(session['user_id'])})
    if not user:
        session.clear()
        return redirect(url_for('index'))
    
    # Redirect to appropriate dashboard based on role
    if user['role'] == 'doctor':
        return render_template('doctor_dashboard.html', user=user)
    else:
        return render_template('patient_dashboard.html', user=user)

@app.route('/doctor/dashboard')
def doctor_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # Get user details
    user = users_collection.find_one({'_id': ObjectId(session['user_id'])})
    if not user:
        session.clear()
        return redirect(url_for('index'))
    
    if user['role'] != 'doctor':
        return redirect(url_for('index'))
    
    print(f"Doctor ID: {user['_id']}")  # Debug log
    return render_template('doctor_dashboard.html', user=user)

if __name__ == '__main__':
    try:
        # Use a different port and add host parameter
        app.run(host='127.0.0.1', port=5001, debug=True, use_reloader=False)
    except OSError as e:
        print(f"Error starting server: {e}")
        print("Try using a different port or restart your computer if the issue persists.")