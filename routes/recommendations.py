from flask import Blueprint, jsonify
from utils.ai_utils import generate_recommendations, analyze_health_trends
from bson import ObjectId
from datetime import datetime

recommendations_bp = Blueprint('recommendations', __name__)

@recommendations_bp.route('/recommendations/<patient_id>', methods=['GET'])
def get_recommendations(patient_id):
    """Get AI-generated health recommendations for a patient"""
    try:
        recommendations = generate_recommendations(patient_id)
        trends = analyze_health_trends(patient_id)
        
        return jsonify({
            'recommendations': recommendations,
            'trends': trends,
            'last_updated': datetime.now().strftime('%Y-%m-%d %I:%M %p')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500 