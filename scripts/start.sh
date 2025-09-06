#!/bin/bash

echo "Starting Personal Stylist AI..."
echo "==============================="

# Set default base path if not provided
export APP_BASE_PATH=${APP_BASE_PATH:-/app}

echo "Using base path: $APP_BASE_PATH"

# Create data directories if they don't exist
mkdir -p "$APP_BASE_PATH/data/database"
mkdir -p "$APP_BASE_PATH/data/users"
mkdir -p "$APP_BASE_PATH/uploads/clothing"
mkdir -p "$APP_BASE_PATH/uploads/body_analysis"
mkdir -p "$APP_BASE_PATH/uploads/temp"
mkdir -p "$APP_BASE_PATH/models/cache"

echo "✓ Directory structure created"

# Set proper permissions
chmod 755 "$APP_BASE_PATH/data" 2>/dev/null || true
chmod 755 "$APP_BASE_PATH/uploads" 2>/dev/null || true

# Initialize database if it doesn't exist or if initialization is forced
DB_FILE="$APP_BASE_PATH/data/database/stylist.db"
if [ ! -f "$DB_FILE" ] || [ "$FORCE_DB_INIT" = "true" ]; then
    echo "Initializing database..."
    python "$APP_BASE_PATH/scripts/init_database.py"
    
    if [ $? -eq 0 ]; then
        echo "✓ Database initialization successful"
    else
        echo "⚠ Database initialization had issues, but continuing..."
        echo "The application will attempt to initialize the database on startup"
    fi
else
    echo "✓ Database already exists"
fi

# Set database permissions
if [ -f "$DB_FILE" ]; then
    chmod 644 "$DB_FILE" 2>/dev/null || true
    echo "✓ Database permissions set"
fi

# Check for required AI models and dependencies
echo "Checking AI models and dependencies..."
python "$APP_BASE_PATH/scripts/check_models.py"

if [ $? -eq 0 ]; then
    echo "✓ AI dependencies verified"
else
    echo "⚠ Some AI dependencies may be missing"
    echo "The application will still start, but some features may be limited"
fi

# Environment variables for Streamlit
export STREAMLIT_SERVER_HEADLESS=${STREAMLIT_SERVER_HEADLESS:-true}
export STREAMLIT_SERVER_ADDRESS=${STREAMLIT_SERVER_ADDRESS:-0.0.0.0}
export STREAMLIT_SERVER_PORT=${STREAMLIT_SERVER_PORT:-8501}
export PYTHONUNBUFFERED=${PYTHONUNBUFFERED:-1}

# Security and performance settings
export STREAMLIT_SERVER_ENABLE_CORS=${STREAMLIT_SERVER_ENABLE_CORS:-false}
export STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=${STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION:-true}

echo "✓ Environment configured"
echo ""
echo "Starting Streamlit application..."
echo "Web interface will be available at: http://localhost:$STREAMLIT_SERVER_PORT"
echo ""

# Change to the application directory
cd "$APP_BASE_PATH"

# Start the Streamlit application with error handling
streamlit run src/main.py \
    --server.address="$STREAMLIT_SERVER_ADDRESS" \
    --server.port="$STREAMLIT_SERVER_PORT" \
    --server.headless="$STREAMLIT_SERVER_HEADLESS" \
    --server.enableCORS="$STREAMLIT_SERVER_ENABLE_CORS" \
    --server.enableXsrfProtection="$STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION" \
    --browser.gatherUsageStats=false