# 8-Axis Servo Control System

Professional servo control interface for dual ClearCore controllers with Python GUI.

## Hardware Architecture
- **ClearCore Controller 1**: 192.168.10.171:8888 (Servos 1-4)  
- **ClearCore Controller 2**: 192.168.10.172:8890 (Servos 5-8)
- **Network**: Dedicated Ethernet subnet (192.168.10.x)
- **Interface**: Touchscreen-optimized GUI with numeric keypad

## Features
- ✅ 8-Axis servo control with dual ClearCore coordination
- ✅ Real-time UDP communication with position feedback
- ✅ Cross-platform support (Windows development, Raspberry Pi deployment)
- ✅ Advanced error handling and debug mode capabilities
- ✅ Professional touchscreen interface with numeric keypad
- ✅ Network resilience with partial connectivity support

## Quick Start

### Development (Windows)
1. Install Python dependencies: `pip install FreeSimpleGUI`
2. Run: `python Servo_Control_8_Axis.py`
3. Use "Continue Anyway" for GUI testing without hardware

### Production (Raspberry Pi)
1. Clone repository: `git clone <repo-url>`
2. Install dependencies: `pip install FreeSimpleGUI`
3. Configure network interface for 192.168.10.x subnet
4. Run: `python3 Servo_Control_8_Axis.py`

## Network Requirements
- Ethernet adapter configured for 192.168.10.x subnet
- Both ClearCore controllers powered and connected
- Network switch or direct connection to ClearCore boards

## File Structure
```
d:\Python\
├── Servo_Control_8_Axis.py        # Main application
├── .gitignore                     # Git ignore rules
├── README.md                      # This file
└── Git_Setup_Guide.md             # Step-by-step Git setup
```

## Version History
- **Rev 31**: 8-axis expansion with dual board architecture
- **Rev 30**: Enhanced network error handling and debug mode
- **Rev 29**: Cross-platform compatibility and Raspberry Pi support

## Authors
Greg Skovira

## License
Internal Use Only