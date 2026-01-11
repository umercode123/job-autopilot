# Job Autopilot - Flask API (Minimal MVP)
# REST API for Streamlit frontend

from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import sys

# Add modules to path
sys.path.insert(0, os.path.dirname(__file__))

from modules.logger_config import app_logger
from modules.database import init_db

app = Flask(__name__)
CORS(app)

# Initialize database
try:
    init_db()
    app_logger.info("Database initialized")
except Exception as e:
    app_logger.error(f"Database initialization failed: {e}")

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok", "message": "Job Autopilot API is running"})

@app.route('/api/jobs/search', methods=['POST'])
def search_jobs():
    """Search jobs endpoint (placeholder)"""
    data = request.json
    app_logger.info(f"Job search request: {data}")
    return jsonify({"message": "Job search endpoint - to be implemented"})

@app.route('/api/resume/optimize', methods=['POST'])
def optimize_resume():
    """Resume optimization endpoint (placeholder)"""
    return jsonify({"message": "Resume optimization endpoint - to be implemented"})

@app.route('/api/email/generate', methods=['POST'])
def generate_email():
    """Email generation endpoint (placeholder)"""
    return jsonify({"message": "Email generation endpoint - to be implemented"})

if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5000))
    app_logger.info(f"Starting Flask API on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)
