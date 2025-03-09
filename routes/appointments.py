from flask import Blueprint, request, jsonify
from config.config import (
    appointments_collection, users_collection, 
    doctor_availability_collection, TIME_SLOTS
)
from utils.priority_utils import analyze_symptoms, get_next_available_slot
from datetime import datetime, timedelta
from bson import ObjectId

appointments_bp = Blueprint('appointments', __name__)

@appointments_bp.route('/appointments/book', methods=['POST'])
def book_appointment():
    try:
        data = request.get_json()
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        # Check if doctor exists
        doctor = users_collection.find_one({
            '_id': ObjectId(data['doctor_id']),
            'role': 'doctor'
        })
        
        if not doctor:
            return jsonify({'error': 'Doctor not found'}), 404

        # Create default slots for today if not exists
        default_slots = [
            '9:00 AM', '9:30 AM', '10:00 AM', '10:30 AM',
            '11:00 AM', '11:30 AM', '12:00 PM', '12:30 PM',
            '2:00 PM', '2:30 PM', '3:00 PM', '3:30 PM',
            '4:00 PM', '4:30 PM', '5:00 PM', '5:30 PM',
            '6:00 PM', '6:30 PM', '7:00 PM', '7:30 PM',
            '8:00 PM', '8:30 PM', '9:00 PM', '9:30 PM',
            '10:00 PM', '10:30 PM', '11:00 PM'
        ]

        # Get or create availability
        availability = doctor_availability_collection.find_one({
            'doctor_id': data['doctor_id'],
            'date': current_date
        })

        if not availability:
            availability = {
                'doctor_id': data['doctor_id'],
                'date': current_date,
                'available_slots': default_slots.copy(),
                'created_at': datetime.utcnow()
            }
            doctor_availability_collection.insert_one(availability)
        
        available_slots = availability.get('available_slots', [])
        if not available_slots:
            available_slots = default_slots.copy()
            doctor_availability_collection.update_one(
                {'_id': availability['_id']},
                {'$set': {'available_slots': available_slots}}
            )

        # Determine priority level based on symptoms
        priority_level = determine_priority_level(data['symptoms'])
        
        # Select time slot based on priority
        if len(available_slots) == 0:
            return jsonify({'error': 'No available slots for today'}), 400
            
        if priority_level == 1:  # Emergency
            appointment_time = available_slots[0]  # First available slot
        elif priority_level == 2:  # Urgent
            slot_index = min(len(available_slots) // 2, len(available_slots) - 1)
            appointment_time = available_slots[slot_index]  # Mid-day slot
        else:  # Routine
            appointment_time = available_slots[-1]  # Last available slot

        # Create appointment
        appointment = {
            'doctor_id': data['doctor_id'],
            'patient_id': data['patient_id'],
            'symptoms': data['symptoms'],
            'status': 'scheduled',
            'appointment_date': current_date,
            'appointment_time': appointment_time,
            'priority_level': priority_level,
            'created_at': datetime.utcnow()
        }

        # Remove booked slot from available slots
        doctor_availability_collection.update_one(
            {'_id': availability['_id']},
            {'$pull': {'available_slots': appointment_time}}
        )

        # Save appointment
        result = appointments_collection.insert_one(appointment)

        return jsonify({
            'message': 'Appointment booked successfully',
            'appointment_id': str(result.inserted_id),
            'appointment_time': appointment_time
        }), 201

    except Exception as e:
        print(f"Error booking appointment: {str(e)}")
        return jsonify({'error': str(e)}), 500

def determine_priority_level(symptoms):
    """Determine appointment priority based on symptoms"""
    symptoms_lower = symptoms.lower()
    
    # Emergency keywords (Priority 1)
    emergency_keywords = [
        'chest pain', 'heart attack', 'stroke', 'severe bleeding',
        'unconscious', 'difficulty breathing', 'severe injury',
        'seizure', 'severe allergic reaction'
    ]
    
    # Urgent keywords (Priority 2)
    urgent_keywords = [
        'fever', 'infection', 'injury', 'pain',
        'vomiting', 'diarrhea', 'sprain', 'cut'
    ]
    
    # Check for emergency conditions
    for keyword in emergency_keywords:
        if keyword in symptoms_lower:
            return 1  # Emergency
    
    # Check for urgent conditions
    for keyword in urgent_keywords:
        if keyword in symptoms_lower:
            return 2  # Urgent
    
    # Default to routine
    return 3  # Routine

@appointments_bp.route('/doctor/availability', methods=['POST'])
def set_doctor_availability():
    data = request.get_json()
    date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    # Delete existing availability for the date
    doctor_availability_collection.delete_one({
        'doctor_id': data['doctor_id'],
        'date': date
    })
    
    # Create new availability with all time slots if doctor is available
    availability = {
        'doctor_id': data['doctor_id'],
        'date': date,
        'is_available': data['is_available'],
        'available_slots': TIME_SLOTS if data['is_available'] else [],  # Using 24-hour format slots from config
        'created_at': datetime.utcnow()
    }
    
    doctor_availability_collection.insert_one(availability)
    
    return jsonify({
        'message': 'Marked as available for today' if data['is_available'] else 'Marked as on leave for today',
        'status': 'available' if data['is_available'] else 'leave'
    })

@appointments_bp.route('/doctor/availability/<doctor_id>', methods=['GET'])
def get_doctor_availability(doctor_id):
    try:
        date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        availability = doctor_availability_collection.find_one({
            'doctor_id': doctor_id,
            'date': date
        })
        
        if not availability:
            return jsonify({
                'is_available': None,  # None means not set yet
                'available_slots': TIME_SLOTS,
                'date': date
            })
        
        return jsonify({
            'is_available': availability.get('is_available', False),
            'available_slots': availability.get('available_slots', []) if availability.get('is_available', False) else [],
            'date': date
        })
    except Exception as e:
        print(f"Error getting doctor availability: {str(e)}")
        return jsonify({'error': str(e)}), 500

@appointments_bp.route('/appointments/doctor/<doctor_id>', methods=['GET'])
def get_doctor_appointments(doctor_id):
    try:
        filter_type = request.args.get('type', 'upcoming')
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        # Base query
        base_query = {
            'doctor_id': doctor_id,
            'type': {'$ne': 'consultation'}  # Exclude consultations
        }
        
        # Add filters based on type
        if filter_type == 'upcoming':
            base_query.update({
                'appointment_date': current_date,
                'status': 'scheduled'
            })
        elif filter_type == 'completed':
            base_query['status'] = 'completed'
        
        # Get appointments
        appointments = appointments_collection.find(base_query).sort([
            ('appointment_time', 1)  # Sort by time ascending
        ])
        
        # Format appointments
        appointment_list = []
        for apt in appointments:
            # Get patient details
            patient = users_collection.find_one({'_id': ObjectId(apt['patient_id'])})
            if patient:
                appointment_list.append({
                    'id': str(apt['_id']),
                    'patient_name': patient['name'],
                    'patient_id': str(patient['_id']),
                    'symptoms': apt['symptoms'],
                    'time': apt.get('appointment_time', ''),
                    'status': apt.get('status', ''),
                    'diagnosis': apt.get('diagnosis', ''),
                    'prescription': apt.get('prescription', ''),
                    'notes': apt.get('notes', '')
                })
        
        return jsonify(appointment_list)
        
    except Exception as e:
        print(f"Error getting doctor appointments: {str(e)}")
        return jsonify({'error': str(e)}), 500

@appointments_bp.route('/appointments/patient/<patient_id>', methods=['GET'])
def get_patient_appointments(patient_id):
    # Get the filter type from query parameters (upcoming/past)
    filter_type = request.args.get('type', 'all')
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    # Base query
    base_query = {'patient_id': patient_id, 'type': {'$ne': 'consultation'}}
    
    # Add date filter based on type
    if filter_type == 'upcoming':
        base_query['appointment_date'] = {'$gte': current_date}
        base_query['status'] = {'$in': ['scheduled', 'pending']}
    elif filter_type == 'past':
        base_query['$or'] = [
            {'appointment_date': {'$lt': current_date}},
            {'status': {'$in': ['completed', 'cancelled', 'no-show']}}
        ]
    
    appointments = appointments_collection.find(base_query).sort([
        ('appointment_date', -1 if filter_type == 'past' else 1),
        ('appointment_time', -1 if filter_type == 'past' else 1)
    ])
    
    appointment_list = []
    for apt in appointments:
        # Get doctor details
        doctor = users_collection.find_one({'_id': ObjectId(apt['doctor_id'])})
        
        appointment_list.append({
            'id': str(apt['_id']),
            'doctor_name': doctor['name'],
            'doctor_specialization': doctor.get('specialization', 'General'),
            'symptoms': apt['symptoms'],
            'date': apt['appointment_date'],
            'time': apt['appointment_time'],
            'status': apt['status'],
            'diagnosis': apt.get('diagnosis', ''),
            'prescription': apt.get('prescription', ''),
            'notes': apt.get('doctor_notes', ''),
            'completed_at': apt.get('completed_at', None)
        })
    
    return jsonify(appointment_list)

@appointments_bp.route('/appointments/<appointment_id>/update', methods=['POST'])
def update_appointment(appointment_id):
    try:
        data = request.get_json()
        current_time = datetime.utcnow()
        
        # Get the current appointment
        appointment = appointments_collection.find_one({'_id': ObjectId(appointment_id)})
        if not appointment:
            return jsonify({'error': 'Appointment not found'}), 404
            
        # Update the appointment
        update_data = {
            'status': 'completed',
            'diagnosis': data['diagnosis'],
            'prescription': data['prescription'],
            'notes': data['notes'],
            'completed_at': current_time,
            'updated_at': current_time
        }
        
        result = appointments_collection.update_one(
            {'_id': ObjectId(appointment_id)},
            {'$set': update_data}
        )
        
        if result.modified_count:
            return jsonify({
                'message': 'Appointment completed successfully',
                'status': 'completed'
            })
        
        return jsonify({'error': 'No changes made to appointment'}), 400
        
    except Exception as e:
        print(f"Error updating appointment: {str(e)}")
        return jsonify({'error': str(e)}), 500

@appointments_bp.route('/appointments/request', methods=['POST'])
def request_appointment():
    data = request.get_json()
    
    # Check if patient already has a pending or scheduled appointment
    existing_appointment = appointments_collection.find_one({
        'patient_id': data['patient_id'],
        'status': {'$in': ['pending', 'scheduled']}
    })
    
    if existing_appointment:
        return jsonify({'error': 'You already have a pending or scheduled appointment'}), 400
    
    # Get doctor's availability
    availability = doctor_availability_collection.find_one({
        'doctor_id': data['doctor_id'],
        'date': datetime.now().strftime('%Y-%m-%d')
    })
    
    if not availability or not availability.get('is_available', False):
        return jsonify({'error': 'Doctor is not available today'}), 400
    
    # Determine priority level based on symptoms
    priority_level = determine_priority_level(data['symptoms'])
    
    # Create appointment request
    appointment = {
        'patient_id': data['patient_id'],
        'doctor_id': data['doctor_id'],
        'symptoms': data['symptoms'],
        'status': 'pending',
        'priority_level': priority_level,  # 1: Emergency, 2: Urgent, 3: Routine
        'requested_at': datetime.utcnow(),
        'type': 'appointment'
    }
    
    result = appointments_collection.insert_one(appointment)
    
    return jsonify({
        'message': 'Appointment request submitted successfully',
        'appointment_id': str(result.inserted_id),
        'priority_level': priority_level
    })

@appointments_bp.route('/appointments/<appointment_id>/respond', methods=['POST'])
def respond_to_appointment(appointment_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        appointment = appointments_collection.find_one({'_id': ObjectId(appointment_id)})
        if not appointment:
            return jsonify({'error': 'Appointment not found'}), 404

        if data['action'] == 'accept':
            # Validate time slot
            if not data.get('appointment_time'):
                return jsonify({'error': 'Appointment time is required'}), 400

            # Update appointment status and time
            result = appointments_collection.update_one(
                {'_id': ObjectId(appointment_id)},
                {
                    '$set': {
                        'status': 'scheduled',
                        'appointment_time': data['appointment_time'],
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count:
                return jsonify({'message': 'Appointment accepted successfully'})
            else:
                return jsonify({'error': 'Failed to update appointment'}), 500

        elif data['action'] == 'reject':
            # Validate rejection reason
            if not data.get('reason'):
                return jsonify({'error': 'Rejection reason is required'}), 400

            # Update appointment status
            result = appointments_collection.update_one(
                {'_id': ObjectId(appointment_id)},
                {
                    '$set': {
                        'status': 'rejected',
                        'rejection_reason': data['reason'],
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count:
                return jsonify({'message': 'Appointment rejected successfully'})
            else:
                return jsonify({'error': 'Failed to update appointment'}), 500

        else:
            return jsonify({'error': 'Invalid action'}), 400

    except Exception as e:
        print(f"Error responding to appointment: {str(e)}")
        return jsonify({'error': str(e)}), 500

@appointments_bp.route('/doctors/available', methods=['GET'])
def get_available_doctors():
    specialization = request.args.get('specialization')
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    # Get IDs of available doctors
    available_doctors = doctor_availability_collection.find({
        'date': current_date,
        'is_available': True
    })
    available_doctor_ids = [ObjectId(doc['doctor_id']) for doc in available_doctors]
    
    # Query for doctors
    query = {
        '_id': {'$in': available_doctor_ids},
        'role': 'doctor'
    }
    if specialization and specialization != 'general':
        query['specialization'] = specialization
    
    doctors = users_collection.find(query, {
        'password': 0,
        'email': 0
    })
    
    doctor_list = []
    for doc in doctors:
        doctor_list.append({
            'id': str(doc['_id']),
            'name': doc['name'],
            'specialization': doc.get('specialization', 'General'),
            'qualification': doc.get('qualification', '')
        })
    
    return jsonify(doctor_list)

@appointments_bp.route('/patient/consultations/<patient_id>', methods=['GET'])
def get_patient_consultations(patient_id):
    """Get all completed consultations for a patient"""
    # Query for both consultation records and completed appointments
    consultations = appointments_collection.find({
        'patient_id': patient_id,
        '$or': [
            {'type': 'consultation'},
            {'type': 'appointment', 'status': 'completed'}
        ]
    }).sort('created_at', -1)  # Sort by creation date
    
    consultation_list = []
    for cons in consultations:
        # Get doctor details
        doctor = users_collection.find_one({'_id': ObjectId(cons['doctor_id'])})
        
        consultation_list.append({
            'id': str(cons['_id']),
            'doctor_name': doctor['name'],
            'doctor_specialization': doctor.get('specialization', 'General'),
            'date': cons.get('consultation_date', cons.get('appointment_date', '')),
            'time': cons.get('consultation_time', cons.get('appointment_time', '')),
            'symptoms': cons['symptoms'],
            'diagnosis': cons.get('diagnosis', ''),
            'prescription': cons.get('prescription', ''),
            'notes': cons.get('notes', cons.get('doctor_notes', '')),
            'created_at': cons.get('created_at', cons.get('completed_at', ''))
        })
    
    return jsonify({'consultations': consultation_list})

@appointments_bp.route('/appointments/pending/<doctor_id>', methods=['GET'])
def get_pending_appointments(doctor_id):
    try:
        # Find all pending appointments for the doctor
        pending = appointments_collection.find({
            'doctor_id': doctor_id,
            'status': 'pending',
            'type': 'appointment'
        }).sort('requested_at', -1)
        
        appointment_list = []
        for apt in pending:
            # Get patient details
            patient = users_collection.find_one({'_id': ObjectId(apt['patient_id'])})
            if patient:
                appointment_list.append({
                    'id': str(apt['_id']),
                    'patient_name': patient['name'],
                    'patient_id': str(patient['_id']),
                    'symptoms': apt.get('symptoms', ''),
                    'priority_level': apt.get('priority_level', 3),
                    'requested_at': apt['requested_at'].strftime('%Y-%m-%d %H:%M') if apt.get('requested_at') else 'Unknown'
                })
        
        return jsonify(appointment_list)
    except Exception as e:
        print(f"Error fetching pending appointments: {str(e)}")
        return jsonify({'error': str(e)}), 500 