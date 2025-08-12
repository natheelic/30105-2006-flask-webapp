"""
Code Generator for ESP32 and Raspberry Pi Pico WH
Generates MicroPython code based on device configuration
"""

import json
from datetime import datetime

class CodeGenerator:
    def __init__(self):
        self.templates = {
            'ESP32': {
                'basic_sensor': self.esp32_basic_sensor_template,
                'advanced_iot': self.esp32_advanced_iot_template,
                'relay_control': self.esp32_relay_control_template
            },
            'PICO_WH': {
                'basic_sensor': self.pico_basic_sensor_template,
                'advanced_iot': self.pico_advanced_iot_template,
                'relay_control': self.pico_relay_control_template
            }
        }
    
    def generate_code(self, device_config, template_type='basic_sensor'):
        """Generate MicroPython code based on device configuration"""
        device_type = device_config.get('device_type', 'ESP32')
        
        if device_type in self.templates and template_type in self.templates[device_type]:
            return self.templates[device_type][template_type](device_config)
        else:
            return self.esp32_basic_sensor_template(device_config)
    
    def esp32_basic_sensor_template(self, config):
        """Generate basic sensor code for ESP32"""
        device_name = config.get('device_name', 'ESP32_Device')
        wifi_ssid = config.get('wifi_ssid', 'YOUR_WIFI_SSID')
        wifi_password = config.get('wifi_password', 'YOUR_WIFI_PASSWORD')
        pin_config = config.get('pin_config', {})
        
        temp_pin = pin_config.get('temperature_pin', 4)
        light_pin = pin_config.get('light_pin', 32)
        led_pin = pin_config.get('led_pin', 2)
        
        code = f'''# ESP32 Basic Sensor Code - Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Device: {device_name}

import network
import urequests as requests
import ujson as json
import time
import machine
from machine import Pin, ADC
import dht

# Configuration
DEVICE_NAME = "{device_name}"
WIFI_SSID = "{wifi_ssid}"
WIFI_PASSWORD = "{wifi_password}"
SERVER_URL = "http://YOUR_SERVER_IP:4000/api/esp32/data"

# Pin Setup
LED_PIN = {led_pin}
TEMP_PIN = {temp_pin}
LIGHT_PIN = {light_pin}

# Initialize hardware
led = Pin(LED_PIN, Pin.OUT)
dht_sensor = dht.DHT22(Pin(TEMP_PIN))
light_adc = ADC(Pin(LIGHT_PIN))
light_adc.atten(ADC.ATTN_11DB)

class ESP32Sensor:
    def __init__(self):
        self.wifi = network.WLAN(network.STA_IF)
        self.connected = False
        
    def connect_wifi(self):
        """Connect to WiFi"""
        print(f"Connecting to {{WIFI_SSID}}")
        self.wifi.active(True)
        self.wifi.connect(WIFI_SSID, WIFI_PASSWORD)
        
        timeout = 0
        while not self.wifi.isconnected() and timeout < 20:
            print(".", end="")
            time.sleep(1)
            timeout += 1
            
        if self.wifi.isconnected():
            self.connected = True
            print(f"\\nConnected! IP: {{self.wifi.ifconfig()[0]}}")
            return True
        else:
            print("\\nFailed to connect")
            return False
    
    def read_sensors(self):
        """Read sensor data"""
        data = {{
            "sensor_id": DEVICE_NAME,
            "temperature": 0.0,
            "humidity": 0.0,
            "light": 0.0
        }}
        
        try:
            dht_sensor.measure()
            time.sleep(0.5)
            data["temperature"] = dht_sensor.temperature()
            data["humidity"] = dht_sensor.humidity()
        except Exception as e:
            print(f"DHT Error: {{e}}")
            
        try:
            light_raw = light_adc.read()
            data["light"] = (light_raw / 4095) * 1000
        except Exception as e:
            print(f"Light Error: {{e}}")
            
        return data
    
    def send_data(self, data):
        """Send data to server"""
        try:
            headers = {{'Content-Type': 'application/json'}}
            response = requests.post(SERVER_URL, data=json.dumps(data), headers=headers)
            
            if response.status_code == 200:
                print("Data sent successfully")
                return True
            else:
                print(f"HTTP Error: {{response.status_code}}")
                return False
        except Exception as e:
            print(f"Send error: {{e}}")
            return False
    
    def run(self):
        """Main loop"""
        if not self.connect_wifi():
            return
            
        while True:
            try:
                sensor_data = self.read_sensors()
                self.send_data(sensor_data)
                time.sleep(30)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {{e}}")
                time.sleep(5)

# Run
if __name__ == "__main__":
    sensor = ESP32Sensor()
    sensor.run()
'''
        return code
    
    def pico_basic_sensor_template(self, config):
        """Generate basic sensor code for Pico WH"""
        device_name = config.get('device_name', 'PICO_Device')
        wifi_ssid = config.get('wifi_ssid', 'YOUR_WIFI_SSID')
        wifi_password = config.get('wifi_password', 'YOUR_WIFI_PASSWORD')
        
        code = f'''# Raspberry Pi Pico WH Basic Sensor Code - Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Device: {device_name}

import network
import urequests as requests
import ujson as json
import time
import machine
from machine import Pin, ADC
import dht

# Configuration
DEVICE_NAME = "{device_name}"
WIFI_SSID = "{wifi_ssid}"
WIFI_PASSWORD = "{wifi_password}"
SERVER_URL = "http://YOUR_SERVER_IP:4000/api/esp32/data"

# Pin Setup for Pico WH
LED_PIN = "LED"
TEMP_PIN = 2
LIGHT_PIN = 26

# Initialize hardware
led = Pin(LED_PIN, Pin.OUT)
dht_sensor = dht.DHT22(Pin(TEMP_PIN))
light_adc = ADC(LIGHT_PIN)

class PicoSensor:
    def __init__(self):
        self.wlan = network.WLAN(network.STA_IF)
        self.connected = False
        
    def connect_wifi(self):
        """Connect to WiFi"""
        self.wlan.active(True)
        self.wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        
        max_wait = 20
        while max_wait > 0:
            if self.wlan.status() < 0 or self.wlan.status() >= 3:
                break
            max_wait -= 1
            time.sleep(1)
        
        if self.wlan.status() == 3:
            self.connected = True
            print(f"Connected! IP: {{self.wlan.ifconfig()[0]}}")
            return True
        else:
            print("WiFi connection failed")
            return False
    
    def read_sensors(self):
        """Read sensor data"""
        data = {{
            "sensor_id": DEVICE_NAME,
            "device_type": "PICO_WH",
            "temperature": 0.0,
            "humidity": 0.0,
            "light": 0.0
        }}
        
        try:
            dht_sensor.measure()
            time.sleep(2)
            data["temperature"] = dht_sensor.temperature()
            data["humidity"] = dht_sensor.humidity()
        except Exception as e:
            print(f"DHT Error: {{e}}")
            
        try:
            light_raw = light_adc.read_u16()
            data["light"] = (light_raw / 65535) * 100
        except Exception as e:
            print(f"Light Error: {{e}}")
            
        return data
    
    def send_data(self, data):
        """Send data to server"""
        try:
            headers = {{'Content-Type': 'application/json'}}
            response = requests.post(SERVER_URL, data=json.dumps(data), headers=headers)
            
            if response.status_code == 200:
                print("Data sent successfully")
                return True
            else:
                print(f"HTTP Error: {{response.status_code}}")
                return False
        except Exception as e:
            print(f"Send error: {{e}}")
            return False
    
    def run(self):
        """Main loop"""
        if not self.connect_wifi():
            return
            
        while True:
            try:
                sensor_data = self.read_sensors()
                self.send_data(sensor_data)
                time.sleep(30)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {{e}}")
                time.sleep(5)

# Run
if __name__ == "__main__":
    sensor = PicoSensor()
    sensor.run()
'''
        return code
    
    def esp32_advanced_iot_template(self, config):
        """Advanced ESP32 template with more features"""
        return self.esp32_basic_sensor_template(config)
    
    def esp32_relay_control_template(self, config):
        """ESP32 relay control template"""
        return self.esp32_basic_sensor_template(config)
    
    def pico_advanced_iot_template(self, config):
        """Advanced Pico template"""
        return self.pico_basic_sensor_template(config)
    
    def pico_relay_control_template(self, config):
        """Pico relay control template"""
        return self.pico_basic_sensor_template(config)
    
    def generate_python_uploader(self, device_config, code_content):
        """Generate Python uploader script"""
        device_name = device_config.get('device_name', 'Device')
        device_type = device_config.get('device_type', 'ESP32')
        
        uploader_code = f'''#!/usr/bin/env python3
"""
Device Code Uploader for {device_type} - {device_name}
Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Requirements:
    pip install esptool ampy pyserial

Usage:
    python uploader.py [PORT]
"""

import os
import sys
import subprocess
import time

# Configuration
DEVICE_TYPE = "{device_type}"
DEVICE_NAME = "{device_name}"
BAUD_RATE = 115200

# Device code to upload
DEVICE_CODE = """{code_content}"""

def find_device_port():
    """Find device port automatically"""
    import serial.tools.list_ports
    
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if any(vid in port.hwid.upper() for vid in ['10C4:EA60', '1A86:7523']):
            print(f"Found device on: {{port.device}}")
            return port.device
    
    # Common ports
    common_ports = ['/dev/cu.usbserial-0001', '/dev/ttyUSB0', 'COM3']
    for port in common_ports:
        try:
            import serial
            ser = serial.Serial(port, BAUD_RATE, timeout=1)
            ser.close()
            return port
        except:
            continue
    
    return None

def upload_code(port):
    """Upload code to device"""
    print(f"Uploading to {{port}}...")
    
    # Write code to file
    with open('main.py', 'w') as f:
        f.write(DEVICE_CODE)
    
    # Upload using ampy
    try:
        cmd = f"ampy --port {{port}} --baud {{BAUD_RATE}} put main.py"
        result = subprocess.run(cmd.split(), capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ Code uploaded successfully!")
            return True
        else:
            print(f"✗ Upload failed: {{result.stderr}}")
            return False
    except Exception as e:
        print(f"✗ Upload error: {{e}}")
        return False

def main():
    port = sys.argv[1] if len(sys.argv) > 1 else find_device_port()
    
    if not port:
        port = input("Enter device port: ")
    
    if port and upload_code(port):
        print(f"{{DEVICE_NAME}} is ready!")
    else:
        print("Upload failed!")

if __name__ == "__main__":
    main()
'''
        return uploader_code

# Global instance
code_gen = CodeGenerator()
