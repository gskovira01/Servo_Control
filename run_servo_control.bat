@echo off
REM =============================================================================
REM Servo Control System Launcher Script for Windows
REM =============================================================================
REM 
REM PURPOSE:
REM   Launch the 8-axis servo control GUI application on Windows
REM   from the GitHub repository directory
REM
REM LOCATION: 
REM   Place this script in the Servo_Control directory
REM
REM USAGE:
REM   run_servo_control.bat
REM
REM AUTHOR: Greg Skovira
REM DATE: November 11, 2025
REM =============================================================================

cd /d "%~dp0"

echo Starting Servo Control System...
echo Location: %CD%
echo Script: Servo_Control_8_Axis.py
echo Time: %DATE% %TIME%
echo ==========================================

if not exist "Servo_Control_8_Axis.py" (
    echo ERROR: Servo_Control_8_Axis.py not found in current directory
    pause
    exit /b 1
)

python Servo_Control_8_Axis.py

if %ERRORLEVEL% neq 0 (
    echo Servo Control System exited with error code %ERRORLEVEL%
) else (
    echo Servo Control System exited normally
)

pause