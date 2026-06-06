#!/bin/bash

# Simple deployment for Render.com
echo "🚀 Preparing for Render deployment..."

# Create render.yaml (Render configuration)
cat > render.yaml << EOF
services:
  - type: web
    name: agile-backlog-api
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port \$PORT
    envVars:
      - key: DATABASE_URL
        sync: false
      - key: JWT_SECRET_KEY
        generateValue: true
      - key: APP_ENV
        value: production
EOF

# Create runtime.txt
echo "python-3.11" > runtime.txt

echo "✅ Created render.yaml and runtime.txt"
echo ""
echo "📋 Next: Push to GitHub, then deploy on Render"