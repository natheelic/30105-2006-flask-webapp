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
        """สร้างตารางที่จำเป็นในฐานข้อมูล"""
        # สร้างฐานข้อมูลก่อน
        if not self.create_database_if_not_exists():
            return False
        
        connection = self.get_connection()
        if not connection:
            return False
        
        try:
            with connection.cursor() as cursor:
                # สร้างตารางสำหรับข้อมูล ESP32
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS esp32_data (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        temperature FLOAT,
                        humidity FLOAT,
                        light FLOAT,
                        device_id VARCHAR(50),
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        raw_data JSON,
                        INDEX idx_timestamp (timestamp),
                        INDEX idx_device_id (device_id)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """)
                
                # สร้างตารางสำหรับข้อมูลจากผู้ใช้
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_data (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        data_input TEXT NOT NULL,
                        ip_address VARCHAR(45),
                        submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_submitted_at (submitted_at)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """)
                
                connection.commit()
                logger.info("All tables created successfully")
                return True
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            connection.rollback()
            return False
        finally:
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
    
    def get_esp32_data(self, limit=50):
        """ดึงข้อมูล ESP32 จากฐานข้อมูล"""
        connection = self.get_connection()
        if not connection:
            return []
        
        try:
            with connection.cursor() as cursor:
                sql = """
                    SELECT id, temperature, humidity, light, device_id, timestamp, raw_data
                    FROM esp32_data 
                    ORDER BY timestamp DESC 
                    LIMIT %s
                """
                cursor.execute(sql, (limit,))
                results = cursor.fetchall()
                
                # แปลง raw_data จาก JSON string กลับเป็น dict
                for row in results:
                    if row['raw_data']:
                        try:
                            row['raw_data'] = json.loads(row['raw_data'])
                        except (json.JSONDecodeError, TypeError):
                            row['raw_data'] = {}
                
                return results
        except Exception as e:
            logger.error(f"Error fetching ESP32 data: {e}")
            return []
        finally:
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