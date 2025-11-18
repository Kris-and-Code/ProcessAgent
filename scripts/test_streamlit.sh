#!/bin/bash
# Test script for Streamlit UI
# This script will start Streamlit and provide instructions

echo "🧩 ProcessAgent Streamlit UI Test"
echo "=================================="
echo ""
echo "Starting Streamlit server..."
echo "The UI will open in your browser automatically."
echo ""
echo "Test Steps:"
echo "1. Enter goal: 'Prepare drilling operation for aluminum part'"
echo "2. Select material: 'Aluminum 6061'"
echo "3. Click 'Generate Plan'"
echo "4. Verify Plan and G-Code sections appear"
echo "5. Check validation status"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd "$(dirname "$0")/.."
source venv/bin/activate
streamlit run process_agent/ui/app.py

