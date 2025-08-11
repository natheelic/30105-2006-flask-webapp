import pymysql
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.config = Config()
    
    def get_connection(self):
        try:
            connection = pymysql.connect(
                host=self.config.MYSQL_HOST,
                port=self.config.MYSQL_PORT,
                user=self.config.MYSQL_USER,
                password=self.config.MYSQL_PASSWORD,
                database=self.config.MYSQL_DB,
                charset=self.config.MYSQL_CHARSET,
                cursorclass=pymysql.cursors.DictCursor
            )
            return connection
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            return None
    
    def create_tables(self):
        """สร้างตารางที่จำเป็นในฐานข้อมูล"""
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
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        device_id VARCHAR(50),
                        raw_data JSON
                    )
                """)
                
                # สร้างตารางสำหรับข้อมูลจากฟอร์ม
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_data (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        data_input TEXT,
                        submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        ip_address VARCHAR(45)
                    )
                """)
                
                connection.commit()
                logger.info("Tables created successfully")
                return True
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            return False
        finally:
            connection.close()
    
    def insert_esp32_data(self, data):
        """บันทึกข้อมูล ESP32 ลงฐานข้อมูล"""
        connection = self.get_connection()
        if not connection:
            return False
        
        try:
            with connection.cursor() as cursor:
                sql = """
                    INSERT INTO esp32_data (temperature, humidity, device_id, raw_data)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(sql, (
                    data.get('temperature'),
                    data.get('humidity'),
                    data.get('device_id', 'unknown'),
                    str(data)
                ))
                connection.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error inserting ESP32 data: {e}")
            return False
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
                    SELECT * FROM esp32_data 
                    ORDER BY timestamp DESC 
                    LIMIT %s
                """
                cursor.execute(sql, (limit,))
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error fetching ESP32 data: {e}")
            return []
        finally:
            connection.close()
    
    def insert_user_data(self, data_input, ip_address):
        """บันทึกข้อมูลจากผู้ใช้"""
        connection = self.get_connection()
        if not connection:
            return False
        
        try:
            with connection.cursor() as cursor:
                sql = """
                    INSERT INTO user_data (data_input, ip_address)
                    VALUES (%s, %s)
                """
                cursor.execute(sql, (data_input, ip_address))
                connection.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error inserting user data: {e}")
            return False
        finally:
            connection.close()