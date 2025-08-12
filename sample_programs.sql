-- สร้างโปรแกรมตัวอย่างใน ESP32 programs table
INSERT INTO esp32_programs (program_name, description, program_code, version, created_by) VALUES 
('Basic Sensor Reader', 'อ่านค่าเซนเซอร์พื้นฐานและส่งข้อมูลผ่าน WiFi', 
'#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// WiFi credentials
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Server endpoint
const char* serverURL = "http://your-server.com/api/esp32/data";

// Pin definitions
#define TEMP_SENSOR_PIN A0
#define HUMIDITY_SENSOR_PIN A1
#define LIGHT_SENSOR_PIN A2

void setup() {
    Serial.begin(115200);
    
    // Initialize pins
    pinMode(TEMP_SENSOR_PIN, INPUT);
    pinMode(HUMIDITY_SENSOR_PIN, INPUT);
    pinMode(LIGHT_SENSOR_PIN, INPUT);
    
    // Connect to WiFi
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.println("Connecting to WiFi...");
    }
    Serial.println("WiFi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
}

void loop() {
    // Read sensor values
    float temperature = analogRead(TEMP_SENSOR_PIN) * (100.0 / 4095.0);
    float humidity = analogRead(HUMIDITY_SENSOR_PIN) * (100.0 / 4095.0);
    float light = analogRead(LIGHT_SENSOR_PIN);
    
    // Create JSON payload
    DynamicJsonDocument doc(1024);
    doc["device_id"] = "ESP32_001";
    doc["temperature"] = temperature;
    doc["humidity"] = humidity;
    doc["light"] = light;
    doc["timestamp"] = millis();
    
    String jsonString;
    serializeJson(doc, jsonString);
    
    // Send data to server
    sendDataToServer(jsonString);
    
    // Wait 30 seconds before next reading
    delay(30000);
}

void sendDataToServer(String data) {
    if (WiFi.status() == WL_CONNECTED) {
        HTTPClient http;
        http.begin(serverURL);
        http.addHeader("Content-Type", "application/json");
        
        int httpResponseCode = http.POST(data);
        
        if (httpResponseCode > 0) {
            String response = http.getString();
            Serial.println("Server response: " + response);
        } else {
            Serial.println("Error sending data: " + String(httpResponseCode));
        }
        
        http.end();
    }
}', '1.0.0', 'System'),

('WiFi Weather Station', 'สถานีตรวจอากาศแบบ WiFi พร้อม OLED Display', 
'#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <DHT.h>

// Display settings
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// DHT sensor
#define DHT_PIN 2
#define DHT_TYPE DHT22
DHT dht(DHT_PIN, DHT_TYPE);

// WiFi credentials
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* serverURL = "http://your-server.com/api/esp32/data";

// Variables
unsigned long lastUpdate = 0;
const unsigned long updateInterval = 60000; // 1 minute

void setup() {
    Serial.begin(115200);
    
    // Initialize DHT sensor
    dht.begin();
    
    // Initialize OLED display
    if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
        Serial.println(F("SSD1306 allocation failed"));
        for(;;);
    }
    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(0,0);
    display.println("Starting...");
    display.display();
    
    // Connect to WiFi
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        display.print(".");
        display.display();
    }
    
    display.clearDisplay();
    display.setCursor(0,0);
    display.println("WiFi Connected!");
    display.println(WiFi.localIP());
    display.display();
    delay(2000);
}

void loop() {
    unsigned long currentTime = millis();
    
    // Read sensors
    float temperature = dht.readTemperature();
    float humidity = dht.readHumidity();
    float light = analogRead(A0);
    
    // Update display
    updateDisplay(temperature, humidity, light);
    
    // Send data to server every minute
    if (currentTime - lastUpdate >= updateInterval) {
        sendSensorData(temperature, humidity, light);
        lastUpdate = currentTime;
    }
    
    delay(1000);
}

void updateDisplay(float temp, float hum, float light) {
    display.clearDisplay();
    display.setCursor(0,0);
    display.setTextSize(1);
    display.println("Weather Station");
    display.println("================");
    
    display.setTextSize(1);
    display.print("Temp: ");
    display.print(temp);
    display.println(" C");
    
    display.print("Humidity: ");
    display.print(hum);
    display.println(" %");
    
    display.print("Light: ");
    display.println(light);
    
    display.print("WiFi: ");
    display.println(WiFi.status() == WL_CONNECTED ? "OK" : "ERROR");
    
    display.display();
}

void sendSensorData(float temp, float hum, float light) {
    if (WiFi.status() == WL_CONNECTED) {
        HTTPClient http;
        http.begin(serverURL);
        http.addHeader("Content-Type", "application/json");
        
        DynamicJsonDocument doc(1024);
        doc["device_id"] = "ESP32_WEATHER_001";
        doc["temperature"] = temp;
        doc["humidity"] = hum;
        doc["light"] = light;
        doc["location"] = "Home Station";
        
        String jsonString;
        serializeJson(doc, jsonString);
        
        int httpResponseCode = http.POST(jsonString);
        
        if (httpResponseCode > 0) {
            Serial.println("Data sent successfully");
        } else {
            Serial.println("Failed to send data");
        }
        
        http.end();
    }
}', '1.0.0', 'System'),

