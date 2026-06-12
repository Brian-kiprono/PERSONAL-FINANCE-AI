#!/bin/bash

# deploy.sh - Production deployment script

echo "🚀 Deploying FinanceAI..."

# Load environment variables
export $(cat .env | xargs)

# Install dependencies
pip install -r requirements.txt

# Set up database
python -c "from database import Database; Database()"

# Start with gunicorn for production
gunicorn -w 4 -b 0.0.0.0:5000 app:app

echo "✅ Deployment complete!"