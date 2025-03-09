from datetime import datetime
from config.config import appointments_collection
from bson import ObjectId

def generate_recommendations(patient_id):
    """
    Generate personalized health recommendations based on:
    1. Patient's consultation history
    2. Diagnosis patterns
    3. Treatment adherence
    4. Visit frequency
    5. Age-based recommendations
    6. Seasonal health patterns
    """
    # Get patient's complete medical history
    consultations = list(appointments_collection.find({
        'patient_id': patient_id,
        '$or': [
            {'type': 'consultation'},
            {'type': 'appointment', 'status': 'completed'}
        ]
    }).sort('created_at', -1))
    
    recommendations = []
    
    if not consultations:
        return [
            "Welcome to your health journey! Schedule your first check-up to start monitoring your health.",
            "Regular health check-ups help prevent potential health issues.",
            "Keep track of any symptoms or health concerns to discuss with your doctor."
        ]
    
    # Analyze consultation patterns
    diagnoses = [cons.get('diagnosis', '').lower() for cons in consultations if cons.get('diagnosis')]
    symptoms = [cons.get('symptoms', '').lower() for cons in consultations if cons.get('symptoms')]
    prescriptions = [cons.get('prescription', '').lower() for cons in consultations if cons.get('prescription')]
    
    # 1. Analyze visit frequency and adherence
    if len(consultations) >= 2:
        visit_dates = [cons['created_at'] for cons in consultations if cons.get('created_at')]
        if visit_dates:
            days_since_last = (datetime.now() - visit_dates[0]).days
            if days_since_last > 180:
                recommendations.append("It's been over 6 months since your last check-up. Consider scheduling a visit.")
            
            # Calculate average visit interval
            intervals = [(visit_dates[i] - visit_dates[i+1]).days 
                        for i in range(len(visit_dates)-1)]
            if intervals:
                avg_interval = sum(intervals) / len(intervals)
                if avg_interval > 120:  # If average gap is more than 4 months
                    recommendations.append("Regular check-ups are important. Consider scheduling visits more frequently.")
    
    # 2. Analyze chronic conditions
    condition_patterns = {
        'diabetes': {
            'keywords': ['diabetes', 'blood sugar', 'glucose', 'a1c'],
            'recommendations': [
                "Monitor your blood sugar levels regularly",
                "Maintain a balanced diet with controlled carbohydrate intake",
                "Regular exercise helps control blood sugar levels",
                "Keep a food and blood sugar diary"
            ]
        },
        'hypertension': {
            'keywords': ['hypertension', 'blood pressure', 'bp high'],
            'recommendations': [
                "Monitor your blood pressure daily",
                "Reduce salt intake in your diet",
                "Practice stress management techniques",
                "Take medications regularly as prescribed"
            ]
        },
        'heart': {
            'keywords': ['heart', 'cardiac', 'cholesterol', 'cardiovascular'],
            'recommendations': [
                "Regular cardiovascular exercise is important",
                "Maintain a heart-healthy diet low in saturated fats",
                "Monitor your cholesterol levels",
                "Stay active and maintain a healthy weight"
            ]
        },
        'respiratory': {
            'keywords': ['asthma', 'copd', 'breathing', 'respiratory'],
            'recommendations': [
                "Keep your inhaler accessible at all times",
                "Avoid known triggers that affect your breathing",
                "Monitor your peak flow readings",
                "Ensure your living space is well-ventilated"
            ]
        },
        'joint': {
            'keywords': ['arthritis', 'joint pain', 'rheumatoid', 'osteo'],
            'recommendations': [
                "Regular gentle exercises help maintain joint flexibility",
                "Apply heat/cold therapy as recommended",
                "Maintain proper posture during daily activities",
                "Consider low-impact exercises like swimming"
            ]
        }
    }
    
    # Check for chronic conditions in diagnosis history
    for condition, data in condition_patterns.items():
        if any(any(keyword in diagnosis for keyword in data['keywords']) 
               for diagnosis in diagnoses):
            recommendations.extend(data['recommendations'])
    
    # 3. Analyze recent symptoms for acute conditions
    recent_symptoms = symptoms[0] if symptoms else ""
    acute_patterns = {
        'pain': {
            'keywords': ['pain', 'ache', 'sore'],
            'recommendations': [
                "Rest the affected area and avoid strenuous activity",
                "Apply ice/heat therapy as appropriate",
                "Monitor pain levels and note any changes",
                "Follow prescribed pain management techniques"
            ]
        },
        'infection': {
            'keywords': ['fever', 'infection', 'flu', 'cold'],
            'recommendations': [
                "Get adequate rest and stay hydrated",
                "Monitor your temperature regularly",
                "Complete the full course of prescribed medications",
                "Practice good hygiene to prevent spread"
            ]
        },
        'digestive': {
            'keywords': ['stomach', 'digestion', 'nausea', 'gastric'],
            'recommendations': [
                "Maintain a food diary to identify triggers",
                "Eat smaller, frequent meals",
                "Stay hydrated with clear fluids",
                "Avoid known irritant foods"
            ]
        }
    }
    
    # Add recommendations for acute conditions
    if recent_symptoms:
        for condition, data in acute_patterns.items():
            if any(keyword in recent_symptoms for keyword in data['keywords']):
                recommendations.extend(data['recommendations'])
    
    # 4. Analyze medication adherence
    if prescriptions:
        recommendations.extend([
            "Take medications as prescribed by your doctor",
            "Keep a medication schedule to ensure timely doses",
            "Don't skip or modify doses without consulting your doctor",
            "Report any side effects to your healthcare provider"
        ])
    
    # 5. Add seasonal health recommendations
    current_month = datetime.now().month
    if 11 <= current_month <= 2:  # Winter
        recommendations.extend([
            "Stay warm and protect yourself from cold weather",
            "Get your flu vaccination if you haven't already",
            "Keep your immune system strong with proper nutrition"
        ])
    elif 3 <= current_month <= 5:  # Spring
        recommendations.extend([
            "Be mindful of seasonal allergies",
            "Stay active with outdoor activities",
            "Maintain good respiratory health"
        ])
    elif 6 <= current_month <= 8:  # Summer
        recommendations.extend([
            "Stay hydrated in warm weather",
            "Protect your skin from sun exposure",
            "Exercise during cooler parts of the day"
        ])
    else:  # Fall
        recommendations.extend([
            "Prepare for flu season with preventive measures",
            "Maintain regular exercise as weather changes",
            "Keep up with vitamin D intake"
        ])
    
    # 6. Add general wellness recommendations
    general_recommendations = [
        "Maintain a balanced diet rich in fruits and vegetables",
        "Aim for 7-8 hours of quality sleep each night",
        "Stay physically active with regular exercise",
        "Practice stress management techniques",
        "Keep up with preventive health screenings",
        "Stay socially connected and maintain mental well-being"
    ]
    
    recommendations.extend(general_recommendations)
    
    # Remove duplicates and limit to most relevant recommendations
    recommendations = list(dict.fromkeys(recommendations))
    return recommendations[:10]  # Return top 10 most relevant recommendations