('Smart Garden Monitor', 'ระบบตรวจสอบสวนอัจฉริยะพร้อมควบคุมการรดน้ำ', 
'#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// WiFi credentials
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* serverURL = "http://your-server.com/api/esp32/data";

// Pin definitions
#define SOIL_MOISTURE_PIN A0
#define LIGHT_SENSOR_PIN A1
#define WATER_PUMP_PIN 5
#define LED_PIN 2

// Thresholds
#define SOIL_MOISTURE_THRESHOLD 30  // Percentage
#define WATERING_DURATION 5000      // 5 seconds

// Variables
unsigned long lastWatering = 0;
unsigned long wateringCooldown = 300000; // 5 minutes
bool automaticMode = true;

void setup() {
    Serial.begin(115200);
    
    // Initialize pins
    pinMode(SOIL_MOISTURE_PIN, INPUT);
    pinMode(LIGHT_SENSOR_PIN, INPUT);
    pinMode(WATER_PUMP_PIN, OUTPUT);
    pinMode(LED_PIN, OUTPUT);
    
    digitalWrite(WATER_PUMP_PIN, LOW);
    digitalWrite(LED_PIN, HIGH); // Status LED on
    
    // Connect to WiFi
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.println("Connecting to WiFi...");
        digitalWrite(LED_PIN, !digitalRead(LED_PIN)); // Blink LED
    }
    
    digitalWrite(LED_PIN, HIGH); // Solid LED when connected
    Serial.println("Smart Garden Monitor Ready!");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
}

void loop() {
    // Read sensors
    float soilMoisture = readSoilMoisture();
    float lightLevel = analogRead(LIGHT_SENSOR_PIN);
    float temperature = 25.0; // Mock temperature (add real sensor if needed)
    
    // Check if watering is needed
    if (automaticMode && needsWatering(soilMoisture)) {
        waterPlants();
    }
    
    // Send data to server
    sendGardenData(soilMoisture, lightLevel, temperature);
    
    // Status indication
    if (soilMoisture < SOIL_MOISTURE_THRESHOLD) {
        blinkLED(3); // Blink 3 times for low moisture
    }
    
    delay(30000); // Send data every 30 seconds
}

float readSoilMoisture() {
    int rawValue = analogRead(SOIL_MOISTURE_PIN);
    // Convert to percentage (adjust based on your sensor calibration)
    float moisture = map(rawValue, 0, 4095, 100, 0); // Inverted: wet=high value, dry=low value
    return constrain(moisture, 0, 100);
}

bool needsWatering(float moisture) {
    unsigned long currentTime = millis();
    
    return (moisture < SOIL_MOISTURE_THRESHOLD && 
            (currentTime - lastWatering) > wateringCooldown);
}

void waterPlants() {
    Serial.println("Watering plants...");
    
    digitalWrite(WATER_PUMP_PIN, HIGH);
    delay(WATERING_DURATION);
    digitalWrite(WATER_PUMP_PIN, LOW);
    
    lastWatering = millis();
    
    Serial.println("Watering complete");
}

void blinkLED(int times) {
    for (int i = 0; i < times; i++) {
        digitalWrite(LED_PIN, LOW);
        delay(200);
        digitalWrite(LED_PIN, HIGH);
        delay(200);
    }
}

void sendGardenData(float moisture, float light, float temp) {
    if (WiFi.status() == WL_CONNECTED) {
        HTTPClient http;
        http.begin(serverURL);
        http.addHeader("Content-Type", "application/json");
        
        DynamicJsonDocument doc(1024);
        doc["device_id"] = "ESP32_GARDEN_001";
        doc["temperature"] = temp;
        doc["humidity"] = moisture; // Using moisture as humidity field
        doc["light"] = light;
        doc["soil_moisture"] = moisture;
        doc["location"] = "Garden Area";
        
        // Additional garden-specific data
        JsonObject rawData = doc.createNestedObject("raw_data");
        rawData["last_watering"] = lastWatering;
        rawData["automatic_mode"] = automaticMode;
        rawData["needs_watering"] = needsWatering(moisture);
        rawData["pump_status"] = digitalRead(WATER_PUMP_PIN);
        
        String jsonString;
        serializeJson(doc, jsonString);
        
        int httpResponseCode = http.POST(jsonString);
        
        if (httpResponseCode > 0) {
            Serial.println("Garden data sent successfully");
            
            // Check for server commands (optional)
            String response = http.getString();
            parseServerResponse(response);
        } else {
            Serial.println("Failed to send garden data");
        }
        
        http.end();
    }
}

void parseServerResponse(String response) {
    DynamicJsonDocument doc(512);
    deserializeJson(doc, response);
    
    // Check for remote commands
    if (doc.containsKey("commands")) {
        JsonObject commands = doc["commands"];
        
        if (commands.containsKey("water_now") && commands["water_now"]) {
            Serial.println("Remote watering command received");
            waterPlants();
        }
        
        if (commands.containsKey("automatic_mode")) {
            automaticMode = commands["automatic_mode"];
            Serial.println("Automatic mode: " + String(automaticMode ? "ON" : "OFF"));
        }
    }
}', '1.0.0', 'System');
