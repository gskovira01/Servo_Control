#!/usr/bin/env python3
"""
=============================================================================
Servo Control System Python Launcher
=============================================================================

PURPOSE:
    Cross-platform Python launcher for the 8-axis servo control GUI
    Handles environment setup and error checking

LOCATION: 
    Place in /home/pi/Servo_Control/ directory on Raspberry Pi
    Make executable with: chmod +x launch_servo_control.py

USAGE:
    python3 launch_servo_control.py
    ./launch_servo_control.py              # If made executable

AUTHOR: Greg Skovira
DATE: November 11, 2025
=============================================================================
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.absolute()
    servo_script = script_dir / "Servo_Control_8_Axis.py"
    
    print("=" * 50)
    print("Servo Control System Launcher")
    print("=" * 50)
    print(f"Location: {script_dir}")
    print(f"Python: {sys.version}")
    print(f"Platform: {sys.platform}")
    
    # Change to the script directory
    os.chdir(script_dir)
    print(f"Working Directory: {os.getcwd()}")
    
    # Check if the servo script exists
    if not servo_script.exists():
        print(f"\nERROR: {servo_script.name} not found!")
        print("Make sure you are in the correct directory with the servo control files.")
        return 1
    
    # Check required modules
    required_modules = ['socket', 'threading', 'tkinter']
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print(f"\nWARNING: Missing modules: {', '.join(missing_modules)}")
        print("Install with: sudo apt-get install python3-tkinter")
    
    print(f"\nStarting: {servo_script.name}")
    print("-" * 50)
    
    try:
        # Run the servo control script
        result = subprocess.run([sys.executable, str(servo_script)], 
                              cwd=script_dir)
        
        print("-" * 50)
        if result.returncode == 0:
            print("Servo Control System exited normally")
        else:
            print(f"Servo Control System exited with code {result.returncode}")
            
        return result.returncode
        
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
        return 130
    except Exception as e:
        print(f"\nError launching servo control: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)