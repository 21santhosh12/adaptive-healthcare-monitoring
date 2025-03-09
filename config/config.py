from pymongo import MongoClient
import os

# MongoDB Atlas connection string
MONGO_URI = "mongodb+srv://santhosh:2002Sk@parkingtokensystem.o4l8l.mongodb.net/?retryWrites=true&w=majority&appName=ParkingTokenSystem"

# Initialize MongoDB client
client = MongoClient(MONGO_URI)

# Initialize database
db = client.healthcare_monitoring

# Define collections
users_collection = db.users
health_records_collection = db.health_records
appointments_collection = db.appointments
doctor_availability_collection = db.doctor_availability  # New collection

# Database configuration
DATABASE_CONFIG = {
    'MONGO_URI': MONGO_URI,
    'DATABASE_NAME': 'healthcare_monitoring',
    'COLLECTIONS': {
        'users': 'users',
        'health_records': 'health_records',
        'appointments': 'appointments',
        'doctor_availability': 'doctor_availability'
    }
}

# Priority levels for different conditions
PRIORITY_LEVELS = {
    'emergency': 1,  # Highest priority
    'urgent': 2,
    'routine': 3,    # Lowest priority
}

# Emergency keywords for AI prioritization
EMERGENCY_KEYWORDS = [
    'accident', 'bleeding', 'chest pain', 'heart attack', 'stroke',
    'unconscious', 'severe', 'critical', 'emergency', 'trauma'
]

URGENT_KEYWORDS = [
    'fracture', 'fever', 'infection', 'pain', 'injury',
    'vomiting', 'dizziness', 'moderate', 'urgent'
]

# Time slots in 24-hour format
TIME_SLOTS = [
    '09:00', '09:30', '10:00', '10:30', '11:00', '11:30',
    '12:00', '12:30', '14:00', '14:30', '15:00', '15:30',
    '16:00', '16:30', '17:00', '17:30', '18:00', '18:30',
    '19:00', '19:30', '20:00', '20:30', '21:00'
]

# Default appointment duration in minutes
DEFAULT_APPOINTMENT_DURATION = 30 