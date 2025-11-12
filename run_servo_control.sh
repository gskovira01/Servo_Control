#!/bin/bash
# =============================================================================
# Servo Control System Launcher Script for Raspberry Pi
# =============================================================================
# 
# PURPOSE:
#   Launch the 8-axis servo control GUI application on Raspberry Pi
#   from the GitHub repository directory
#
# LOCATION: 
#   Place this script in /home/pi/Servo_Control/ directory
#   Make executable with: chmod +x run_servo_control.sh
#
# USAGE:
#   ./run_servo_control.sh                    # Run normally
#   ./run_servo_control.sh &                  # Run in background
#   nohup ./run_servo_control.sh &            # Run detached from terminal
#
# AUTHOR: Greg Skovira
# DATE: November 11, 2025
# =============================================================================

# Change to the correct directory
cd /home/pi/Servo_Control

# Check if the Python script exists
if [ ! -f "Servo_Control_8_Axis.py" ]; then
    echo "ERROR: Servo_Control_8_Axis.py not found in /home/pi/Servo_Control"
    echo "Make sure you have cloned the repository and are in the correct directory"
    exit 1
fi

# Activate existing Python 3.12 virtual environment
if [ -d "/home/pi/mypy/myvenv" ]; then
    echo "Activating Python 3.12 virtual environment..."
    source /home/pi/mypy/myvenv/bin/activate
    echo "Using Python: $(python --version)"
else
    echo "ERROR: Virtual environment not found at /home/pi/mypy/myvenv"
    exit 1
fi

# Set display for GUI applications (if running over SSH)
export DISPLAY=:0

# Add current directory to Python path
export PYTHONPATH="${PYTHONPATH}:/home/pi/Servo_Control"

echo "Starting Servo Control System..."
echo "Location: /home/pi/Servo_Control"
echo "Script: Servo_Control_8_Axis.py"
echo "Python: $(python3 --version)"
echo "Time: $(date)"
echo "=========================================="

# Run the servo control application (using activated virtual environment)
python Servo_Control_8_Axis.py

# Check exit status
if [ $? -eq 0 ]; then
    echo "Servo Control System exited normally"
else
    echo "Servo Control System exited with error code $?"
fi