# Flask Web App with ESP32 API Integration

โปรเจกต์นี้เป็น Web Application ที่พัฒนาโดยใช้ Flask พร้อมฟีเจอร์:

## 📌 ฟีเจอร์หลัก

- 🧭 มี Navbar สำหรับนำทางทุกหน้า
- 🌐 หน้าเว็บ: Home, ESP32, Add Data, Submit Data
- ✉️ ฟอร์มส่งข้อมูลจากผู้ใช้
- 🔌 รองรับการเชื่อมต่อกับ ESP32 ผ่าน API (รับข้อมูล JSON)
- 🎨 ใช้ CSS ภายนอก (ใน static/style.css)

## 🗂 โครงสร้างโฟลเดอร์

```
flask-webapp/
├── static/
│   └── style.css
├── templates/
│   ├── base.html
│   ├── home.html
│   ├── esp32.html
│   ├── add_data.html
│   └── submit_data.html
├── app.py
└── README.md
```

## 🚀 วิธีใช้งาน

### 1. ติดตั้ง Flask

```bash
pip install flask
```

### 2. รันแอป

```bash
python app.py
```

### 3. เปิดเว็บ

เข้าใช้งานที่: [http://localhost:4000](http://localhost:4000)

## 🔌 ESP32 Integration

ESP32 สามารถส่งข้อมูลผ่าน HTTP POST เช่น:

```http
POST /api/esp32/data HTTP/1.1
Content-Type: application/json

{
  "temperature": 32.5,
  "humidity": 58
}
```

**Response:**

```json
{
  "status": "success",
  "received": {
    "temperature": 32.5,
    "humidity": 58
  }
}
```

## 👤 ผู้พัฒนา

Nathee Srina