def analyze_health_trends(patient_id):
    """
    Analyze patient's health trends based on consultation history
    Returns insights about health patterns
    """
    consultations = list(appointments_collection.find({
        'patient_id': patient_id,
        '$or': [
            {'type': 'consultation'},
            {'type': 'appointment', 'status': 'completed'}
        ]
    }).sort('created_at', -1))
    
    trends = []
    
    if not consultations:
        trends.append("No consultation history available yet. Regular check-ups help maintain good health.")
        return trends
        
    # Analyze visit frequency
    if len(consultations) >= 2:
        recent_visits = [cons for cons in consultations if cons.get('created_at')]
        if recent_visits:
            latest_visit = recent_visits[0].get('created_at')
            if latest_visit:
                days_since_last = (datetime.now() - latest_visit).days
                if days_since_last > 180:
                    trends.append("It's been over 6 months since your last visit. Consider scheduling a check-up.")
                elif days_since_last > 90:
                    trends.append("It's been over 3 months since your last visit.")
    
    # Analyze recurring conditions
    diagnoses = [cons.get('diagnosis', '').lower() for cons in consultations if cons.get('diagnosis')]
    if diagnoses:
        recurring = [d for d in set(diagnoses) if diagnoses.count(d) > 1]
        if recurring:
            trends.append(f"You have had recurring issues with: {', '.join(recurring)}. Consider discussing a long-term management plan.")
    
    # Check follow-up adherence
    follow_ups = [c for c in consultations if c.get('next_visit_needed')]
    if follow_ups:
        latest_follow_up = follow_ups[0]
        if latest_follow_up.get('next_visit_recommendation'):
            trends.append(f"Your last visit recommended a follow-up: {latest_follow_up['next_visit_recommendation']}")
    
    # Analyze recent health changes
    if len(consultations) >= 2:
        latest = consultations[0]
        previous = consultations[1]
        if (latest.get('diagnosis') and previous.get('diagnosis') and 
            latest['diagnosis'].lower() != previous['diagnosis'].lower()):
            trends.append("Your recent health concerns differ from previous visits. Keep monitoring any new symptoms.")
    
    # Add general insights based on consultation frequency
    if len(consultations) == 1:
        trends.append("This is your first consultation. Regular check-ups are important for preventive care.")
    elif len(consultations) > 5:
        trends.append("You've been regularly monitoring your health. Keep up the good work!")
    
    return trends 