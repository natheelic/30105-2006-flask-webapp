
# วิธีการติดตั้งและใช้งาน

## 1. ติดตั้ง dependencies

pip install -r requirements.txt

## 2. รันแอปพลิเคชัน

python app.py

## 3. ทดสอบ API

### Health check

curl http://localhost:4000/api/health

### Send test data

curl -X POST http://localhost:4000/api/esp32/data \
  -H "Content-Type: application/json" \
  -d '{"temperature": 25.5, "humidity": 60.2, "device_id": "ESP32_001"}'