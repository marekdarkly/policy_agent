#!/bin/bash
# Activate virtual environment and run LaunchDarkly setup
# Usage: ./setup_ld.sh

cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    echo "📦 Installing dependencies..."
    pip install -q python-dotenv boto3 launchdarkly-server-sdk launchdarkly-server-sdk-ai langchain-core
else
    source venv/bin/activate
fi

echo "🔧 Running LaunchDarkly setup..."
python3 setup_ld.py

