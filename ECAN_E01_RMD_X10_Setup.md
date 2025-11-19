# ECAN E-0-1 to RMD-X10 Integration Guide
**Complete Setup for Galil DMC-4080 ↔ ECAN E-0-1 ↔ RMD-X10-P35-100-C-N**

---

## System Architecture
```
Galil DMC-4080 ←→ [Ethernet Switch] ←→ ECAN E-0-1 ←→ [CAN Bus] ←→ RMD-X10-P35-100-C-N
IP: 192.168.1.150       IP: 192.168.1.100    CAN ID: 0x141        Node ID: 1
```

---

## Hardware Connections

### ECAN E-0-1 Wiring:
```
ECAN E-0-1 Connections:
├── Power: 12-24V DC (check unit specs)
├── Ethernet: RJ45 to network switch
├── CAN1: Primary connection to RMD-X10
└── CAN2: Available for future expansion
```

### CAN Bus Wiring (ECAN to RMD-X10):
```
ECAN E-0-1 CAN1         RMD-X10-P35-100-C-N
CAN1_H         ←→       CAN_H (White wire)
CAN1_L         ←→       CAN_L (Blue wire)
GND            ←→       GND (Black wire)

Power Supply            RMD-X10-P35-100-C-N
24V+           ←→       Power+ (Red wire)
GND            ←→       GND (Black wire)
```

### Network Setup:
```
Ethernet Switch
├── Galil DMC-4080 (192.168.1.150)
└── ECAN E-0-1 (192.168.1.100)
```

---

## ECAN E-0-1 Configuration

### Step 1: Initial Access
```bash
# Connect to default IP (likely 192.168.1.100 or 192.168.1.200)
# Open web browser:
http://192.168.1.100

# Default credentials (check manual):
Username: admin
Password: admin (or 123456)
```

### Step 2: Network Configuration
```
IP Settings:
├── IP Address: 192.168.1.100
├── Subnet Mask: 255.255.255.0
├── Gateway: 192.168.1.1
└── DNS: 8.8.8.8
```

### Step 3: CAN Configuration
```
CAN1 Settings:
├── Baud Rate: 500000 (500kbps - RMD-X10 standard)
├── Mode: Transparent/Bridge Mode
├── Frame Format: Standard (11-bit ID)
└── Termination: Enable (if end node)

TCP Settings:
├── Port: 8080 (or check documentation)
├── Protocol: TCP Server
└── Buffer Size: Maximum available
```

### Step 4: Transparent Mode Setup
```
Data Format Options:
Option 1: Raw Binary (preferred)
Option 2: ASCII Hex (backup method)

Frame Format:
CAN ID (3 bytes) + DLC (1 byte) + Data (8 bytes)
Example: 141 08 A4 00 00 00 E8 03 00 00
```

---

## DMC Program for ECAN Integration

### Complete Galil DMC-4080 Program:
```dmc
REM =====================================================
REM RMD-X10 Control via ECAN E-0-1 Gateway
REM Galil DMC-4080 ↔ ECAN E-0-1 ↔ RMD-X10-P35-100-C-N
REM =====================================================

REM Variable Declarations
DIM ecan_handle as Integer
DIM position_target as Integer
DIM velocity_target as Integer
DIM current_position as Integer
DIM actuator_status as Integer
DIM command_string[20] as String
DIM response_string[20] as String

REM Network Configuration
#CONNECT_ECAN
REM Connect to ECAN E-0-1 gateway
IH "192.168.1.100",8080
ecan_handle = _IH
IF ecan_handle = -1
    MG "ECAN Connection Failed"
    EN
ENDIF
MG "Connected to ECAN Gateway, Handle:",ecan_handle
EN

REM RMD-X10 Command Functions
#ENABLE_MOTOR
REM Enable RMD-X10 motor
command_string = "14108880000000000000"  ' CAN ID 141, DLC 08, Enable command
IW ecan_handle,command_string
WT 100  ' Wait 100ms for response
MG "Motor Enabled"
EN

#DISABLE_MOTOR
REM Disable RMD-X10 motor
command_string = "14108800000000000000"  ' CAN ID 141, DLC 08, Disable command
IW ecan_handle,command_string
WT 100
MG "Motor Disabled"
EN

#MOVE_POSITION
REM Move to absolute position
REM Input: position_target (in encoder counts)
VAR position_hex[8]
position_hex[0] = position_target & $FF
position_hex[1] = (position_target >> 8) & $FF
position_hex[2] = (position_target >> 16) & $FF
position_hex[3] = (position_target >> 24) & $FF

REM Build position command: 0xA4 = Multi-turn position control
command_string = "141"  ' CAN ID
command_string = command_string + "08"  ' DLC = 8 bytes
command_string = command_string + "A4"  ' Position control command
command_string = command_string + "00000000"  ' Reserved bytes
command_string = command_string + "000003E8"  ' Max speed (1000 RPM)

IW ecan_handle,command_string
MG "Position Command Sent:",position_target
EN

#MOVE_VELOCITY
REM Velocity control
REM Input: velocity_target (in RPM * 100)
command_string = "141"  ' CAN ID
command_string = command_string + "08"  ' DLC = 8 bytes
command_string = command_string + "A2"  ' Velocity control command
command_string = command_string + "00"  ' Reserved
command_string = command_string + "0000"  ' Reserved
command_string = command_string + "00000000"  ' Velocity data

IW ecan_handle,command_string
MG "Velocity Command Sent:",velocity_target
EN

#READ_POSITION
REM Read current position from RMD-X10
command_string = "14108800000000000000"  ' Position read command
IW ecan_handle,command_string
WT 50  ' Wait for response

REM Read response (implementation depends on ECAN format)
response_string = _IR ecan_handle
IF response_string <> ""
    MG "Position Response:",response_string
ENDIF
EN

#HOME_ACTUATOR
REM Home the actuator to zero position
MG "Starting Home Sequence..."
JS #ENABLE_MOTOR
WT 500

REM Move to home position (0)
position_target = 0
JS #MOVE_POSITION
WT 2000  ' Wait for move to complete

MG "Homing Complete"
EN

#TEST_SEQUENCE
REM Test sequence for RMD-X10
MG "Starting RMD-X10 Test Sequence"

JS #ENABLE_MOTOR
WT 1000

REM Move to 90 degrees (9000 encoder counts assuming 100:1 ratio)
position_target = 9000
JS #MOVE_POSITION
WT 3000

REM Move to 180 degrees
position_target = 18000
JS #MOVE_POSITION
WT 3000

REM Return to home
position_target = 0
JS #MOVE_POSITION
WT 3000

JS #DISABLE_MOTOR
MG "Test Sequence Complete"
EN

REM Main Program
#MAIN
MG "RMD-X10 Control Program Started"
JS #CONNECT_ECAN
WT 1000

REM Run test sequence
JS #TEST_SEQUENCE

MG "Program Complete"
EN

REM Auto-start
XQ #MAIN
```

