from flask import Flask, render_template, request, jsonify
from database import Database
from config import Config
import logging
import json
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
db = Database()

# Create tables on startup
with app.app_context():
    if db.create_tables():
        logger.info("Database initialized successfully")
    else:
        logger.error("Failed to initialize database")

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/esp32')
def esp32():
    # ดึงข้อมูล ESP32 ล่าสุดจากฐานข้อมูล
    data = db.get_esp32_data(20)  # ดึง 20 รายการล่าสุด
    return render_template('esp32.html', esp32_data=data)

@app.route('/add-data')
def add_data():
    return render_template('add_data.html')

@app.route('/about-me')
def about_me():
    return render_template('about_me.html')

@app.route('/submit-data', methods=['POST'])
def submit_data():
    data_from_input = request.form.get('data_input', '')
    client_ip = request.remote_addr
    
    # บันทึกลงฐานข้อมูล
    record_id = db.insert_user_data(data_from_input, client_ip)
    
    if record_id:
        logger.info(f"User data saved with ID: {record_id}")
        status = "success"
    else:
        logger.error("Failed to save user data")
        status = "error"
    
    return render_template('submit_data.html', 
                         data=data_from_input, 
                         status=status,
                         record_id=record_id)

@app.route('/api/esp32/data', methods=['POST'])
def api_esp32_data():
    try:
        data = request.json
        logger.info(f"📡 Received from ESP32: {data}")
        
        # บันทึกลงฐานข้อมูล
        record_id = db.insert_esp32_data(data)
        
        if record_id:
            response = {
                "status": "success", 
                "message": "Data saved successfully",
                "record_id": record_id,
                "received": data,
                "timestamp": datetime.now().isoformat()
            }
            return jsonify(response), 200
        else:
            response = {
                "status": "error", 
                "message": "Failed to save data",
                "received": data
            }
            return jsonify(response), 500
            
    except Exception as e:
        logger.error(f"Error processing ESP32 data: {e}")
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 400

@app.route('/api/esp32/data', methods=['GET'])
def get_esp32_data():
    """API สำหรับดึงข้อมูล ESP32"""
    try:
        limit = request.args.get('limit', 50, type=int)
        data = db.get_esp32_data(limit)
        
        return jsonify({
            "status": "success",
            "count": len(data),
            "data": data
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching ESP32 data: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    connection = db.get_connection()
    if connection:
        connection.close()
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }), 200
    else:
        return jsonify({
            "status": "unhealthy",
            "database": "disconnected",
            "timestamp": datetime.now().isoformat()
        }), 503

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000, debug=True)
