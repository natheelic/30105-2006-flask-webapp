from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
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

@app.route('/data-history')
def data_history():
    """หน้าสำหรับดูประวัติข้อมูลทั้งหมด"""
    esp32_data = db.get_esp32_data(100)
    user_data = db.get_user_data(50) if hasattr(db, 'get_user_data') else []
    stats = db.get_database_stats() if hasattr(db, 'get_database_stats') else {}
    
    return render_template('data_history.html', 
                         esp32_data=esp32_data, 
                         user_data=user_data,
                         stats=stats)

@app.route('/submit-data', methods=['POST'])
def submit_data():
    data_from_input = request.form.get('data_input', '').strip()
    client_ip = request.remote_addr
    
    if not data_from_input:
        flash('กรุณากรอกข้อมูล', 'error')
        return redirect(url_for('add_data'))
    
    # บันทึกลงฐานข้อมูล
    record_id = db.insert_user_data(data_from_input, client_ip)
    
    if record_id:
        logger.info(f"User data saved with ID: {record_id}")
        flash('บันทึกข้อมูลเรียบร้อยแล้ว!', 'success')
        status = "success"
    else:
        logger.error("Failed to save user data")
        flash('เกิดข้อผิดพลาดในการบันทึกข้อมูล', 'error')
        status = "error"
    
    return render_template('submit_data.html', 
                         data=data_from_input, 
                         status=status,
                         record_id=record_id)

@app.route('/api/esp32/data', methods=['POST'])
def api_esp32_data():
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No data received"}), 400
        
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

@app.route('/api/esp32/latest')
def api_esp32_latest():
    """API สำหรับดึงข้อมูลล่าสุดจาก ESP32"""
    try:
        data = db.get_latest_esp32_data() if hasattr(db, 'get_latest_esp32_data') else None
        
        if data:
            return jsonify({
                "status": "success",
                "data": data
            }), 200
        else:
            return jsonify({
                "status": "no_data",
                "message": "No ESP32 data found"
            }), 404
            
    except Exception as e:
        logger.error(f"Error fetching latest ESP32 data: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    try:
        connection = db.get_connection()
        if connection:
            # Test database query
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            connection.close()
            
            # Get database stats
            stats = db.get_database_stats() if hasattr(db, 'get_database_stats') else {}
            
            return jsonify({
                "status": "healthy",
                "database": "connected",
                "timestamp": datetime.now().isoformat(),
                "stats": stats
            }), 200
        else:
            return jsonify({
                "status": "unhealthy",
                "database": "disconnected",
                "timestamp": datetime.now().isoformat()
            }), 503
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "database": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 503

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000, debug=True)