---

## RMD-X10 Command Reference

### Key CAN Commands:
```
Enable Motor:    CAN ID 0x141, Data: 88 00 00 00 00 00 00 00
Disable Motor:   CAN ID 0x141, Data: 80 00 00 00 00 00 00 00
Position Control: CAN ID 0x141, Data: A4 00 [Position] [Max Speed]
Velocity Control: CAN ID 0x141, Data: A2 00 [Velocity] 00 00 00 00
Read Position:   CAN ID 0x141, Data: 92 00 00 00 00 00 00 00
```

### Position Calculation:
```
RMD-X10-P35-100 Specifications:
- Gear Ratio: 100:1
- Encoder Resolution: Typically 16384 counts per revolution
- Full Rotation: 1,638,400 encoder counts (16384 * 100)

Position Examples:
- 90 degrees:  409,600 counts
- 180 degrees: 819,200 counts  
- 360 degrees: 1,638,400 counts
```

---

## Troubleshooting Guide

### Connection Issues:
```bash
# Test ECAN network connectivity
ping 192.168.1.100

# Test port connectivity
telnet 192.168.1.100 8080

# Check CAN bus with oscilloscope
# CAN_H: ~3.5V idle, ~2.5V dominant
# CAN_L: ~1.5V idle, ~2.5V dominant
```

### Common Problems:

**1. ECAN Not Responding:**
- Check power supply (12-24V DC)
- Verify Ethernet cable connection
- Try factory reset (check manual)
- Check default IP address

**2. CAN Communication Fails:**
- Verify CAN baud rate (500kbps)
- Check CAN termination resistors (120Ω)
- Verify wiring (CAN_H/CAN_L not swapped)
- Check RMD-X10 power supply

**3. RMD-X10 Not Moving:**
- Send enable command first
- Check position vs velocity commands
- Verify command format (hex encoding)
- Check for error responses

### Diagnostic Commands:
```dmc
REM Test ECAN connectivity
MG "ECAN Handle:",ecan_handle
MG "Network Status:",_IH

REM Monitor CAN traffic
REM Enable verbose mode if available
```

---

## Performance Optimization

### Reduce Latency:
1. **Use binary format** instead of ASCII hex
2. **Increase buffer sizes** in ECAN configuration
3. **Minimize command overhead** - batch operations
4. **Use dedicated network** - avoid network congestion

### Improve Reliability:
1. **Add command acknowledgment** checking
2. **Implement timeout handling** for commands
3. **Add position feedback** verification
4. **Use heartbeat monitoring** for connection status

---

## Expansion Options

### Future Capabilities:
```
Current Setup:     1x RMD-X10 on CAN1
Future Options:    
├── CAN1: Multiple RMD-X10 units (different IDs)
├── CAN2: Additional CAN devices
├── Sensors: Position feedback, limit switches
└── HMI: Touch screen interface via Ethernet
```

### Multi-Axis Configuration:
```dmc
REM Multiple RMD-X10 units
#MOVE_ALL_AXES
position_target = 18000  ' 180 degrees

REM Axis 1 (CAN ID 0x141)
command_string = "141" + "08" + "A4" + position_hex_string
JS #SEND_COMMAND

REM Axis 2 (CAN ID 0x142)  
command_string = "142" + "08" + "A4" + position_hex_string
JS #SEND_COMMAND

MG "All Axes Moving"
EN
```

---

## Next Steps After Setup:

1. **Test basic connectivity** between Galil and ECAN
2. **Verify CAN communication** with RMD-X10
3. **Run position test sequence** to validate operation
4. **Integrate with existing servo system** (Galil_8_Axis.dmc)
5. **Add safety interlocks** and error handling
6. **Document final configuration** for future reference

The ECAN E-0-1 should give you excellent performance for your servo control application!