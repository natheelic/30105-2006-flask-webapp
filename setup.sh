#!/bin/bash

echo "🚀 IoT Flask Web Application Setup Script"
echo "=========================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Install Python packages
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Test database connection
echo "🔗 Testing database connection..."
python3 -c "
from database import Database
from config import Config

print('📊 Testing MySQL connection...')
db = Database()
connection = db.get_connection()

if connection:
    print('✅ Database connection successful')
    connection.close()
    
    # Create tables
    print('📋 Creating database tables...')
    if db.create_tables():
        print('✅ Database tables created successfully')
    else:
        print('❌ Failed to create database tables')
        exit(1)
else:
    print('❌ Database connection failed')
    print('Please check your database configuration in config.py')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Setup completed successfully!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Run the application: python3 app.py"
    echo "2. Open your browser: http://localhost:4000"
    echo "3. Test the API endpoints"
    echo ""
    echo "🔧 Useful commands:"
    echo "- Health check: curl http://localhost:4000/api/health"
    echo "- Send test data: python3 test_app.py"
    echo ""
    echo "📱 ESP32 API endpoint: POST http://localhost:4000/api/esp32/data"
    echo ""
else
    echo "❌ Setup failed. Please check the error messages above."
    exit 1
fi
