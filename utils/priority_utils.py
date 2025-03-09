from config.config import (PRIORITY_LEVELS, EMERGENCY_KEYWORDS, 
    URGENT_KEYWORDS, TIME_SLOTS)
import re

def analyze_symptoms(symptoms_text):
    """
    Analyze symptoms text to determine appointment priority using a scoring system
    Returns: priority_level (1: Emergency, 2: Urgent, 3: Routine)
    """
    # Convert to lowercase for case-insensitive matching
    text = symptoms_text.lower()
    
    # Initialize score (higher score means higher priority)
    priority_score = 0
    
    # Emergency conditions (immediate medical attention needed)
    emergency_conditions = {
        'chest pain': 10,
        'heart attack': 10,
        'stroke': 10,
        'severe bleeding': 10,
        'unconscious': 10,
        'not breathing': 10,
        'seizure': 10,
        'severe allergic': 9,
        'head injury': 9,
        'severe burn': 9,
        'poisoning': 9,
        'suicide': 10,
        'severe trauma': 9,
        'coughing blood': 9,
        'severe abdominal pain': 8
    }
    
    # Urgent conditions (need prompt attention but not immediately life-threatening)
    urgent_conditions = {
        'high fever': 7,
        'broken bone': 7,
        'sprain': 6,
        'cut': 6,
        'moderate pain': 6,
        'infection': 6,
        'asthma': 7,
        'dehydration': 7,
        'migraine': 6,
        'eye injury': 7,
        'ear pain': 6,
        'severe sore throat': 6,
        'persistent vomiting': 7,
        'moderate bleeding': 7,
        'difficulty breathing': 7
    }
    
    # Risk factors that increase priority
    risk_factors = {
        'pregnant': 3,
        'diabetes': 2,
        'heart disease': 2,
        'elderly': 2,
        'infant': 3,
        'cancer': 2,
        'immunocompromised': 2,
        'high blood pressure': 1,
        'recent surgery': 2
    }
    
    # Duration factors
    duration_indicators = {
        'sudden': 2,
        'severe': 2,
        'worsening': 1,
        'constant': 1,
        'chronic': -1  # Chronic conditions might be less urgent unless specified as severe
    }
    
    # Check for emergency conditions
    for condition, score in emergency_conditions.items():
        if condition in text:
            priority_score += score
    
    # Check for urgent conditions
    for condition, score in urgent_conditions.items():
        if condition in text:
            priority_score += score
    
    # Check for risk factors
    for factor, score in risk_factors.items():
        if factor in text:
            priority_score += score
    
    # Check duration and severity indicators
    for indicator, score in duration_indicators.items():
        if indicator in text:
            priority_score += score
    
    # Additional contextual analysis
    if 'cannot' in text or 'can\'t' in text:
        priority_score += 1
    if 'very' in text or 'extremely' in text:
        priority_score += 1
    if 'getting worse' in text or 'worsening' in text:
        priority_score += 2
    if 'days' in text:
        priority_score -= 1  # Longer duration might indicate less urgency
    if 'weeks' in text or 'months' in text:
        priority_score -= 2  # Chronic conditions unless specified as severe
    
    # Determine final priority level based on score
    if priority_score >= 8:
        return PRIORITY_LEVELS['emergency']  # Emergency
    elif priority_score >= 5:
        return PRIORITY_LEVELS['urgent']     # Urgent
    else:
        return PRIORITY_LEVELS['routine']    # Routine

def calculate_waiting_time(appointment_time, current_time, priority_level):
    """
    Calculate estimated waiting time in minutes considering priority level
    """
    base_wait = calculate_base_waiting_time(appointment_time, current_time)
    
    # Adjust waiting time based on priority
    if priority_level == PRIORITY_LEVELS['emergency']:
        return max(0, base_wait - 30)  # Reduce wait time by 30 minutes for emergencies
    elif priority_level == PRIORITY_LEVELS['urgent']:
        return max(0, base_wait - 15)  # Reduce wait time by 15 minutes for urgent cases
    
    return base_wait

def calculate_base_waiting_time(appointment_time, current_time):
    """Calculate base waiting time without priority adjustments"""
    from datetime import datetime
    apt_time = datetime.strptime(appointment_time, '%H:%M')
    current = datetime.strptime(current_time, '%H:%M')
    
    diff = apt_time - current
    return max(0, diff.seconds // 60)  # Convert to minutes, ensure non-negative

def get_next_available_slot(doctor_id, priority_level, appointments_collection, current_date):
    """
    Find the next available appointment slot based on priority and current load
    """
    # Get all appointments for the doctor on the current date
    existing_appointments = list(appointments_collection.find({
        'doctor_id': doctor_id,
        'appointment_date': current_date
    }).sort('priority_level', 1))
    
    # Get available slots
    taken_slots = [apt['appointment_time'] for apt in existing_appointments]
    available_slots = [slot for slot in TIME_SLOTS if slot not in taken_slots]
    
    if not available_slots:
        return None
    
    # For emergency cases (priority_level 1)
    if priority_level == PRIORITY_LEVELS['emergency']:
        # Try to find the earliest possible slot
        return available_slots[0]
    
    # For urgent cases (priority_level 2)
    elif priority_level == PRIORITY_LEVELS['urgent']:
        # Try to find a slot in the first half of the day
        mid_point = len(available_slots) // 2
        return available_slots[min(mid_point, len(available_slots) - 1)]
    
    # For routine cases (priority_level 3)
    else:
        # Consider the doctor's current load and distribute routine appointments
        current_load = len(existing_appointments)
        if current_load < 5:  # Light load
            return available_slots[len(available_slots) // 2]  # Mid-day slot
        else:  # Heavy load
            return available_slots[-1]  # Later slot

def should_notify_emergency(priority_level, symptoms):
    """
    Determine if emergency notification is needed based on priority and symptoms
    """
    if priority_level == PRIORITY_LEVELS['emergency']:
        emergency_indicators = [
            'chest pain', 'heart attack', 'stroke', 'severe bleeding',
            'unconscious', 'not breathing', 'seizure'
        ]
        return any(indicator in symptoms.lower() for indicator in emergency_indicators)
    return False 