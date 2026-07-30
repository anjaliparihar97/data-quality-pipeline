#!/bin/bash
echo "============================================="
echo " Statista Data Quality Audit Engine"
echo " Author: Anjali Parihar"
echo "============================================="
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt
echo ""
echo "Launching app..."
echo "Open your browser at: http://localhost:8501"
echo ""
streamlit run app.py
