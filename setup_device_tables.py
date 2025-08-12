#!/usr/bin/env python3
"""
Database Setup Script - Create device management tables
"""

import mysql.connector
import json
from config import Config

def create_device_tables():
    """Create device management tables"""
    try:
        # Connect to MySQL
        connection = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB
        )
        
        cursor = connection.cursor()
        
        print("Creating ESP32 devices table...")
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
        
        print("Creating program templates table...")
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
        print("✓ Device management tables created successfully!")
        
        # Add sample templates
        print("Adding sample program templates...")
        
        templates = [
            {
                'template_name': 'basic_sensor',
                'template_type': 'ESP32',
                'description': 'Basic sensor reading with WiFi connectivity',
                'required_libraries': ['urequests', 'dht', 'machine', 'network']
            },
            {
                'template_name': 'advanced_iot',
                'template_type': 'ESP32', 
                'description': 'Advanced IoT with deep sleep and OTA updates',
                'required_libraries': ['urequests', 'dht', 'machine', 'network', 'esp32']
            },
            {
                'template_name': 'relay_control',
                'template_type': 'ESP32',
                'description': 'Relay control system with web interface',
                'required_libraries': ['urequests', 'socket', 'machine', 'network']
            },
            {
                'template_name': 'basic_sensor',
                'template_type': 'PICO_WH',
                'description': 'Basic sensor reading for Raspberry Pi Pico WH',
                'required_libraries': ['urequests', 'dht', 'machine', 'network']
            }
        ]
        
        for template in templates:
            try:
                cursor.execute("""
                    INSERT IGNORE INTO program_templates 
                    (template_name, template_type, description, required_libraries)
                    VALUES (%s, %s, %s, %s)
                """, (
                    f"{template['template_name']}_{template['template_type'].lower()}",
                    template['template_type'],
                    template['description'],
                    json.dumps(template['required_libraries'])
                ))
            except Exception as e:
                print(f"Template insert error: {e}")
        
        connection.commit()
        print("✓ Sample templates added!")
        
        # Show existing tables
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print("\nExisting tables:")
        for table in tables:
            print(f"  - {table[0]}")
            
        # Show esp32_devices structure
        cursor.execute("DESCRIBE esp32_devices")
        columns = cursor.fetchall()
        print("\nesp32_devices table structure:")
        for col in columns:
            print(f"  - {col[0]} ({col[1]})")
        
        connection.close()
        print("\n✓ Database setup completed successfully!")
        
    except Exception as e:
        print(f"✗ Database setup failed: {e}")
        if 'connection' in locals():
            connection.rollback()
            connection.close()

if __name__ == "__main__":
    print("Setting up device management database...")
    create_device_tables()
