#!/bin/bash
echo "🚀 Installing Flask IoT Web Application..."

# Install Python dependencies
pip install -r requirements.txt

# Create database if not exists
python -c "
from database import Database
db = Database()
print('📊 Creating database tables...')
if db.create_tables():
    print('✅ Database initialized successfully')
else:
    print('❌ Failed to initialize database')
"

echo "✨ Installation completed!"
echo "Run: python app.py"