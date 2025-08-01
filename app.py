from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/esp32')
def esp32():
    return render_template('esp32.html')

@app.route('/add-data')
def add_data():
    return render_template('add_data.html')

@app.route('/submit-data', methods=['POST'])
def submit_data():
    data_from_input = request.form['data_input']
    return render_template('submit_data.html', data=data_from_input)

@app.route('/api/esp32/data', methods=['POST'])
def api_esp32_data():
    data = request.json
    print("📡 Received from ESP32:", data)
    return jsonify({"status": "success", "received": data}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000, debug=True)
