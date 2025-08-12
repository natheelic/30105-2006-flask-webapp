from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file
from database import Database
from config import Config
from code_generator import code_gen
import logging
import json
import os
import tempfile
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

@app.route('/manage-esp32')
def manage_esp32():
    """หน้าจัดการ ESP32 Devices"""
    devices = db.get_esp32_devices() if hasattr(db, 'get_esp32_devices') else []
    return render_template('manage_esp32.html', devices=devices)

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

# ESP32 Device Management API Routes
@app.route('/api/esp32/devices', methods=['GET'])
def api_get_esp32_devices():
    """API สำหรับดึงรายการ ESP32 devices"""
    try:
        devices = db.get_esp32_devices()
        return jsonify({
            "status": "success",
            "count": len(devices),
            "devices": devices
        }), 200
    except Exception as e:
        logger.error(f"Error fetching ESP32 devices: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/esp32/devices', methods=['POST'])
def api_add_esp32_device():
    """API สำหรับเพิ่ม ESP32 device ใหม่"""
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No data received"}), 400
        
        # ตรวจสอบข้อมูลที่จำเป็น
        required_fields = ['device_id', 'device_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    "status": "error", 
                    "message": f"Missing required field: {field}"
                }), 400
        
        device_id = db.add_esp32_device(data)
        
        if device_id:
            logger.info(f"ESP32 device added with ID: {device_id}")
            return jsonify({
                "status": "success",
                "message": "Device added successfully",
                "device_id": device_id
            }), 201
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to add device"
            }), 500
            
    except Exception as e:
        logger.error(f"Error adding ESP32 device: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/esp32/devices/<device_id>', methods=['GET'])
def api_get_esp32_device(device_id):
    """API สำหรับดึงข้อมูล ESP32 device เฉพาะ"""
    try:
        device = db.get_esp32_device(device_id)
        
        if device:
            return jsonify(device), 200
        else:
            return jsonify({
                "status": "error",
                "message": "Device not found"
            }), 404
            
    except Exception as e:
        logger.error(f"Error fetching ESP32 device: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/esp32/devices/<device_id>', methods=['PUT'])
def api_update_esp32_device(device_id):
    """API สำหรับอัพเดท ESP32 device"""
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No data received"}), 400
        
        success = db.update_esp32_device(device_id, data)
        
        if success:
            logger.info(f"ESP32 device updated: {device_id}")
            return jsonify({
                "status": "success",
                "message": "Device updated successfully"
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to update device or device not found"
            }), 404
            
    except Exception as e:
        logger.error(f"Error updating ESP32 device: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/esp32/devices/<device_id>', methods=['DELETE'])
def api_delete_esp32_device(device_id):
    """API สำหรับลบ ESP32 device"""
    try:
        success = db.delete_esp32_device(device_id)
        
        if success:
            logger.info(f"ESP32 device deleted: {device_id}")
            return jsonify({
                "status": "success",
                "message": "Device deleted successfully"
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to delete device or device not found"
            }), 404
            
    except Exception as e:
        logger.error(f"Error deleting ESP32 device: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# ESP32 Program Management API Routes
@app.route('/api/esp32/programs', methods=['GET'])
def api_get_esp32_programs():
    """API สำหรับดึงรายการโปรแกรม ESP32"""
    try:
        programs = db.get_esp32_programs()
        return jsonify(programs), 200
    except Exception as e:
        logger.error(f"Error fetching ESP32 programs: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/esp32/programs/<int:program_id>', methods=['GET'])
def api_get_esp32_program(program_id):
    """API สำหรับดึงโปรแกรม ESP32 เฉพาะ"""
    try:
        program = db.get_esp32_program(program_id)
        
        if program:
            return jsonify(program), 200
        else:
            return jsonify({
                "status": "error",
                "message": "Program not found"
            }), 404
            
    except Exception as e:
        logger.error(f"Error fetching ESP32 program: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/esp32/programs', methods=['POST'])
def api_add_esp32_program():
    """API สำหรับเพิ่มโปรแกรม ESP32"""
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No data received"}), 400
        
        # ตรวจสอบข้อมูลที่จำเป็น
        required_fields = ['program_name', 'program_code']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    "status": "error", 
                    "message": f"Missing required field: {field}"
                }), 400
        
        program_id = db.add_esp32_program(data)
        
        if program_id:
            logger.info(f"ESP32 program added with ID: {program_id}")
            return jsonify({
                "status": "success",
                "message": "Program added successfully",
                "program_id": program_id
            }), 201
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to add program"
            }), 500
            
    except Exception as e:
        logger.error(f"Error adding ESP32 program: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# ESP32/PICO Device Management Routes

@app.route('/devices')
def device_management():
    """Device management page"""
    try:
        devices = db.get_devices()
        templates = db.get_program_templates()
        return render_template('device_management.html', devices=devices, templates=templates)
    except Exception as e:
        logger.error(f"Error loading devices: {e}")
        flash(f"Error loading devices: {e}", 'error')
        return redirect(url_for('home'))

@app.route('/devices/add', methods=['GET', 'POST'])
def add_device():
    """Add new ESP32/PICO device"""
    if request.method == 'POST':
        try:
            device_data = {
                'device_name': request.form.get('device_name'),
                'device_type': request.form.get('device_type', 'ESP32'),
                'description': request.form.get('description', ''),
                'wifi_ssid': request.form.get('wifi_ssid', ''),
                'wifi_password': request.form.get('wifi_password', ''),
                'program_template': request.form.get('program_template', 'basic_sensor'),
                'pin_config': {
                    'temperature_pin': int(request.form.get('temp_pin', 4)),
                    'light_pin': int(request.form.get('light_pin', 32)),
                    'led_pin': int(request.form.get('led_pin', 2)),
                    'relay_pin': int(request.form.get('relay_pin', 5))
                },
                'sensor_config': {
                    'temperature_enabled': 'temp_enabled' in request.form,
                    'humidity_enabled': 'humidity_enabled' in request.form,
                    'light_enabled': 'light_enabled' in request.form,
                    'soil_moisture_enabled': 'soil_enabled' in request.form
                }
            }
            
            device_id = db.add_device(device_data)
            
            if device_id:
                flash(f"Device '{device_data['device_name']}' added successfully!", 'success')
                return redirect(url_for('device_management'))
            else:
                flash("Failed to add device", 'error')
                
        except Exception as e:
            logger.error(f"Error adding device: {e}")
            flash(f"Error adding device: {e}", 'error')
    
    return render_template('add_device.html')

@app.route('/devices/<int:device_id>')
def device_details(device_id):
    """View device details and generated code"""
    try:
        device = db.get_device_by_id(device_id)
        if not device:
            flash("Device not found", 'error')
            return redirect(url_for('device_management'))
        
        # Generate code for the device
        generated_code = code_gen.generate_code(device, device['program_template'])
        
        return render_template('device_details.html', device=device, code=generated_code)
        
    except Exception as e:
        logger.error(f"Error loading device details: {e}")
        flash(f"Error loading device: {e}", 'error')
        return redirect(url_for('device_management'))

@app.route('/devices/<int:device_id>/download')
def download_device_code(device_id):
    """Download generated code for device"""
    try:
        device = db.get_device_by_id(device_id)
        if not device:
            return jsonify({"error": "Device not found"}), 404
        
        # Generate code
        generated_code = code_gen.generate_code(device, device['program_template'])
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
        temp_file.write(generated_code)
        temp_file.close()
        
        filename = f"{device['device_name']}_main.py"
        
        response = send_file(temp_file.name, as_attachment=True, download_name=filename)
        response.call_on_close(lambda: os.unlink(temp_file.name))
        
        return response
        
    except Exception as e:
        logger.error(f"Error downloading code: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/devices/<int:device_id>/uploader')
def download_uploader(device_id):
    """Download Python uploader script"""
    try:
        device = db.get_device_by_id(device_id)
        if not device:
            return jsonify({"error": "Device not found"}), 404
        
        # Generate device code
        device_code = code_gen.generate_code(device, device['program_template'])
        
        # Generate uploader script
        uploader_code = code_gen.generate_python_uploader(device, device_code)
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
        temp_file.write(uploader_code)
        temp_file.close()
        
        filename = f"{device['device_name']}_uploader.py"
        
        response = send_file(temp_file.name, as_attachment=True, download_name=filename)
        response.call_on_close(lambda: os.unlink(temp_file.name))
        
        return response
        
    except Exception as e:
        logger.error(f"Error downloading uploader: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/devices', methods=['GET'])
def api_get_devices():
    """API endpoint to get all devices"""
    try:
        device_type = request.args.get('type')
        devices = db.get_devices(device_type)
        return jsonify({
            "status": "success",
            "devices": devices,
            "count": len(devices)
        })
    except Exception as e:
        logger.error(f"Error getting devices: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/devices/<int:device_id>/code')
def api_generate_code(device_id):
    """API endpoint to generate code for device"""
    try:
        device = db.get_device_by_id(device_id)
        if not device:
            return jsonify({"error": "Device not found"}), 404
        
        template_type = request.args.get('template', device['program_template'])
        generated_code = code_gen.generate_code(device, template_type)
        
        return jsonify({
            "status": "success",
            "device_name": device['device_name'],
            "device_type": device['device_type'],
            "template": template_type,
            "code": generated_code
        })
        
    except Exception as e:
        logger.error(f"Error generating code: {e}")
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000, debug=True)
