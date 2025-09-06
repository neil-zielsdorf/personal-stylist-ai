#!/bin/bash

echo "Starting Personal Stylist AI..."
echo "==============================="

# Create data directories if they don't exist
mkdir -p /app/data/database
mkdir -p /app/data/users
mkdir -p /app/uploads/clothing
mkdir -p /app/uploads/body_analysis
mkdir -p /app/uploads/temp

# Initialize database if it doesn't exist
if [ ! -f "/app/data/database/stylist.db" ]; then
    echo "Initializing database..."
    python /app/scripts/init_database.py
fi

# Set permissions
chmod 755 /app/data
chmod 755 /app/uploads
chmod 644 /app/data/database/stylist.db 2>/dev/null || true

# Check for required models
echo "Checking AI models..."
python /app/scripts/check_models.py

echo "Starting Streamlit application..."
streamlit run /app/src/main.py --server.address=0.0.0.0 --server.port=8501