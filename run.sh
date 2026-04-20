#!/bin/bash
set -e

# TinyCopyServer Quick Start for Linux/macOS

echo "Installing dependencies..."
python -m pip install -r requirements.txt

echo ""
echo "Starting TinyCopyServer..."
echo ""
echo "Server will be available at: http://localhost:8000"
echo "Admin Panel: http://localhost:8000 (lock icon)"
echo "Username: admin"
echo "Password: tcs2024secure"
echo ""

python main.py
