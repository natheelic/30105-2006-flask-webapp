import pymysql
from config import Config
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.config = Config()
    
    def get_connection(self):
        """สร้างการเชื่อมต่อฐานข้อมูล MySQL"""
        try:
            connection = pymysql.connect(
                host=self.config.MYSQL_HOST,
                port=self.config.MYSQL_PORT,
                user=self.config.MYSQL_USER,
                password=self.config.MYSQL_PASSWORD,
                database=self.config.MYSQL_DB,
                charset=self.config.MYSQL_CHARSET,
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False
            )
            return connection
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            return None
    
    def create_database_if_not_exists(self):
        """สร้างฐานข้อมูลถ้าไม่มี"""
        try:
            # เชื่อมต่อโดยไม่ระบุฐานข้อมูล
            connection = pymysql.connect(
                host=self.config.MYSQL_HOST,
                port=self.config.MYSQL_PORT,
                user=self.config.MYSQL_USER,
                password=self.config.MYSQL_PASSWORD,
                charset=self.config.MYSQL_CHARSET
            )
            
            with connection.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.config.MYSQL_DB}")
                connection.commit()
                logger.info(f"Database {self.config.MYSQL_DB} created or already exists")
            
            connection.close()
            return True
        except Exception as e:
            logger.error(f"Error creating database: {e}")
            return False
    
    def create_tables(self):
        """Create all required tables"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create esp32_data table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS esp32_data (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    device_id VARCHAR(100) DEFAULT 'ESP32_DEFAULT',
                    temperature FLOAT,
                    humidity FLOAT,
                    light FLOAT,
                    raw_data JSON,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_device_timestamp (device_id, timestamp),
                    INDEX idx_timestamp (timestamp)
                )
            """)
            
            connection.commit()
            
            # Create device management tables
            self.create_device_tables()
            
            logging.info("All tables created successfully")
            
        except Exception as e:
            logging.error(f"Error creating tables: {e}")
            connection.rollback()
        finally:
            if connection:
                connection.close()
    
    def insert_esp32_data(self, data):
        """บันทึกข้อมูล ESP32 ลงฐานข้อมูล"""
        connection = self.get_connection()
        if not connection:
            return None
        
        try:
            with connection.cursor() as cursor:
                sql = """
                    INSERT INTO esp32_data (temperature, humidity, light, device_id, raw_data)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (
                    data.get('temperature'),
                    data.get('humidity'),
                    data.get('light'),
                    data.get('device_id', 'ESP32_DEFAULT'),
                    json.dumps(data)
                ))
                connection.commit()
                record_id = cursor.lastrowid
                logger.info(f"ESP32 data inserted with ID: {record_id}")
                return record_id
        except Exception as e:
            logger.error(f"Error inserting ESP32 data: {e}")
            connection.rollback()
            return None
        finally:
            connection.close()
    
    def get_esp32_data(self, limit=10, sensor_id=None):
        """Get ESP32 data with optional filtering"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            if sensor_id:
                query = """
                    SELECT id, device_id, temperature, humidity, light, raw_data, timestamp 
                    FROM esp32_data 
                    WHERE JSON_EXTRACT(raw_data, '$.sensor_id') = %s
                    ORDER BY timestamp DESC LIMIT %s
                """
                cursor.execute(query, (sensor_id, limit))
            else:
                query = """
                    SELECT id, device_id, temperature, humidity, light, raw_data, timestamp 
                    FROM esp32_data 
                    ORDER BY timestamp DESC LIMIT %s
                """
                cursor.execute(query, (limit,))
            
            rows = cursor.fetchall()
            
            result = []
            for row in rows:
                data = {
                    'id': row[0],
                    'device_id': row[1],
                    'temperature': row[2],
                    'humidity': row[3],
                    'light': row[4],
                    'raw_data': json.loads(row[5]) if row[5] else {},
                    'timestamp': row[6]
                }
                result.append(data)
            
            return result
            
        except Exception as e:
            logging.error(f"Error retrieving ESP32 data: {e}")
            return []
        finally:
            if connection:
                connection.close()

    def create_device_tables(self):
        """Create device management tables"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            # Create esp32_devices table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS esp32_devices (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    device_name VARCHAR(100) NOT NULL UNIQUE,
                    device_type ENUM('ESP32', 'PICO_WH', 'ESP8266') DEFAULT 'ESP32',
                    description TEXT,
                    wifi_ssid VARCHAR(100),
                    wifi_password VARCHAR(100),
                    pin_config JSON,
                    sensor_config JSON,
                    program_template VARCHAR(50) DEFAULT 'basic_sensor',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
            
            # Create program_templates table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS program_templates (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    template_name VARCHAR(100) NOT NULL UNIQUE,
                    template_type ENUM('ESP32', 'PICO_WH', 'ESP8266') DEFAULT 'ESP32',
                    description TEXT,
                    code_template LONGTEXT,
                    required_libraries JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            
            connection.commit()
            logging.info("Device management tables created successfully")
            
        except Exception as e:
            logging.error(f"Error creating device tables: {e}")
            connection.rollback()
        finally:
            if connection:
                connection.close()

    def add_device(self, device_data):
        """Add a new ESP32/PICO device"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            query = """
                INSERT INTO esp32_devices 
                (device_name, device_type, description, wifi_ssid, wifi_password, 
                 pin_config, sensor_config, program_template)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(query, (
                device_data['device_name'],
                device_data['device_type'],
                device_data['description'],
                device_data['wifi_ssid'],
                device_data['wifi_password'],
                json.dumps(device_data['pin_config']),
                json.dumps(device_data['sensor_config']),
                device_data['program_template']
            ))
            
            device_id = cursor.lastrowid
            connection.commit()
            logging.info(f"Device added successfully with ID: {device_id}")
            return device_id
            
        except Exception as e:
            logging.error(f"Error adding device: {e}")
            connection.rollback()
            return None
        finally:
            if connection:
                connection.close()

    def get_devices(self, device_type=None):
        """Get all devices or filtered by type"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            if device_type:
                query = """
                    SELECT id, device_name, device_type, description, wifi_ssid,
                           pin_config, sensor_config, program_template, created_at, is_active
                    FROM esp32_devices 
                    WHERE device_type = %s AND is_active = TRUE
                    ORDER BY created_at DESC
                """
                cursor.execute(query, (device_type,))
            else:
                query = """
                    SELECT id, device_name, device_type, description, wifi_ssid,
                           pin_config, sensor_config, program_template, created_at, is_active
                    FROM esp32_devices 
                    WHERE is_active = TRUE
                    ORDER BY created_at DESC
                """
                cursor.execute(query)
            
            rows = cursor.fetchall()
            devices = []
            
            for row in rows:
                device = {
                    'id': row[0],
                    'device_name': row[1],
                    'device_type': row[2],
                    'description': row[3],
                    'wifi_ssid': row[4],
                    'pin_config': json.loads(row[5]) if row[5] else {},
                    'sensor_config': json.loads(row[6]) if row[6] else {},
                    'program_template': row[7],
                    'created_at': row[8],
                    'is_active': row[9]
                }
                devices.append(device)
            
            return devices
            
        except Exception as e:
            logging.error(f"Error retrieving devices: {e}")
            return []
        finally:
            if connection:
                connection.close()

    def get_device_by_id(self, device_id):
        """Get device by ID"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            query = """
                SELECT id, device_name, device_type, description, wifi_ssid, wifi_password,
                       pin_config, sensor_config, program_template, created_at, is_active
                FROM esp32_devices 
                WHERE id = %s AND is_active = TRUE
            """
            cursor.execute(query, (device_id,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'id': row[0],
                    'device_name': row[1],
                    'device_type': row[2],
                    'description': row[3],
                    'wifi_ssid': row[4],
                    'wifi_password': row[5],
                    'pin_config': json.loads(row[6]) if row[6] else {},
                    'sensor_config': json.loads(row[7]) if row[7] else {},
                    'program_template': row[8],
                    'created_at': row[9],
                    'is_active': row[10]
                }
            return None
            
        except Exception as e:
            logging.error(f"Error retrieving device: {e}")
            return None
        finally:
            if connection:
                connection.close()

    def add_program_template(self, template_data):
        """Add a program template"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            query = """
                INSERT INTO program_templates 
                (template_name, template_type, description, code_template, required_libraries)
                VALUES (%s, %s, %s, %s, %s)
            """
            
            cursor.execute(query, (
                template_data['template_name'],
                template_data['template_type'],
                template_data['description'],
                template_data['code_template'],
                json.dumps(template_data['required_libraries'])
            ))
            
            template_id = cursor.lastrowid
            connection.commit()
            logging.info(f"Program template added successfully with ID: {template_id}")
            return template_id
            
        except Exception as e:
            logging.error(f"Error adding program template: {e}")
            connection.rollback()
            return None
        finally:
            if connection:
                connection.close()

    def get_program_templates(self, template_type=None):
        """Get program templates"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            if template_type:
                query = """
                    SELECT id, template_name, template_type, description, 
                           code_template, required_libraries, created_at
                    FROM program_templates 
                    WHERE template_type = %s
                    ORDER BY template_name
                """
                cursor.execute(query, (template_type,))
            else:
                query = """
                    SELECT id, template_name, template_type, description, 
                           code_template, required_libraries, created_at
                    FROM program_templates 
                    ORDER BY template_name
                """
                cursor.execute(query)
            
            rows = cursor.fetchall()
            templates = []
            
            for row in rows:
                template = {
                    'id': row[0],
                    'template_name': row[1],
                    'template_type': row[2],
                    'description': row[3],
                    'code_template': row[4],
                    'required_libraries': json.loads(row[5]) if row[5] else [],
                    'created_at': row[6]
                }
                templates.append(template)
            
            return templates
            
        except Exception as e:
            logging.error(f"Error retrieving program templates: {e}")
            return []
        finally:
            if connection:
                connection.close()
    
    def get_latest_esp32_data(self):
        """ดึงข้อมูล ESP32 ล่าสุด"""
        data = self.get_esp32_data(1)
        return data[0] if data else None
    
    def insert_user_data(self, data_input, ip_address):
        """บันทึกข้อมูลจากผู้ใช้"""
        connection = self.get_connection()
        if not connection:
            return None
        
        try:
            with connection.cursor() as cursor:
                sql = """
                    INSERT INTO user_data (data_input, ip_address)
                    VALUES (%s, %s)
                """
                cursor.execute(sql, (data_input, ip_address))
                connection.commit()
                record_id = cursor.lastrowid
                logger.info(f"User data inserted with ID: {record_id}")
                return record_id
        except Exception as e:
            logger.error(f"Error inserting user data: {e}")
            connection.rollback()
            return None
        finally:
            connection.close()
    
    def get_user_data(self, limit=50):
        """ดึงข้อมูลจากผู้ใช้"""
        connection = self.get_connection()
        if not connection:
            return []
        
        try:
            with connection.cursor() as cursor:
                sql = """
                    SELECT id, data_input, ip_address, submitted_at
                    FROM user_data 
                    ORDER BY submitted_at DESC 
                    LIMIT %s
                """
                cursor.execute(sql, (limit,))
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error fetching user data: {e}")
            return []
        finally:
            connection.close()
    
    def get_database_stats(self):
        """ดึงสถิติฐานข้อมูล"""
        connection = self.get_connection()
        if not connection:
            return {}
        
        try:
            stats = {}
            with connection.cursor() as cursor:
                # นับข้อมูล ESP32
                cursor.execute("SELECT COUNT(*) as count FROM esp32_data")
                stats['esp32_count'] = cursor.fetchone()['count']
                
                # นับข้อมูลผู้ใช้
                cursor.execute("SELECT COUNT(*) as count FROM user_data")
                stats['user_data_count'] = cursor.fetchone()['count']
                
                # ข้อมูล ESP32 ล่าสุด
                cursor.execute("SELECT timestamp FROM esp32_data ORDER BY timestamp DESC LIMIT 1")
                result = cursor.fetchone()
                stats['last_esp32_data'] = result['timestamp'] if result else None
                
            return stats
        except Exception as e:
            logger.error(f"Error fetching database stats: {e}")
            return {}
        finally:
            connection.close()
    
    # ESP32 Device Management Methods
    def get_esp32_devices(self, active_only=True):
        """ดึงรายการ ESP32 devices"""
        connection = self.get_connection()
        if not connection:
            return []
        
        try:
            with connection.cursor() as cursor:
                if active_only:
                    sql = "SELECT * FROM esp32_devices WHERE is_active = TRUE ORDER BY device_name"
                else:
                    sql = "SELECT * FROM esp32_devices ORDER BY device_name"
                
                cursor.execute(sql)
                devices = cursor.fetchall()
                
                # แปลง pin_config จาก JSON
                for device in devices:
                    if device['pin_config']:
                        try:
                            device['pin_config'] = json.loads(device['pin_config'])
                        except (json.JSONDecodeError, TypeError):
                            device['pin_config'] = {}
                
                return devices
        except Exception as e:
            logger.error(f"Error fetching ESP32 devices: {e}")
            return []
        finally:
            connection.close()
    
    def get_esp32_device(self, device_id):
        """ดึงข้อมูล ESP32 device เฉพาะ"""
        connection = self.get_connection()
        if not connection:
            return None
        
        try:
            with connection.cursor() as cursor:
                sql = "SELECT * FROM esp32_devices WHERE device_id = %s"
                cursor.execute(sql, (device_id,))
                device = cursor.fetchone()
                
                if device and device['pin_config']:
                    try:
                        device['pin_config'] = json.loads(device['pin_config'])
                    except (json.JSONDecodeError, TypeError):
                        device['pin_config'] = {}
                
                return device
        except Exception as e:
            logger.error(f"Error fetching ESP32 device: {e}")
            return None
        finally:
            connection.close()
    
    def add_esp32_device(self, device_data):
        """เพิ่ม ESP32 device ใหม่"""
        connection = self.get_connection()
        if not connection:
            return None
        
        try:
            with connection.cursor() as cursor:
                sql = """
                    INSERT INTO esp32_devices 
                    (device_id, device_name, description, pin_config, location, program_code)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (
                    device_data.get('device_id'),
                    device_data.get('device_name'),
                    device_data.get('description', ''),
                    json.dumps(device_data.get('pin_config', {})),
                    device_data.get('location', ''),
                    device_data.get('program_code', '')
                ))
                connection.commit()
                device_id = cursor.lastrowid
                logger.info(f"ESP32 device added with ID: {device_id}")
                return device_id
        except Exception as e:
            logger.error(f"Error adding ESP32 device: {e}")
            connection.rollback()
            return None
        finally:
            connection.close()
    
    def update_esp32_device(self, device_id, device_data):
        """อัพเดท ESP32 device"""
        connection = self.get_connection()
        if not connection:
            return False
        
        try:
            with connection.cursor() as cursor:
                sql = """
                    UPDATE esp32_devices 
                    SET device_name = %s, description = %s, pin_config = %s, 
                        location = %s, program_code = %s, updated_at = NOW()
                    WHERE device_id = %s
                """
                cursor.execute(sql, (
                    device_data.get('device_name'),
                    device_data.get('description', ''),
                    json.dumps(device_data.get('pin_config', {})),
                    device_data.get('location', ''),
                    device_data.get('program_code', ''),
                    device_id
                ))
                connection.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating ESP32 device: {e}")
            connection.rollback()
            return False
        finally:
            connection.close()
    
    def delete_esp32_device(self, device_id):
        """ลบ ESP32 device (soft delete)"""
        connection = self.get_connection()
        if not connection:
            return False
        
        try:
            with connection.cursor() as cursor:
                sql = "UPDATE esp32_devices SET is_active = FALSE WHERE device_id = %s"
                cursor.execute(sql, (device_id,))
                connection.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting ESP32 device: {e}")
            connection.rollback()
            return False
        finally:
            connection.close()
    
    # ESP32 Program Management Methods
    def get_esp32_programs(self):
        """ดึงรายการโปรแกรม ESP32"""
        connection = self.get_connection()
        if not connection:
            return []
        
        try:
            with connection.cursor() as cursor:
                sql = "SELECT * FROM esp32_programs ORDER BY created_at DESC"
                cursor.execute(sql)
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error fetching ESP32 programs: {e}")
            return []
        finally:
            connection.close()
    
    def add_esp32_program(self, program_data):
        """เพิ่มโปรแกรม ESP32"""
        connection = self.get_connection()
        if not connection:
            return None
        
        try:
            with connection.cursor() as cursor:
                sql = """
                    INSERT INTO esp32_programs 
                    (program_name, description, program_code, version, created_by)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (
                    program_data.get('program_name'),
                    program_data.get('description', ''),
                    program_data.get('program_code'),
                    program_data.get('version', '1.0.0'),
                    program_data.get('created_by', 'Admin')
                ))
                connection.commit()
                program_id = cursor.lastrowid
                logger.info(f"ESP32 program added with ID: {program_id}")
                return program_id
        except Exception as e:
            logger.error(f"Error adding ESP32 program: {e}")
            connection.rollback()
            return None
        finally:
            connection.close()
    
    def get_esp32_program(self, program_id):
        """ดึงโปรแกรม ESP32 เฉพาะ"""
        connection = self.get_connection()
        if not connection:
            return None
        
        try:
            with connection.cursor() as cursor:
                sql = "SELECT * FROM esp32_programs WHERE id = %s"
                cursor.execute(sql, (program_id,))
                return cursor.fetchone()
        except Exception as e:
            logger.error(f"Error fetching ESP32 program: {e}")
            return None
        finally:
            connection.close()
    
    def update_device_last_seen(self, device_id):
        """อัพเดท last seen ของ ESP32 device"""
        connection = self.get_connection()
        if not connection:
            return False
        
        try:
            with connection.cursor() as cursor:
                sql = "UPDATE esp32_devices SET last_seen = NOW() WHERE device_id = %s"
                cursor.execute(sql, (device_id,))
                connection.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating device last seen: {e}")
            connection.rollback()
            return False
        finally:
            connection.close()