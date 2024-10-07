#! /bin/bash

echo "Installing Python dependencies..."
pip install fastapi[all] uvicorn python-jose[cryptography] passlib[bcrypt] python-multipart python-dotenv email-validator

echo "Running Falcon Panel Development Server"
echo "Falcon Panel Development Server is running on http://localhost:3000"

cd web/falcon
npm run dev &

cd server
python3 run.py

#-------------------------#
# how to run this script?
# chmod +x run.sh
# ./run.sh
#-------------------------#