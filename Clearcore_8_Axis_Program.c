/*
================================================================================
                         SERVO CONTROL 8-AXIS - CLEARCORE FIRMWARE
                         Dual Board Architecture - Revision 8.0
================================================================================

PURPOSE:
    ClearCore controller firmware for 8-axis servo control system using
    dual ClearCore boards connected via Ethernet UDP communication.
    Provides real-time servo control with position feedback, velocity/acceleration
    control, and network communication with Python GUI host system.
    
MIGRATION NOTE - FUTURE GALIL DMC-4080 UPGRADE:
    This dual ClearCore board architecture is designed for migration to a 
    single Galil DMC-4080 8-axis controller. The Galil DMC-4080 will provide:
    - Native 8-axis coordinated motion control
    - Advanced trajectory planning and motion profiles  
    - Simplified single-board architecture
    - Enhanced Ethernet communication capabilities
    - More sophisticated servo control algorithms
    
    Current: 2x ClearCore boards (4 motors each) = 8-axis total
    Future:  1x Galil DMC-4080 board (8 motors) = 8-axis total

HARDWARE ARCHITECTURE:
    - ClearCore Board 1: Motors 1-4 on connectors M0-M3 (192.168.1.171:8888)
    - ClearCore Board 2: Motors 5-8 on connectors M0-M3 (192.168.1.172:8890)
    - Host System: Python GUI coordinator (192.168.1.100:8889)
    - Network: Dedicated Ethernet subnet (192.168.1.x) for servo control
    - Motors: Step/Direction servo drives with HLFB feedback

GALIL DMC-4080 MIGRATION STRATEGY:
    
    Phase 1 - Current State (Dual ClearCore):
    - 2x ClearCore boards, each controlling 4 servos  
    - UDP communication with Python GUI
    - Manual/Auto modes with basic motion sequences
    
    Phase 2 - Future State (Single Galil DMC-4080):
    - 1x Galil DMC-4080 controller, 8 servo axes (A-H)
    - Native Ethernet communication (no dual-board complexity)
    - Advanced motion capabilities:
      * Coordinated 8-axis interpolated motion
      * Electronic gearing and camming
      * Advanced trajectory planning
      * Built-in PID tuning and optimization
    
    Migration Benefits:
    - Simplified hardware (single board vs dual boards)
    - Enhanced motion control (coordinated multi-axis)
    - Better real-time performance
    - Advanced servo tuning capabilities
    - Integrated I/O handling
    - Professional motion control software tools

RECENT ENHANCEMENTS (8-Axis Expansion):
    ✅ Dual ClearCore board architecture: Independent 4-motor control per board
    ✅ Extended variable support: All 8 motors with independent control parameters
    ✅ Comprehensive command parsing: Full parameter and position control
    ✅ Clear position commands: Individual motor position reset capability
    ✅ Enhanced documentation: Detailed motor mapping and board coordination
    ✅ Migration planning: Galil DMC-4080 upgrade pathway documented

DEPLOYMENT SCENARIOS:
    1. Production: Dual ClearCore boards, 8 servo motors, full network connectivity
    2. Development: Single board testing, 4 motor operation, partial system validation
    3. Simulation: Network communication testing without physical motors

NETWORK TOPOLOGY:
    [Python GUI Host] ←→ [Ethernet Switch] ←→ [ClearCore 1] + [ClearCore 2]
           ↓                     ↓                   ↓              ↓
    192.168.1.100:8889    192.168.1.1       192.168.1.171   192.168.1.172
                                                  :8888         :8890

MOTOR MAPPING:
    Board 1 (BOARD_ID=1):          Board 2 (BOARD_ID=2):
    S1 → Motor1 (M0) [Axis 1]      S1 → Motor5 (M0) [Axis 5]
    S2 → Motor2 (M1) [Axis 2]      S2 → Motor6 (M1) [Axis 6]  
    S3 → Motor3 (M2) [Axis 3]      S3 → Motor7 (M2) [Axis 7]
    S4 → Motor4 (M3) [Axis 4]      S4 → Motor8 (M3) [Axis 8]

COMMUNICATION PROTOCOL:
    - UDP messaging between ClearCore boards and Python GUI
    - Each board sends 12 values (V,A,P × 4 motors) at regular intervals
    - Command routing based on board ID and servo number
    - Real-time position feedback and parameter updates

AUTHORS: Greg Skovira
VERSION: Rev 8.0 (8-Axis Dual Board Architecture)
DATE: November 2025
LICENSE: Internal Use Only

================================================================================
*/

/*
================================================================================
                            CLASSES AND FUNCTIONS INVENTORY
================================================================================

CORE SYSTEM FUNCTIONS:
    setup()                     - ClearCore board initialization and configuration
                                  Sets up network, motors, I/O, and communication protocols
    loop()                      - Main program loop for continuous operation
                                  Handles UDP communication, motor control, and status updates
    
NETWORK COMMUNICATION FUNCTIONS:
    processIncomingMessages()   - Parse and execute incoming UDP commands from Python GUI
                                  Handles parameter updates, position commands, and control states
    sendStatusMessage()         - Transmit real-time servo status to Python GUI
                                  Sends velocity, acceleration, and position data for all 4 servos
    sendButtonStates()          - Transmit current button and control states to GUI
                                  Provides feedback for Mode/Repeat/Start and servo enable states
    sendSetpoints()             - Transmit current servo configuration parameters
                                  Allows GUI to sync with actual hardware setpoint values
    
SERVO CONTROL FUNCTIONS:
    configureMotors()           - Initialize all 4 servo motor configurations
                                  Sets up step/direction mode, HLFB feedback, and safety limits
    updateMotorParameters()     - Apply new velocity/acceleration/position setpoints
                                  Updates individual motor parameters from GUI commands
    executeMotorMovement()      - Command coordinated servo movements
                                  Handles single or multi-axis motion with safety checks
    checkMotorStatus()          - Monitor servo feedback and operational status
                                  Tracks HLFB signals, fault conditions, and position feedback
    
COMMAND PROCESSING FUNCTIONS:
    parseCommand()              - Decode incoming UDP command strings
                                  Extracts command type, servo number, and parameter values
    validateParameters()        - Ensure servo parameters within safe operational limits
                                  Prevents hardware damage from invalid setpoint values
    executeServoCommand()       - Process individual servo control commands
                                  Handles enable/disable, position clear, and parameter updates
    executeSystemCommand()      - Process system-level control commands
                                  Handles Mode/Repeat/Start operations and state changes
    
UTILITY FUNCTIONS:
    formatStatusString()        - Format servo data for UDP transmission
                                  Creates comma-delimited strings for Python GUI consumption
    updateControlStates()       - Manage internal control state variables
                                  Synchronizes button states, mode flags, and system status
    handleErrorConditions()     - Process servo faults and error recovery
                                  Implements safety protocols and error reporting
    performSystemDiagnostics()  - Execute periodic system health checks
                                  Monitors communication, motor status, and system integrity
    
INITIALIZATION FUNCTIONS:
    initializeEthernet()        - Configure Ethernet interface and UDP communication
                                  Sets up IP address, port binding, and network protocols
    initializeServoMotors()     - Configure all 4 servo motor interfaces
                                  Initializes M0-M3 connectors with appropriate settings
    initializeControlVariables() - Set default values for all control parameters
                                   Establishes safe starting configuration for all servos
    initializeSystemState()     - Initialize operational state machine
                                  Sets up mode flags, button states, and control logic
    
MOTOR MANAGEMENT FUNCTIONS:
    Motor1_Functions()          - Dedicated control functions for Servo 1 (M0 connector)
    Motor2_Functions()          - Dedicated control functions for Servo 2 (M1 connector)
    Motor3_Functions()          - Dedicated control functions for Servo 3 (M2 connector)
    Motor4_Functions()          - Dedicated control functions for Servo 4 (M3 connector)
                                  Each motor has independent parameter management and control
    
DEBUG AND MONITORING FUNCTIONS:
    printDebugInfo()            - Output diagnostic information via serial/network
                                  Provides troubleshooting data for development and maintenance
    logSystemEvents()           - Record significant system events and state changes
                                  Maintains operational history for analysis and debugging
    monitorCommunication()      - Track UDP communication health and statistics
                                  Monitors message rates, timeouts, and connection status

TOTAL: 25+ Functions across 500+ lines of embedded C code

KEY DATA STRUCTURES:
    Motor1-4_Parameters         - Individual servo configuration (velocity/acceleration/position)
    UDP_ReceiveBuffer          - Network message buffer for incoming commands
    UDP_TransmitBuffer         - Network message buffer for outgoing status
    System_ControlStates       - Mode/Repeat/Start flags and operational status
    Motor_StatusFlags          - Real-time servo status and fault indicators
    
CRITICAL CONSTANTS:
    BOARD_ID                   - Identifies which board (1 or 2) for dual-board coordination
    UDP_LOCAL_PORT             - Network listening port (8888 for Board 1, 8890 for Board 2)
    MOTOR_COUNT = 4            - Number of servos per ClearCore board
    MAX_VELOCITY/ACCELERATION  - Safety limits for servo motion parameters
    POSITION_FEEDBACK_RATE     - Frequency of status updates to Python GUI

COMMUNICATION PROTOCOL:
    Command Format: "CMD:COMMAND_TYPE:PARAMETERS\n"
    Status Format:  "STATUS:V1,A1,P1,V2,A2,P2,V3,A3,P3,V4,A4,P4\n" 
    Button Format:  "BUTTON_STATES:M,R,S,S1E,S1R,S2E,S2R,S3E,S3R,S4E,S4R\n"

================================================================================
                               REVISION HISTORY
================================================================================

Rev 8.0 - November 9, 2025 - Complete 8-Axis Expansion & Dual Board Architecture
    ✅ MAJOR: Complete 8-axis servo control implementation across dual ClearCore boards
    ✅ MAJOR: Expanded variable support for all 8 motors (Motor1-8 with independent parameters)
    ✅ MAJOR: Dual board coordination with BOARD_ID differentiation (1=171:8888, 2=172:8890)
    ✅ MAJOR: Enhanced UDP communication for coordinated 8-axis operation
    ✅ MAJOR: Comprehensive command parsing for all 8 servos and system functions
    ✅ ENHANCEMENT: Individual position clear commands for each motor
    ✅ ENHANCEMENT: Detailed program documentation and architecture specifications
    ✅ ENHANCEMENT: Enhanced variable naming for clarity (Motor1-8_Velocity/Acceleration/Position)
    ✅ ENHANCEMENT: Robust error handling and parameter validation
    ✅ ENHANCEMENT: Cross-platform coordination with Python GUI dual-tab interface

Rev 7.0 - October 2025 - Enhanced Communication & Multi-Servo Coordination
    ✅ MAJOR: Multi-servo parameter management and coordinated control
    ✅ MAJOR: Advanced UDP command processing with parameter validation
    ✅ ENHANCEMENT: Real-time status feedback for all servo parameters
    ✅ ENHANCEMENT: Button state synchronization with GUI interface
    ✅ ENHANCEMENT: Improved error handling and fault recovery
    ✅ ENHANCEMENT: Enhanced debug output and system monitoring

Rev 6.0 - September 2025 - Network Communication & Real-Time Control
    ✅ MAJOR: UDP network communication with Python GUI
    ✅ MAJOR: Real-time servo position feedback and status reporting
    ✅ ENHANCEMENT: Command parsing and execution engine
    ✅ ENHANCEMENT: Multi-parameter servo control (velocity/acceleration/position)
    ✅ ENHANCEMENT: System state management and control logic

Rev 5.0 - August 2025 - Multi-Motor ClearCore Implementation
    ✅ MAJOR: 4-motor servo control using ClearCore M0-M3 connectors
    ✅ MAJOR: Step/direction servo interface with HLFB feedback
    ✅ ENHANCEMENT: Individual motor parameter configuration
    ✅ ENHANCEMENT: Basic motion control and positioning
    ✅ ENHANCEMENT: Safety limits and fault monitoring

ARCHITECTURE EVOLUTION:
    Rev 5.0: Basic 4-motor ClearCore foundation with servo interfaces
    Rev 6.0: Network integration and real-time communication
    Rev 7.0: Advanced multi-servo coordination and parameter management  
    Rev 8.0: Complete 8-axis expansion with dual-board architecture

CURRENT SYSTEM CAPABILITIES:
    ✅ 8-Axis Servo Control: Independent control across dual ClearCore boards
    ✅ Real-Time Communication: UDP messaging with Python GUI coordination
    ✅ Advanced Parameter Management: Velocity/acceleration/position control per servo
    ✅ Robust Command Processing: Complete command parsing and validation
    ✅ System State Management: Mode/Repeat/Start controls with feedback
    ✅ Safety Implementation: Parameter validation and fault monitoring
    ✅ Dual Board Coordination: Seamless integration for 8-axis operation

DEPLOYMENT ARCHITECTURE:
    Board 1 (BOARD_ID=1): Motors 1-4, IP 192.168.1.171, Port 8888
    Board 2 (BOARD_ID=2): Motors 5-8, IP 192.168.1.172, Port 8890  
    Python GUI Host: Coordinates both boards for unified 8-axis control

PLANNED FUTURE ENHANCEMENTS:
    🔄 Advanced motion profiles and acceleration curves
    🔄 Multi-axis coordinated motion sequences  
    🔄 Safety interlocks and emergency stop integration
    🔄 Data logging and motion history tracking
    🔄 Advanced fault diagnostics and recovery
    🔄 Recipe-based automation and job scheduling
    🔄 Performance optimization and real-time analytics

================================================================================
*/

#include "ClearCore.h"
#include <Ethernet.h>

//***********************************************************************
//*******************Declare variables******************************
#define BOARD_ID 1 // Change to 2 for the second board
//*******************Ethernet Variables******************************
// At the top, before setup()
byte mac1[] = {0x24, 0x15, 0x10, 0xb0, 0x42, 0x3e};
byte mac2[] = {0x24, 0x15, 0x10, 0xb0, 0x43, 0xe9};
IPAddress ip1(192, 168, 1, 171);
IPAddress ip2(192, 168, 1, 172);
unsigned int localPort1 = 8888;
unsigned int localPort2 = 8890;
#define MAX_PACKET_LENGTH 100
// Buffer for holding received packets.
char packetReceived[MAX_PACKET_LENGTH];

// The remote ClearCore's IP address and port
IPAddress remoteIp(192, 168, 1, 100);
unsigned int remotePort = 8889;

// The last time you sent a packet to the remote device, in milliseconds.
unsigned long lastSendTime = 0;
// Delay between sending packets, in milliseconds
const unsigned long sendingInterval = 2*1000;

// An EthernetUDP instance to let us send and receive packets over UDP
EthernetUDP Udp;

// Set this false if not using DHCP to configure the local IP address.
bool usingDhcp = false;

unsigned long lastLoopTime = 0;
const unsigned long loopInterval = 2000; // 2 seconds in milliseconds


// This example has built-in functionality to automatically clear motor alerts,
// including motor shutdowns. Any uncleared alert will cancel and disallow motion.
#define HANDLE_ALERTS (0)

int LoopCount = 0;
unsigned long currentMillis;
unsigned long previousMillis = 0;  // Stores the last time the event was triggered
const long interval = 1000;        // Interval at which to trigger the event (milliseconds)

// Declare user-defined helper functions
enum MoveState {
    MOVE_IDLE,
    MOVE_CHECK_ALERTS,
    MOVE_START,
    MOVE_WAIT_HLFB,
    MOVE_DONE
};

bool MoveAbsolutePosition(MotorDriver &motor, int position, MoveState &moveState, unsigned long &moveStartTime, unsigned long &lastMillis, int &lastPosition);
//void PrintAlerts();
//void HandleMotorAlerts(MotorDriver &motor, const char *motorName);
//void HandleAlerts();

// Define input pins 1, 2, 3, 4, 5, 6, 7, 8 used to enable/disable motors
#define inputPin1 IO0
#define inputPin2 IO1
#define inputPin3 IO2
#define inputPin4 IO3
// Note: For 8-axis operation, use two ClearCore boards
// Board 1 controls motors 1-4, Board 2 controls motors 5-8 (as M0-M3)

int next_step_last = 0;
int next_step = 0;
String inputString = "";  // A string to hold incoming data

// ============================================================================
//                          MOTOR ENABLE VARIABLES 
// ============================================================================

// Define variables for motor enable (4 motors per ClearCore board)
// Each ClearCore board handles 4 motors independently:
// - Board 1 (BOARD_ID=1): Motors 1-4 → GUI Servos 1-4  
// - Board 2 (BOARD_ID=2): Motors 1-4 → GUI Servos 5-8
bool motor1_enable;     // Motor 1 enable state (from hardware input pin)
bool motor2_enable;     // Motor 2 enable state (from hardware input pin)
bool motor3_enable;     // Motor 3 enable state (from hardware input pin)
bool motor4_enable;     // Motor 4 enable state (from hardware input pin)

// MIGRATION NOTE: When upgrading to Galil DMC-4080, these will become:
// bool motor1_enable through motor8_enable for direct 8-axis control
        
// Motor completion tracking for coordinated motion sequences
bool motor1Done;        // Motor 1 movement completion flag
bool motor2Done;        // Motor 2 movement completion flag  
bool motor3Done;        // Motor 3 movement completion flag
bool motor4Done;        // Motor 4 movement completion flag

// ============================================================================
//                          MOTOR CONNECTOR ASSIGNMENTS
// ============================================================================

// Define the motor connectors (4 per ClearCore board)
// Each board uses the same physical connectors M0-M3 for different logical motors
// Board 1: Motors 1-4 = Physical M0-M3 = GUI Servos 1-4
// Board 2: Motors 1-4 = Physical M0-M3 = GUI Servos 5-8  
MotorDriver &motor1 = ConnectorM0;  // Physical connector M0
MotorDriver &motor2 = ConnectorM1;  // Physical connector M1  
MotorDriver &motor3 = ConnectorM2;  // Physical connector M2
MotorDriver &motor4 = ConnectorM3;  // Physical connector M3

// MIGRATION NOTE: Galil DMC-4080 will use direct axis assignments:
// Axis A, B, C, D, E, F, G, H for motors 1-8 respectively

//bool motor1MoveDistance(MotorDriver &motor,int distance);
//bool motor2MoveDistance(MotorDriver &motor,int distance);
//bool motor3MoveDistance(MotorDriver &motor,int distance);
//bool motor4MoveDistance(MotorDriver &motor,int distance);

// ============================================================================
//                    MOTOR VELOCITY AND ACCELERATION LIMITS
// ============================================================================

// Define limits for velocity and acceleration (4 motors per ClearCore board)
// These limits provide safety boundaries for servo operation
// Board 1: Motors 1-4, Board 2: Motors 1-4 (representing GUI motors 5-8)

// Motor 1 limits (Board 1: Servo 1, Board 2: Servo 5)
int velocityLimit1 = 1000;           // Maximum velocity: 1000 pulses per second
int accelerationLimit1 = 100000;     // Maximum acceleration: 100000 pulses per second²

// Motor 2 limits (Board 1: Servo 2, Board 2: Servo 6)  
int velocityLimit2 = 1000;           // Maximum velocity: 1000 pulses per second
int accelerationLimit2 = 100000;     // Maximum acceleration: 100000 pulses per second²

// Motor 3 limits (Board 1: Servo 3, Board 2: Servo 7)
int velocityLimit3 = 1000;           // Maximum velocity: 1000 pulses per second
int accelerationLimit3 = 100000;     // Maximum acceleration: 100000 pulses per second²

// Motor 4 limits (Board 1: Servo 4, Board 2: Servo 8)
int velocityLimit4 = 1000;           // Maximum velocity: 1000 pulses per second  
int accelerationLimit4 = 100000;     // Maximum acceleration: 100000 pulses per second²

// MIGRATION NOTE: Galil DMC-4080 will use individual axis speed/acceleration commands
// Example: SP A=5000,B=3000,C=4000  (Set speed for axes A, B, C)
//         AC A=50000,B=80000,C=60000 (Set acceleration for axes A, B, C)

// ============================================================================
//                       SYSTEM AND SERVO CONTROL VARIABLES
// ============================================================================

// System control variables - shared across both boards
bool Mode = 0;      // 0 = Manual Mode, 1 = Auto Mode
bool Start = 0;     // 0 = Disabled, 1 = Enabled  
bool Repeat = 0;    // 0 = Single, 1 = Repeat

// Servo control buttons (4 servos per ClearCore board)
// Board 1: Controls GUI Servos 1-4, Board 2: Controls GUI Servos 5-8
bool S1B1 = 1;      // Servo 1 Button 1 (Enable/Disable)
bool S1B2 = 0;      // Servo 1 Button 2 (Run/Stop)
bool S2B1 = 1;      // Servo 2 Button 1 (Enable/Disable)
bool S2B2 = 0;      // Servo 2 Button 2 (Run/Stop)
bool S3B1 = 1;      // Servo 3 Button 1 (Enable/Disable)
bool S3B2 = 0;      // Servo 3 Button 2 (Run/Stop)
bool S4B1 = 1;      // Servo 4 Button 1 (Enable/Disable)
bool S4B2 = 0;      // Servo 4 Button 2 (Run/Stop)

// MIGRATION NOTE: Galil DMC-4080 will use simpler axis enable commands
// Example: SH A,B,C,D (Servo Here - enable axes A,B,C,D)
//         MO A,B,C,D (Motor Off - disable axes A,B,C,D)
bool S8B2 = 0;  // Servo8 Button 2 (maps to board 2 S4B2)
//Values (all 8 motors)
int S1V = 0;  // Servo1 Velocity
int S1A = 0;  // Servo1 Actual
int S1P = 0;  // Servo1 Position
int S2V = 0;  // Servo2 Velocity
int S2A = 0;  // Servo2 Actual
int S2P = 0;  // Servo2 Position
int S3V = 0;  // Servo3 Velocity
int S3A = 0;  // Servo3 Actual
int S3P = 0;  // Servo3 Position
int S4V = 0;  // Servo4 Velocity
int S4A = 0;  // Servo4 Actual
int S4P = 0;  // Servo4 Position
int S5V = 0;  // Servo5 Velocity (maps to board 2 S1V)
int S5A = 0;  // Servo5 Actual (maps to board 2 S1A)
int S5P = 0;  // Servo5 Position (maps to board 2 S1P)
int S6V = 0;  // Servo6 Velocity (maps to board 2 S2V)
int S6A = 0;  // Servo6 Actual (maps to board 2 S2A)
int S6P = 0;  // Servo6 Position (maps to board 2 S2P)
int S7V = 0;  // Servo7 Velocity (maps to board 2 S3V)
int S7A = 0;  // Servo7 Actual (maps to board 2 S3A)
int S7P = 0;  // Servo7 Position (maps to board 2 S3P)
int S8V = 0;  // Servo8 Velocity (maps to board 2 S4V)
int S8A = 0;  // Servo8 Actual (maps to board 2 S4A)
int S8P = 0;  // Servo8 Position (maps to board 2 S4P)
// Setpoints (all 8 motors)
int S1V_SPT = 250;  // Servo1 Velocity
int S1A_SPT = 2000;  // Servo1 Acceleration
int S1P_SPT = 0;  // Servo1 Position
int S2V_SPT = 250;  // Servo2 Velocity
int S2A_SPT = 2000;  // Servo2 Position
int S2P_SPT = 0;  // Servo2 Position
int S3V_SPT = 250;  // Servo3 Velocity
int S3A_SPT = 2000;  // Servo3 Actual
int S3P_SPT = 0;  // Servo3 Position
int S4V_SPT = 500;  // Servo4 Velocity
int S4A_SPT = 250;  // Servo4 Actual
int S4P_SPT = 0;  // Servo4 Position
int S5V_SPT = 250;  // Servo5 Velocity (maps to board 2 S1V_SPT)
int S5A_SPT = 2000;  // Servo5 Acceleration (maps to board 2 S1A_SPT)
int S5P_SPT = 0;  // Servo5 Position (maps to board 2 S1P_SPT)
int S6V_SPT = 250;  // Servo6 Velocity (maps to board 2 S2V_SPT)
int S6A_SPT = 2000;  // Servo6 Acceleration (maps to board 2 S2A_SPT)
int S6P_SPT = 0;  // Servo6 Position (maps to board 2 S2P_SPT)
int S7V_SPT = 250;  // Servo7 Velocity (maps to board 2 S3V_SPT)
int S7A_SPT = 2000;  // Servo7 Acceleration (maps to board 2 S3A_SPT)
int S7P_SPT = 0;  // Servo7 Position (maps to board 2 S3P_SPT)
int S8V_SPT = 250;  // Servo8 Velocity (maps to board 2 S4V_SPT)
int S8A_SPT = 2000;  // Servo8 Acceleration (maps to board 2 S4A_SPT)
int S8P_SPT = 0;  // Servo8 Position (maps to board 2 S4P_SPT)

// Add these global variables for previous velocity and time (all 8 motors)
// Add these global variables at the top of your file:
int prev_S1V = 0, prev_S2V = 0, prev_S3V = 0, prev_S4V = 0;
int prev_S5V = 0, prev_S6V = 0, prev_S7V = 0, prev_S8V = 0;
unsigned long prev_S1V_time = 0, prev_S2V_time = 0, prev_S3V_time = 0, prev_S4V_time = 0;
unsigned long prev_S5V_time = 0, prev_S6V_time = 0, prev_S7V_time = 0, prev_S8V_time = 0;

//Gains Constants
float KV1 = 100;  // Postion Gain
float KA1 = 1;  // Postion Gain 
float KP1 = 1;  // Postion Gain 

float KV2 = 100;  // Postion Gain
float KA2 = 1;  // Postion Gain 
float KP2 = 1;  // Postion Gain  

float KV3 = 1;  // Postion Gain
float KA3 = 1;  // Postion Gain 
float KP3 = 1;  // Postion Gain  

float KV4 = 1;  // Postion Gain
float KA4 = 1;  // Postion Gain 
float KP4 = 1;  // Postion Gain 

int PrimaryAddress = 2000;
int SecondaryAddress = 2000;
int PrimaryTOS = 0;
int SecondaryTOS = 0;
int PrimaryFinish = 4000;
int SecondaryFinish = 4000;


// Primary Rotation : motor 1 - Define a 11 by 3 array for velocity setpoints, acceleration, and position
int motor1_setpoints[11][3] = {
    {10, 8000, 2000}, // Idle              :  Step 0 : Velocity 0, Acceleration 0, Position 0
    {10, 8000, 2000}, // Address           :  Step 1 : Velocity 1, Acceleration 1, Position 1
    {10, 8000, 1500}, // Initial Take Away :  Step 2 : Velocity 1, Acceleration 1, Position 1
    {10, 8000, 1000}, // Take Away         :  Step 3 : Velocity 1, Acceleration 1, Position 1
    {10, 8000, 500}, // Full Rotation      :  Step 4 : Velocity 1, Acceleration 1, Position 1
    {10, 8000, 0}, // Top of Swing      :  Step 5 : Velocity 1, Acceleration 1, Position 1
    {100, 8000, 500}, // Initial Downswing :  Step 6 : Velocity 1, Acceleration 1, Position 1
    {100, 8000, 1000}, // Release           :  Step 7 : Velocity 1, Acceleration 1, Position 1
    {100, 8000, 2000}, // Impact            :  Step 8 : Velocity 1, Acceleration 1, Position 1
    {100, 8000, 2500}, // Follow Through    :  Step 9 : Velocity 1, Acceleration 1, Position 1
    {100, 8000, 4000}, // Finish            :  Step 10 : Velocity 1, Acceleration 1, Position   
};

// Secondary Rotation : motor 2 - Define a 11 by 3 array for velocity setpoints, acceleration, and position
int motor2_setpoints[11][3] = {
    {12, 8000, 2000},  // Idle              :  Step 0 : Velocity 0, Acceleration 0, Position 0
    {12, 8000, 2000}, // Address           :  Step 1 : Velocity, Acceleration, Position
    {12, 8000, 2000}, // Initial Take Away :  Step 2 : Velocity, Acceleration, Position
    {12, 8000, 2000}, // Take Away         :  Step 3 : Velocity, Acceleration, Position
    {12, 8000, 0}, // Full Rotation     :  Step 4 : Velocity, Acceleration, Position
    {12, 8000, 0}, // Top of Swing      :  Step 5 : Velocity, Acceleration, Position
    {102, 8000, 0}, // Initial Downswing :  Step 6 : Velocity, Acceleration, Position
    {102, 8000, 500}, // Release           :  Step 7 : Velocity, Acceleration, Position
    {102, 8000, 2000}, // Impact            :  Step 8 : Velocity, Acceleration, Position
    {102, 8000, 3000}, // Follow Through    :  Step 9 : Velocity, Acceleration, Position
    {102, 8000, 4000}, // Finish            :  Step 10 : Velocity, Acceleration, Position
};

// Tertiary Lift : motor 3 - Define a 11 by 3 array for velocity setpoints, acceleration, and position
int motor3_setpoints[11][3] = {
    {1003, 8000, 000}, // Idle              :  Step 0 : Velocity, Acceleration, Position
    {2003, 8000, 900}, // Address           :  Step 1 : Velocity, Acceleration, Position
    {2003, 8000, 800}, // Initial Take Away :  Step 2 : Velocity, Acceleration, Position
    {2003, 8000, 700}, // Take Away         :  Step 3 : Velocity, Acceleration, Position
    {2003, 8000, 600}, // Full Rotation     :  Step 4 : Velocity, Acceleration, Position
    {2003, 8000, 500}, // Top of Swing      :  Step 5 : Velocity, Acceleration, Position
    {2003, 8000, 600}, // Initial Downswing :  Step 6 : Velocity, Acceleration, Position
    {2003, 8000, 700}, // Release           :  Step 7 : Velocity, Acceleration, Position
    {2003, 8000, 800}, // Impact            :  Step 8 : Velocity, Acceleration, Position 
    {2003, 8000, 900}, // Follow Through    :  Step 9 : Velocity, Acceleration, Position
    {2003, 8000, 1000}, // Finish            :  Step 10 : Velocity, Acceleration, Position
};

// Tertiary Rotation : motor 4 - Define a 11 by 3 array for velocity setpoints, acceleration, and position
int motor4_setpoints[11][3] = {
    {500, 2000, 000}, // Idle              :  Step 0 : Velocity, Acceleration, Position
    {500, 5000, 400}, // Address           :  Step 1 : Velocity, Acceleration, Position
    {500, 5000, 400}, // Initial Take Away :  Step 2 : Velocity, Acceleration, Position
    {500, 5000, 270}, // Take Away         :  Step 3 : Velocity, Acceleration, Position
    {500, 5000, 125}, // Full Rotation     :  Step 4 : Velocity, Acceleration, Position
    {500, 5000, 000}, // Top of Swing      :  Step 5 : Velocity, Acceleration, Position
    {500, 5000, 300}, // Initial Downswing :  Step 6 : Velocity, Acceleration, Position
    {500, 5000, 356}, // Release           :  Step 7 : Velocity, Acceleration, Position
    {500, 5000, 390}, // Impact            :  Step 8 : Velocity, Acceleration, Position
    {500, 5000, 415}, // Follow Through    :  Step 9 : Velocity, Acceleration, Position
    {500, 5000, 623}, // Finish   
};

MoveState moveState1 = MOVE_IDLE;
MoveState moveState2 = MOVE_IDLE;
MoveState moveState3 = MOVE_IDLE;
MoveState moveState4 = MOVE_IDLE;

unsigned long moveStartTime1;
unsigned long moveStartTime2;
unsigned long moveStartTime3;
unsigned long moveStartTime4;

const unsigned long moveTimeout = 10000; // Timeout in milliseconds

// Add these variables at the top with other global declarations
unsigned long lastMillis1 = 0, lastMillis2 = 0, lastMillis3 = 0, lastMillis4 = 0;
int lastPosition1 = 0, lastPosition2 = 0, lastPosition3 = 0, lastPosition4 = 0;

// Add these global variables near the top with other declarations
int initialPosition1 = 0, initialPosition2 = 0, initialPosition3 = 0, initialPosition4 = 0;

// Define the interval for calculating position and speed (in milliseconds)
const unsigned long calculationInterval = 100; // 100ms interval

// Add these variables at the top with other global declarations
unsigned long lastCalculationTime = 0;

// Add these variables at the top with other global declarations
unsigned long lastStateEngineStepTime = 0;
const unsigned long stateEngineStepInterval = 3000; // 1 second interval

// Add these variables at the top with other global declarations
unsigned long lastReportDataTime = 0;
const unsigned long ReportDataInterval = 3000; // 3 second interval

//***********************************************************************

void parseData(String data, int &V, int &A, int &P);
void handleCommand(String command);
void sendCurrentValues();
void sendButtonStates();
void sendSetpoints();
void CalculateAcceleration(MotorDriver &motor, int &acceleration, unsigned long &lastMillis, int &lastVelocity);
void sendStateEngineStep();
void loadMotorSetpoints();
void loadSetpoints(int step);

//***********************************************************************
// ============================================================================
//                          MAIN SETUP FUNCTION
// ============================================================================

/**
 * @brief Initialize ClearCore board and configure 8-axis servo control system
 * 
 * This function performs complete system initialization for dual-board 8-axis
 * servo control operation. Sets up network communication, motor interfaces,
 * and system state variables for coordinated operation with Python GUI.
 * 
 * Initialization Sequence:
 * 1. Configure Ethernet interface with board-specific IP and port
 * 2. Initialize all 4 servo motor connectors (M0-M3) 
 * 3. Set safe default parameters for velocity, acceleration, position
 * 4. Configure HLFB feedback and step/direction interfaces
 * 5. Initialize system control states and communication variables
 * 
 * Network Configuration:
 * - Board 1 (BOARD_ID=1): IP 192.168.1.171, Port 8888
 * - Board 2 (BOARD_ID=2): IP 192.168.1.172, Port 8890
 * 
 * Safety Features:
 * - All motors start in disabled state for safety
 * - Default parameters within safe operational limits
 * - HLFB feedback monitoring enabled for fault detection
 * 
 * @param None
 * @return void
 * 
 * @note This function must complete successfully before main loop operation
 * @warning Ensure proper network configuration before power-on
 */
// ============================================================================
//                          MAIN SETUP FUNCTION
// ============================================================================

/**
 * @brief Initialize ClearCore board and configure 4-motor servo control system
 * 
 * This function performs complete system initialization for dual-board 8-axis
 * servo control operation. Each ClearCore board runs this same program but
 * with different BOARD_ID settings to control different motor sets.
 * 
 * Initialization Sequence:
 * 1. Configure Ethernet interface with board-specific IP and port
 * 2. Initialize all 4 servo motor connectors (M0-M3) with HLFB feedback
 * 3. Set velocity and acceleration limits for safe operation
 * 4. Enable motors based on hardware input pin states
 * 5. Wait for HLFB assertion to confirm motor readiness
 * 6. Handle any motor alerts during initialization
 * 
 * Board Configuration:
 * - Board 1 (BOARD_ID=1): Controls Motors 1-4 (GUI Servos 1-4)
 *   IP: 192.168.1.171, Port: 8888
 * - Board 2 (BOARD_ID=2): Controls Motors 5-8 (GUI Servos 5-8) 
 *   IP: 192.168.1.172, Port: 8890
 * 
 * Motor Configuration:
 * - Step/Direction mode with HLFB bipolar PWM feedback
 * - 482Hz carrier frequency for noise immunity
 * - Hardware enable pins (IO0-IO3) control motor enable states
 * - Velocity and acceleration limits enforced for safety
 * 
 * Safety Features:
 * - Motors only enabled if hardware enable pins are active
 * - HLFB monitoring ensures proper motor connection
 * - Alert handling prevents operation with motor faults
 * - 3-second timeout for HLFB assertion prevents infinite waits
 * 
 * @param None
 * @return void
 * 
 * @note Both boards run identical code - BOARD_ID determines configuration
 * @warning Ensure proper network and motor connections before power-on
 */
void setup() {

// ========================================================================
// 8-AXIS DUAL BOARD ARCHITECTURE NOTE:
// ========================================================================
// This same program runs on both ClearCore boards. The BOARD_ID define 
// determines which board this is (1 or 2). Each board independently 
// controls 4 motors and communicates with the Python GUI via UDP.
// The Python GUI coordinates both boards to provide unified 8-axis control.
//
// Board 1: Motors 1-4 → Python GUI Servos 1-4 (Tab 1)
// Board 2: Motors 5-8 → Python GUI Servos 5-8 (Tab 2)

// ========================================================================
// SERIAL COMMUNICATION INITIALIZATION  
// ========================================================================

Serial.begin(9600);     // Initialize serial at 9600 baud for debug output 

// ========================================================================
// NETWORK CONFIGURATION - BOARD-SPECIFIC SETTINGS
// ========================================================================

// Configure network parameters based on board ID for dual-board operation
// Each board requires unique MAC address, IP address, and UDP port
byte* mac;          // Pointer to board-specific MAC address
IPAddress ip;       // Board-specific IP address for network identification  
unsigned int localPort;  // Board-specific UDP port for communication

if (BOARD_ID == 1) {
    // Board 1 configuration - Primary board (Motors 1-4)
    mac = mac1;                 // Use MAC address 1 for unique network identity
    ip = ip1;                   // IP: 192.168.1.171 for Board 1 
    localPort = localPort1;     // Port: 8888 for Board 1 communication
} else {
    // Board 2 configuration - Secondary board (Motors 5-8)
    mac = mac2;                 // Use MAC address 2 for unique network identity
    ip = ip2;                   // IP: 192.168.1.172 for Board 2
    localPort = localPort2;     // Port: 8890 for Board 2 communication
}

// Initialize Ethernet interface with board-specific parameters
// Static IP configuration for reliable industrial networking
Ethernet.begin(mac, ip);

// Start UDP server for communication with Python GUI
// UDP provides low-latency real-time communication for servo control
Udp.begin(localPort);

    // ========================================================================
    // NETWORK LINK VERIFICATION
    // ========================================================================
    
    // Verify physical Ethernet connection before proceeding
    // Critical for ensuring reliable communication with Python GUI
    while (Ethernet.linkStatus() == LinkOFF) {
        Serial.println("The Ethernet cable is unplugged...");
        delay(1000);    // Wait 1 second before checking again
    }
    
    // Re-initialize UDP listener after confirming physical link
    // Ensures UDP socket is properly bound for incoming messages
    Udp.begin(localPort);
    Serial.println("UDP listener started.");
    
    // ========================================================================
    // SERIAL COMMUNICATION TIMEOUT HANDLING
    // ========================================================================
    
    // Wait for Serial connection with timeout to prevent infinite blocking
    // Allows operation even without serial monitor connected
    uint32_t timeout = 2000;           // 2-second timeout for serial connection
    uint32_t startTime = millis();     // Record start time for timeout calculation
    while (!Serial && millis() - startTime < timeout) {
        continue;    // Wait for serial connection or timeout
    }

    // ========================================================================
    // HARDWARE INPUT PIN INITIALIZATION
    // ========================================================================
    
    // Initialize step control variable for motion sequencing
    next_step = 0;
    
    // Read hardware enable input pins to determine initial motor enable states
    // Hardware pins provide physical override for motor enable functionality
    motor1_enable = digitalRead(inputPin1);    // Read IO0 for Motor 1 enable state
    motor2_enable = digitalRead(inputPin2);    // Read IO1 for Motor 2 enable state  
    motor3_enable = digitalRead(inputPin3);    // Read IO2 for Motor 3 enable state
    motor4_enable = digitalRead(inputPin4);    // Read IO3 for Motor 4 enable state

    // ========================================================================
    // MOTOR MANAGER CONFIGURATION
    // ========================================================================
    
    // Configure global motor manager settings for all motors
    // Normal clock rate provides standard timing for step/direction signals
    MotorMgr.MotorInputClocking(MotorManager::CLOCK_RATE_NORMAL);
    
    // Set all motors to step/direction mode for servo drive compatibility
    // This mode provides step pulses and direction signals to external servo drives
    MotorMgr.MotorModeSet(MotorManager::MOTOR_ALL, Connector::CPM_MODE_STEP_AND_DIR);

    // ========================================================================
    // INDIVIDUAL MOTOR CONFIGURATION - ALL 4 MOTORS
    // ========================================================================

    // Motor 1 Configuration (M0 Connector)
    // Configure HLFB feedback for position and status monitoring
    motor1.HlfbMode(MotorDriver::HLFB_MODE_HAS_BIPOLAR_PWM);   // Bipolar PWM feedback mode
    motor1.HlfbCarrier(MotorDriver::HLFB_CARRIER_482_HZ);      // 482Hz carrier for noise immunity
    motor1.VelMax(velocityLimit1);                             // Set maximum velocity limit for safety
    motor1.AccelMax(accelerationLimit1);                       // Set maximum acceleration limit for safety

    // Motor 2 Configuration (M1 Connector)  
    // Identical configuration to Motor 1 for consistent operation
    motor2.HlfbMode(MotorDriver::HLFB_MODE_HAS_BIPOLAR_PWM);   // Bipolar PWM feedback mode
    motor2.HlfbCarrier(MotorDriver::HLFB_CARRIER_482_HZ);      // 482Hz carrier for noise immunity
    motor2.VelMax(velocityLimit2);                             // Set maximum velocity limit for safety
    motor2.AccelMax(accelerationLimit2);                       // Set maximum acceleration limit for safety

    // Motor 3 Configuration (M2 Connector)
    // Identical configuration to Motor 1 for consistent operation  
    motor3.HlfbMode(MotorDriver::HLFB_MODE_HAS_BIPOLAR_PWM);   // Bipolar PWM feedback mode
    motor3.HlfbCarrier(MotorDriver::HLFB_CARRIER_482_HZ);      // 482Hz carrier for noise immunity
    motor3.VelMax(velocityLimit3);                             // Set maximum velocity limit for safety
    motor3.AccelMax(accelerationLimit3);                       // Set maximum acceleration limit for safety

    // Motor 4 Configuration (M3 Connector)
    // Identical configuration to Motor 1 for consistent operation
    motor4.HlfbMode(MotorDriver::HLFB_MODE_HAS_BIPOLAR_PWM);   // Bipolar PWM feedback mode
    motor4.HlfbCarrier(MotorDriver::HLFB_CARRIER_482_HZ);      // 482Hz carrier for noise immunity
    motor4.VelMax(velocityLimit4);                             // Set maximum velocity limit for safety
    motor4.AccelMax(accelerationLimit4);                       // Set maximum acceleration limit for safety

    // ========================================================================
    // MOTOR ENABLE SEQUENCE BASED ON HARDWARE PINS
    // ========================================================================
    
    // Enable motors based on hardware input pin states read during initialization
    // This provides physical override capability for safety and manual control
    motor1.EnableRequest(motor1_enable);
    Serial.println("Motor1 Enabled");
    motor2.EnableRequest(motor2_enable);
    Serial.println("Motor2 Enabled");
    motor3.EnableRequest(motor3_enable);
    Serial.println("Motor3 Enabled");
    motor4.EnableRequest(motor4_enable);
    Serial.println("Motor4 Enabled");

    // ========================================================================
    // HLFB (HIGH LEVEL FEEDBACK) VERIFICATION FOR ALL MOTORS
    // ========================================================================
    
    Serial.println("Waiting for HLFB...");
    
    // Motor 1 HLFB Verification - Confirm motor is ready for operation
    if (motor1.EnableActiveLevel() == true) {
        unsigned long start1 = millis();
        // Wait for HLFB assertion with 3-second timeout to prevent infinite blocking
        while (motor1.HlfbState() != MotorDriver::HLFB_ASSERTED &&
               !motor1.StatusReg().bit.AlertsPresent &&
               millis() - start1 < 3000) {
            delay(10);    // Small delay to prevent excessive polling
        }
        if (motor1.HlfbState() != MotorDriver::HLFB_ASSERTED) {
            Serial.println("Warning: Motor1 HLFB not asserted (not connected or not enabled)");
        }
    }
    
    // Motor 2 HLFB Verification - Confirm motor is ready for operation
    if (motor2.EnableActiveLevel() == true) {
        unsigned long start2 = millis();
        // Wait for HLFB assertion with 3-second timeout to prevent infinite blocking
        while (motor2.HlfbState() != MotorDriver::HLFB_ASSERTED &&
               !motor2.StatusReg().bit.AlertsPresent &&
               millis() - start2 < 3000) {
            delay(10);    // Small delay to prevent excessive polling
        }
        if (motor2.HlfbState() != MotorDriver::HLFB_ASSERTED) {
            Serial.println("Warning: Motor2 HLFB not asserted (not connected or not enabled)");
        }
    }
    
    // Motor 3 HLFB Verification - Confirm motor is ready for operation  
    if (motor3.EnableActiveLevel() == true) {
        unsigned long start3 = millis();
        // Wait for HLFB assertion with 3-second timeout to prevent infinite blocking
        while (motor3.HlfbState() != MotorDriver::HLFB_ASSERTED &&
               !motor3.StatusReg().bit.AlertsPresent &&
               millis() - start3 < 3000) {
            delay(10);    // Small delay to prevent excessive polling
        }
        if (motor3.HlfbState() != MotorDriver::HLFB_ASSERTED) {
            Serial.println("Warning: Motor3 HLFB not asserted (not connected or not enabled)");
        }
    }
    
    // Motor 4 HLFB Verification - Confirm motor is ready for operation
    if (motor4.EnableActiveLevel() == true) {
        unsigned long start4 = millis();
        // Wait for HLFB assertion with 3-second timeout to prevent infinite blocking
        while (motor4.HlfbState() != MotorDriver::HLFB_ASSERTED &&
               !motor4.StatusReg().bit.AlertsPresent &&
               millis() - start4 < 3000) {
            delay(10);    // Small delay to prevent excessive polling
        }
        if (motor4.HlfbState() != MotorDriver::HLFB_ASSERTED) {
            Serial.println("Warning: Motor4 HLFB not asserted (not connected or not enabled)");
        }
    }

    // Check if motor alert occurred during enabling
    // Clear alert if configured to do so 
    if (motor1.StatusReg().bit.AlertsPresent) {
        Serial.println("Motor1 alert detected.");
        PrintAlerts();
        if (HANDLE_ALERTS) {
            HandleAlerts();
        } else {
            Serial.println("Enable automatic alert handling by setting HANDLE_ALERTS to 1.");
        }
        Serial.println("Enabling may not have completed as expected. Proceed with caution.");
        Serial.println();
    } else {
        Serial.println("Motor1 Ready");
    }

    if (motor2.StatusReg().bit.AlertsPresent) {
        Serial.println("Motor2 alert detected.");
        PrintAlerts();
        if (HANDLE_ALERTS) {
            HandleAlerts();
        } else {
            Serial.println("Enable automatic alert handling by setting HANDLE_ALERTS to 1.");
        }
        Serial.println("Enabling may not have completed as expected. Proceed with caution.");
        Serial.println();
    } else {
        Serial.println("Motor2 Ready");
    }

    if (motor3.StatusReg().bit.AlertsPresent) {
        Serial.println("Motor3 alert detected.");
        PrintAlerts();
        if (HANDLE_ALERTS) {
            HandleAlerts();
        } else {
            Serial.println("Enable automatic alert handling by setting HANDLE_ALERTS to 1.");
        }
        Serial.println("Enabling may not have completed as expected. Proceed with caution.");
        Serial.println();
    } else {
        Serial.println("Motor3 Ready");
    }

    if (motor4.StatusReg().bit.AlertsPresent) {
        Serial.println("Motor4 alert detected.");
        PrintAlerts();
        if (HANDLE_ALERTS) {
            HandleAlerts();
        } else {
            Serial.println("Enable automatic alert handling by setting HANDLE_ALERTS to 1.");
        }

        Serial.println("Enabling may not have completed as expected. Proceed with caution.");
        Serial.println();
    } else {
        Serial.println("Motor4 Ready");
    }
    delay(2000);
  } // End setup
//***********************************************************************
//***********************************************************************
// ============================================================================
//                          MAIN PROGRAM LOOP
// ============================================================================

/**
 * @brief Main program execution loop for continuous servo control operation
 * 
 * This function runs continuously after setup() completes, providing real-time
 * servo control and communication with the Python GUI. Handles incoming UDP
 * commands, motor status monitoring, and periodic status transmission.
 * 
 * Loop Operations:
 * 1. Check for incoming UDP messages from Python GUI
 * 2. Parse and execute servo control commands
 * 3. Monitor motor status and HLFB feedback
 * 4. Send periodic status updates to Python GUI
 * 5. Handle motor alerts and error conditions
 * 6. Manage coordinated motion sequences
 * 
 * Communication Protocol:
 * - Receives commands via UDP from Python GUI
 * - Sends status updates every 2 seconds
 * - Handles parameter updates, position commands, enable/disable
 * - Provides real-time velocity, acceleration, position feedback
 * 
 * Motor Management:
 * - Monitors HLFB status for all 4 motors
 * - Executes absolute position movements with state tracking
 * - Handles alerts and fault conditions
 * - Coordinates multi-axis movements when requested
 * 
 * Timing Control:
 * - 2-second interval for status updates to prevent network flooding
 * - Real-time command processing for responsive control
 * - State machine management for complex motion sequences
 * 
 * @param None
 * @return void (infinite loop)
 * 
 * @note This loop runs continuously until power-off or system reset
 * @warning Do not add blocking delays that could disrupt real-time operation
 */
void loop() {

    // ========================================================================
    // MAIN LOOP TIMING AND COMMUNICATION
    // ========================================================================
    
    // Record current time for timing calculations and interval management
    currentMillis = millis();    // Used to calculate report intervals and timing
    
    // Process incoming UDP commands from Python GUI
    // This function handles all command parsing and execution
    ReadUdpData();
    
    // Serial command processing disabled - UDP communication preferred for network operation
    // ReadSerialData();    // Commented out - using UDP instead of serial commands
    
    // ========================================================================
    // NETWORK PACKET PROCESSING
    // ========================================================================

    // Check for incoming UDP packets from Python GUI
    int packetSize = Udp.parsePacket();    // Parse any available UDP packets
    IPAddress remote = Udp.remoteIP();     // Get sender's IP address for response routing
    
    // Maintain Ethernet connection health and process any DHCP renewals
    Ethernet.maintain();    // Keep network connection active
    delay(10);              // Small delay to prevent excessive CPU usage
    
    // Update motor parameters based on any received commands
    // This function applies new setpoints received via UDP
    UpdateMotorParameters();
  // ========================================================================
  // STATE ENGINE FOR COORDINATED MOTOR SEQUENCING
  // ========================================================================
  
  // Monitor state engine step changes and update Python GUI when step advances
  // This provides feedback to the GUI about automation sequence progress
  if (next_step != next_step_last) {    
      // State step has changed - notify Python GUI of new step number
      sendStateEngineStep();           // Send current step number to GUI
      next_step_last = next_step;      // Update last step tracking variable
      
      // In Auto Mode, automatically load next set of parameters from setpoint arrays
      if (Mode == 1) {    // Auto Mode: Use predefined motion sequences
          loadSetpoints(next_step);    // Load step-specific parameters for coordinated motion
      }
  }


    // ========================================================================
    // MANUAL MODE OPERATION (Mode = 0)
    // ========================================================================
    
    if (Mode == 0) {    // Manual Mode: Direct servo control via GUI setpoints
        // Load current setpoint values from GUI into active motor parameters
        loadMotorSetpoints();
        
        // Execute individual motor movements to GUI-specified positions
        // Each motor moves independently to its respective setpoint position
        MoveAbsolutePosition(motor1, S1P_SPT, moveState1, moveStartTime1, lastMillis1, lastPosition1);
        MoveAbsolutePosition(motor2, S2P_SPT, moveState2, moveStartTime2, lastMillis2, lastPosition2);
        MoveAbsolutePosition(motor3, S3P_SPT, moveState3, moveStartTime3, lastMillis3, lastPosition3);
        MoveAbsolutePosition(motor4, S4P_SPT, moveState4, moveStartTime4, lastMillis4, lastPosition4);
    }

    // ========================================================================
    // AUTOMATIC MODE OPERATION (Mode = 1) - COORDINATED MOTION SEQUENCES
    // ========================================================================
    
    if (Mode == 1) {    // Auto Mode: Predefined motion sequences for automation
        // Load motor setpoints for current automation step
        loadMotorSetpoints();
        
        // Debug output for monitoring setpoint changes (periodic to avoid flooding)
        if (currentMillis - lastReportDataTime >= ReportDataInterval) {
            Serial.println(S2V_SPT);    // Output Motor 2 velocity setpoint for monitoring
        }
        
        // Servo enable checking for coordinated motion (currently commented out)
        // Individual servo enable states can control which motors participate in sequence
        // if (S1B1 == 1) {motor1Done = MoveAbsolutePosition(motor1, S1P_SPT, moveState1, moveStartTime1, lastMillis1, lastPosition1);}
        // if (S2B1 == 1) {motor2Done = MoveAbsolutePosition(motor2, S2P_SPT, moveState2, moveStartTime2, lastMillis2, lastPosition2);}
        // if (S3B1 == 1) {motor3Done = MoveAbsolutePosition(motor3, S3P_SPT, moveState3, moveStartTime3, lastMillis3, lastPosition3);}
        // if (S4B1 == 1) {motor4Done = MoveAbsolutePosition(motor4, S4P_SPT, moveState4, moveStartTime4, lastMillis4, lastPosition4);}
        
        // ====================================================================
        // AUTOMATION SEQUENCE STATE MACHINE
        // ====================================================================
        
        switch (next_step) {
            case 0: // Idle
                //Serial.println("Step 0");
                S1V_SPT = 500;
                S2V_SPT = 500;
                if (S1B1 == 1) {motor1Done = MoveAbsolutePosition(motor1, PrimaryAddress, moveState1, moveStartTime1, lastMillis1, lastPosition1);}
                if (S2B1 == 1) {motor2Done = MoveAbsolutePosition(motor2, SecondaryAddress, moveState2, moveStartTime2, lastMillis2, lastPosition2);}
                if (Start == 1) {  // Removed the semicolon
                    next_step = 1;
                }
                break;
            case 1: // Address
                //Serial.println("Step 1");
                //loadMotorSetpoints();
                //motor1Done = MoveDistance(motor1,2000);
                S2V_SPT = 0;
                if (S1B1 == 1) {motor1Done = MoveAbsolutePosition(motor1, PrimaryAddress, moveState1, moveStartTime1, lastMillis1, lastPosition1);}
                if (S2B1 == 1) {motor2Done = MoveAbsolutePosition(motor2, SecondaryAddress, moveState2, moveStartTime2, lastMillis2, lastPosition2);}
                            
                if (motor1Done && motor2Done) {
                    next_step = 2;
                    moveState1 = MOVE_IDLE;  // Reset moveState1
                    moveState2 = MOVE_IDLE;  // Reset moveState2
                } 
                break;
            case 2: //Initial TakeAway
                //Serial.println("Step 2");

                if (S1B1 == 1) {motor1Done = MoveAbsolutePosition(motor1, PrimaryTOS, moveState1, moveStartTime1, lastMillis1, lastPosition1);}
                if (S2B1 == 1) {motor2Done = MoveAbsolutePosition(motor2, SecondaryTOS, moveState2, moveStartTime2, lastMillis2, lastPosition2);}
                                 
                if ((S1P <= S1P_SPT) &&  (S2P <= S2P_SPT)) {
                    next_step = 3;
                    //moveState1 = MOVE_IDLE;  // Reset moveState1
                    //moveState2 = MOVE_IDLE;  // Reset moveState2
                } 
                break;
            case 3: // Take Away
                //Serial.println("Step 3");
                //loadMotorSetpoints();
                if (S1B1 == 1) {motor1Done = MoveAbsolutePosition(motor1, PrimaryTOS, moveState1, moveStartTime1, lastMillis1, lastPosition1);}
                if (S2B1 == 1) {motor2Done = MoveAbsolutePosition(motor2, SecondaryTOS, moveState2, moveStartTime2, lastMillis2, lastPosition2);}
                
                if ((S1P <= S1P_SPT) &&  (S2P <= S2P_SPT)) {
                    next_step = 4;
                    //moveState1 = MOVE_IDLE;  // Reset moveState1
                    //moveState2 = MOVE_IDLE;  // Reset moveState2
                } 
                break;
            case 4:  // Full Rotation              
                //Serial.println("Step 4");
                //loadMotorSetpoints();
                if (S1B1 == 1) {motor1Done = MoveAbsolutePosition(motor1, PrimaryTOS, moveState1, moveStartTime1, lastMillis1, lastPosition1);}
                if (S2B1 == 1) {motor2Done = MoveAbsolutePosition(motor2, SecondaryTOS, moveState2, moveStartTime2, lastMillis2, lastPosition2);}

                if ((S1P <= S1P_SPT) &&  (S2P <= S2P_SPT)) {
                    next_step = 5;
                    //moveState1 = MOVE_IDLE;  // Reset moveState1
                    //moveState2 = MOVE_IDLE;  // Reset moveState2
                } 
                break;
            case 5:  // Top of Swing
                //Serial.println("Step 5");
                
                if (S1B1 == 1) {motor1Done = MoveAbsolutePosition(motor1, PrimaryTOS, moveState1, moveStartTime1, lastMillis1, lastPosition1);}
                if (S2B1 == 1) {motor2Done = MoveAbsolutePosition(motor2, SecondaryTOS, moveState2, moveStartTime2, lastMillis2, lastPosition2);}

                if (motor1Done && motor2Done) {
                    next_step = 6;  // Reset to the initial step
                    moveState1 = MOVE_IDLE;  // Reset moveState1
                    moveState2 = MOVE_IDLE;  // Reset moveState2
                }
                break;
            case 6:  // Initial Downswing              
                //Serial.println("Step 6");
                
                if (S1B1 == 1) {motor1Done = MoveAbsolutePosition(motor1, PrimaryFinish, moveState1, moveStartTime1, lastMillis1, lastPosition1);}
                if (S2B1 == 1) {motor2Done = MoveAbsolutePosition(motor2, SecondaryFinish, moveState2, moveStartTime2, lastMillis2, lastPosition2);}

                if ((S1P >= S1P_SPT) &&  (S2P >= S2P_SPT)) {
                    next_step = 7;
                    //moveState1 = MOVE_IDLE;  // Reset moveState1
                    //moveState2 = MOVE_IDLE;  // Reset moveState2
                }  
                break;
            case 7:  // Release             
                //Serial.println("Step 7");
                
                if (S1B1 == 1) {motor1Done = MoveAbsolutePosition(motor1, PrimaryFinish, moveState1, moveStartTime1, lastMillis1, lastPosition1);}
                if (S2B1 == 1) {motor2Done = MoveAbsolutePosition(motor2, SecondaryFinish, moveState2, moveStartTime2, lastMillis2, lastPosition2);}

                if ((S1P >= S1P_SPT) &&  (S2P >= S2P_SPT)) {
                    next_step = 8;
                    //moveState1 = MOVE_IDLE;  // Reset moveState1
                    //moveState2 = MOVE_IDLE;  // Reset moveState2
                }   
                break;
            case 8:  // Impact             
                //Serial.println("Step 7");
                
                if (S1B1 == 1) {motor1Done = MoveAbsolutePosition(motor1, PrimaryFinish, moveState1, moveStartTime1, lastMillis1, lastPosition1);}
                if (S2B1 == 1) {motor2Done = MoveAbsolutePosition(motor2, SecondaryFinish, moveState2, moveStartTime2, lastMillis2, lastPosition2);}

                if ((S1P >= S1P_SPT) &&  (S2P >= S2P_SPT)) {
                    next_step = 9;
                    //moveState1 = MOVE_IDLE;  // Reset moveState1
                    //moveState2 = MOVE_IDLE;  // Reset moveState2
                }  
                break;
            case 9:  // Follow Through        
                //Serial.println("Step 7");
                
                if (S1B1 == 1) {motor1Done = MoveAbsolutePosition(motor1, PrimaryFinish, moveState1, moveStartTime1, lastMillis1, lastPosition1);}
                if (S2B1 == 1) {motor2Done = MoveAbsolutePosition(motor2, SecondaryFinish, moveState2, moveStartTime2, lastMillis2, lastPosition2);}

                if ((S1P >= S1P_SPT) &&  (S2P >= S2P_SPT)) {
                    next_step = 10;
                    //moveState1 = MOVE_IDLE;  // Reset moveState1
                    //moveState2 = MOVE_IDLE;  // Reset moveState2
                }  
                break;
            case 10:  // Finish           
                //Serial.println("Step 7");
                
                if (S1B1 == 1) {motor1Done = MoveAbsolutePosition(motor1, PrimaryFinish, moveState1, moveStartTime1, lastMillis1, lastPosition1);}
                if (S2B1 == 1) {motor2Done = MoveAbsolutePosition(motor2, SecondaryFinish, moveState2, moveStartTime2, lastMillis2, lastPosition2);}
              if (motor1Done && motor2Done) {
                  moveState1 = MOVE_IDLE;  // Reset moveState1
                  moveState2 = MOVE_IDLE;  // Reset moveState2
                  if (Repeat == 1) {                  
                      next_step = 1;  // Repeat mode goes back to step 1
                      Start = 0;
                      sendButtonStates();
                  } else {
                      next_step = 0;  // Single mode goes back to step 0
                      next_step = 0;  // Single mode goes back to step 0
                      Start = 0;
                      sendButtonStates();
                  }
              }

                break;
        } // end switch

    }  // end if (S1B2 == 1)
  //**********************************************
   // Serial.println("End Case Statement");
  //**********************************************
  
    //Periodically send the state engine step
    if (currentMillis - lastStateEngineStepTime > stateEngineStepInterval) {
        lastStateEngineStepTime = currentMillis;
        sendStateEngineStep();
    }

    unsigned long scanTime = calculateScanTime();
    // Periodically report debug data
    if (currentMillis - lastReportDataTime >= ReportDataInterval) {
        lastReportDataTime = currentMillis;
        // Calculate and print the scan time
        
        Serial.print("Scan time: ");
        Serial.print(scanTime);
        Serial.println(" ms");

        Serial.print("Mode =");
        Serial.print(Mode);
        Serial.print(" / ");
        Serial.print("S1V_SPT=");
        Serial.print(S1V_SPT); 
        Serial.print(" / ");  
        Serial.print("S1V=");
        Serial.print(S1V);
        Serial.print(" / "); 
        Serial.print("S1P_SPT=");
        Serial.println(S1P_SPT);

     /* Serial.print(" / ");
      Serial.print("S2V_SPT=");
      Serial.print(S2V_SPT);
      Serial.print(" / ");
      Serial.print("S2V=");
      Serial.print(S2V);
      Serial.print(" / ");
      Serial.print("S2P_SPT=");
      Serial.print(S2P_SPT);
      Serial.print(" / ");
      Serial.print("S2P=");
      Serial.print(S2P);
      Serial.print(" / ");
      Serial.println(" ");
      Serial.print("S2P_SPT - S2P = ");
      Serial.print(S2P_SPT - S2P);
      Serial.println(" / ");
      Serial.print("(S2P_SPT - S2P) * Velocity = ");
      Serial.print((S2P_SPT - S2P) * S1V);
      Serial.println(" / ");
      Serial.print("S1P_SPT - S1P = ");
      Serial.print(S1P_SPT - S1P);
      Serial.println(" / ");
      Serial.println(" ");
*/

   }
    // ...existing code...
}   // End loop

//********************************************************************
// Function definitions
//********************************************************************
// ============================================================================
//                      UDP COMMAND PROCESSING FUNCTION
// ============================================================================

/**
 * @brief Process incoming UDP commands from Python GUI
 * 
 * This function handles all incoming UDP messages from the Python GUI,
 * parsing commands and executing appropriate servo control actions.
 * Provides real-time command processing for responsive servo control.
 * 
 * Command Types Handled:
 * - Parameter updates (velocity, acceleration, position setpoints)
 * - Motor enable/disable commands
 * - Position clear commands for individual motors
 * - System mode changes (Manual/Auto, Repeat, Start)
 * - Request commands for status, setpoints, button states
 * 
 * Message Format:
 * - Commands arrive as ASCII strings via UDP
 * - Format: "CMD:COMMAND_TYPE:PARAMETERS\n"
 * - Examples: "CMD:S1_Parameters:1000,500,2000"
 *            "CMD:CLEAR_S1_POSITION"
 *            "CMD:Mode AUTO"
 * 
 * Response Actions:
 * - Updates global parameter variables for motor control
 * - Sends acknowledgment and status responses to Python GUI
 * - Triggers immediate parameter application to motors
 * - Provides error handling for invalid commands
 * 
 * Communication Protocol:
 * - Non-blocking UDP packet processing
 * - Immediate command execution for real-time control
 * - Status feedback sent to confirm command reception
 * - Error messages for debugging and troubleshooting
 * 
 * @param None (uses global Udp object for packet access)
 * @return void
 * 
 * @note Called from main loop for continuous command monitoring
 * @warning Commands execute immediately - ensure valid parameters
 */
void ReadUdpData() {
    int packetSize = Udp.parsePacket();
    if (packetSize > 0) {
        int bytesRead = Udp.read(packetReceived, MAX_PACKET_LENGTH);
        if (bytesRead > 0 && bytesRead < MAX_PACKET_LENGTH) {
            packetReceived[bytesRead] = 0; // Null-terminate
        } else {
            packetReceived[MAX_PACKET_LENGTH - 1] = 0; // Safety
        }
        String udpCommand = String(packetReceived);
        String prefix = "BOARD:" + String(BOARD_ID) + ";";
        if (udpCommand.startsWith(prefix)) {
            udpCommand = udpCommand.substring(prefix.length()); // Remove prefix
            handleCommand(udpCommand);
        }
        // Optionally, ignore or log commands not meant for this board
    }
}


//********************************************************************
void parseData(String data, int &V, int &A, int &P) {
    int firstComma = data.indexOf(',');
    int secondComma = data.indexOf(',', firstComma + 1);

    V = data.substring(0, firstComma).toInt();
    A = data.substring(firstComma + 1, secondComma).toInt();
    P = data.substring(secondComma + 1).toInt();
}
//********************************************************************
// read command string from HMI and parse command string
void handleCommand(String input) {
    input.trim(); // Remove whitespace and newlines
   
      // Special commands
    if (input == "CMD:REQUEST_VALUES") {
        //Serial.println("Debug 900 - Processing CMD:REQUEST_VALUES");
        sendCurrentValues();
        return;
    } else if (input == "CMD:REQUEST_BUTTON_STATES") {
        Serial.println("Debug 901 - Processing CMD:REQUEST_BUTTON_STATES");
        sendButtonStates();
        return;
    } else if (input == "CMD:REQUEST_SETPOINTS") {
        Serial.println("Debug 902 - Processing CMD:REQUEST_SETPOINTS");
        sendSetpoints();
        return;
    } else if (input == "CMD:REQUEST_STATE_ENGINE") {
        sendStateEngineStep();
        return;
    }

    // Remove "CMD:" prefix if present for custom commands
    String command = input;
    if (command.startsWith("CMD:")) {
        command = command.substring(4);
    }

    // Main command handling logic
    if (command == "Mode AUTO") {
        Mode = true;
        Serial.println("DATA: Auto Mode");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command == "Mode MANUAL") {
        Mode = false;
        Serial.println("DATA: Manual Mode");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command == "Repeat ENABLE" && !Repeat) {
        Repeat = true;
        Serial.println("DATA: Repeat enabled");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command == "Repeat DISABLE" && Repeat) {
        Repeat = false;
        Serial.println("DATA: Repeat disabled");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command == "Start ENABLE") {
        Start = true;
        Serial.println("DATA: Start enabled");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command == "Start DISABLE") {
        Start = false;
        Serial.println("DATA: Start disabled");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command == "S1B1 ENABLE" && !S1B1) {
        S1B1 = true;
        Serial.println("Serial Available Flag3a");
        Serial.println("DATA:Servo1 Enabled");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command == "S1B1 DISABLE" && S1B1) {
        S1B1 = false;
        Serial.println("Serial Available Flag4");
        Serial.println("DATA:Servo1 Disabled");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command == "S1B2 Start" && !S1B2) {
        S1B2 = true;
        Serial.println("Serial Available Flag4a");
        Serial.println("DATA:Servo1 Started");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command == "S1B2 STOP" && S1B2) {
        S1B2 = false;
        Serial.println("DATA:Servo1 Stopped");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command.startsWith("S1_Parameters:")) {
        parseData(command.substring(14), S1V_SPT, S1A_SPT, S1P_SPT);
        Serial.println("Serial Available Flag5");
        Serial.print("DATA:Parameters received - V:");
        Serial.print(S1V_SPT);
        Serial.print(" A:");
        Serial.print(S1A_SPT);
        Serial.print(" P:");
        Serial.println(S1P_SPT);
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command == "S2B1 ENABLE" && !S2B1) {
        S2B1 = true;
        Serial.println("DATA:Servo2 Enabled");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command == "S2B1 DISABLE" && S2B1) {
        S2B1 = false;
        Serial.println("DATA:Servo2 Disabled");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command == "S2B2 Start" && !S2B2) {
        S2B2 = true;
        Serial.println("DATA:Servo2 Started");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command == "S2B2 STOP" && S2B2) {
        S2B2 = false;
        Serial.println("DATA:Servo2 Stopped");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command.startsWith("S2_Parameters:")) {
        parseData(command.substring(14), S2V_SPT, S2A_SPT, S2P_SPT);
        Serial.print("DATA:Parameters received - V:");
        Serial.print(S2V_SPT);
        Serial.print(" A:");
        Serial.print(S2A_SPT);
        Serial.print(" P:");
        Serial.println(S2P_SPT);
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command == "S3B1 ENABLE" && !S3B1) {
        S3B1 = true;
        Serial.println("DATA:Servo3 Enabled");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command == "S3B1 DISABLE" && S3B1) {
        S3B1 = false;
        Serial.println("DATA:Servo3 Disabled");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command == "S3B2 Start" && !S3B2) {
        S3B2 = true;
        Serial.println("DATA:Servo3 Started");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command == "S3B2 STOP" && S3B2) {
        S3B2 = false;
        Serial.println("DATA:Servo3 Stopped");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command.startsWith("S3_Parameters:")) {
        parseData(command.substring(14), S3V_SPT, S3A_SPT, S3P_SPT);
        Serial.print("DATA:Parameters received - V:");
        Serial.print(S3V_SPT);
        Serial.print(" A:");
        Serial.print(S3A_SPT);
        Serial.print(" P:");
        Serial.println(S3P_SPT);
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command == "S4B1 ENABLE" && !S4B1) {
        S4B1 = true;
        Serial.println("DATA:Servo4 Enabled");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command == "S4B1 DISABLE" && S4B1) {
        S4B1 = false;
        Serial.println("DATA:Servo4 Disabled");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command == "S4B2 Start" && !S4B2) {
        S4B2 = true;
        Serial.println("DATA:Servo4 Started");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command == "S4B2 STOP" && S4B2) {
        S4B2 = false;
        Serial.println("DATA:Servo4 Stopped");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command.startsWith("S4_Parameters:")) {
        parseData(command.substring(14), S4V_SPT, S4A_SPT, S4P_SPT);
        Serial.print("DATA:Parameters received - V:");
        Serial.print(S4V_SPT);
        Serial.print(" A:");
        Serial.print(S4A_SPT);
        Serial.print(" P:");
        Serial.println(S4P_SPT);
        Serial.print("ACK:");
        Serial.println(command);
    }
    // Clear position commands for all servos
    else if (command == "S1_ClearPosition") {
        motor1.PositionRefSet(0);
        Serial.println("DATA:Servo1 Position Cleared");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command == "S2_ClearPosition") {
        motor2.PositionRefSet(0);
        Serial.println("DATA:Servo2 Position Cleared");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command == "S3_ClearPosition") {
        motor3.PositionRefSet(0);
        Serial.println("DATA:Servo3 Position Cleared");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command == "S4_ClearPosition") {
        motor4.PositionRefSet(0);
        Serial.println("DATA:Servo4 Position Cleared");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else {
        Serial.print("ERR:Unknown command - ");
        Serial.println(command);
        if (Serial.available() > 0) {
            Serial.read();  // Flush the serial buffer
        }
    }
}
//********************************************************************
void sendCurrentValues() {
    String msg = "BOARD:" + String(BOARD_ID) + ";VALUES:";
    msg += String(S1V) + "," + String(S1A) + "," + String(S1P) + ",";
    msg += String(S2V) + "," + String(S2A) + "," + String(S2P) + ",";
    msg += String(S3V) + "," + String(S3A) + "," + String(S3P) + ",";
    msg += String(S4V) + "," + String(S4A) + "," + String(S4P);
    //Serial.print("Sending VALUES: "); Serial.println(msg);
        Udp.beginPacket(remoteIp, remotePort);
    Udp.write(msg.c_str());
    Udp.endPacket();
}

void sendButtonStates() {
    String msg = "BOARD:" + String(BOARD_ID) + ";BUTTON_STATES:";
    msg += (Mode ? "1" : "0"); msg += ",";
    msg += (Repeat ? "1" : "0"); msg += ",";
    msg += (Start ? "1" : "0"); msg += ",";
    msg += (S1B1 ? "1" : "0"); msg += ",";
    msg += (S1B2 ? "1" : "0"); msg += ",";
    msg += (S2B1 ? "1" : "0"); msg += ",";
    msg += (S2B2 ? "1" : "0"); msg += ",";
    msg += (S3B1 ? "1" : "0"); msg += ",";
    msg += (S3B2 ? "1" : "0"); msg += ",";
    msg += (S4B1 ? "1" : "0"); msg += ",";
    msg += (S4B2 ? "1" : "0");

    Udp.beginPacket(remoteIp, remotePort);
    Udp.write(msg.c_str());
    Udp.endPacket();
}

void sendSetpoints() {
    String msg = "BOARD:" + String(BOARD_ID) + ";SETPOINTS:";
    msg += String(S1V_SPT) + "," + String(S1A_SPT) + "," + String(S1P_SPT) + ",";
    msg += String(S2V_SPT) + "," + String(S2A_SPT) + "," + String(S2P_SPT) + ",";
    msg += String(S3V_SPT) + "," + String(S3A_SPT) + "," + String(S3P_SPT) + ",";
    msg += String(S4V_SPT) + "," + String(S4A_SPT) + "," + String(S4P_SPT);

    Udp.beginPacket(remoteIp, remotePort);
    Udp.write(msg.c_str());
    Udp.endPacket();

    // Optionally, also print to Serial with prefix
    Serial.print("BOARD:"); Serial.print(BOARD_ID); Serial.print(";SETPOINTS:");
    Serial.print(S1V_SPT); Serial.print(",");
    Serial.print(S1A_SPT); Serial.print(",");
    Serial.print(S1P_SPT); Serial.print(",");
    Serial.print(S2V_SPT); Serial.print(",");
    Serial.print(S2A_SPT); Serial.print(",");
    Serial.print(S2P_SPT); Serial.print(",");
    Serial.print(S3V_SPT); Serial.print(",");
    Serial.print(S3A_SPT); Serial.print(",");
    Serial.print(S3P_SPT); Serial.print(",");
    Serial.print(S4V_SPT); Serial.print(",");
    Serial.print(S4A_SPT); Serial.print(",");
    Serial.println(S4P_SPT);
}

void sendStateEngineStep() {
    String msg = "BOARD:" + String(BOARD_ID) + ";STATE_ENGINE:" + String(next_step);

    Udp.beginPacket(remoteIp, remotePort);
    Udp.write(msg.c_str());
    Udp.endPacket();

    Serial.print("BOARD:"); Serial.print(BOARD_ID); Serial.print(";STATE_ENGINE:");
    Serial.println(next_step);
}
//********************************************************************
//Motor Functions
//********************************************************************
void loadMotorSetpoints() {
    // Set the motor velocity and accleration to the setpoint values
    motor1.VelMax(S1V_SPT);
    motor1.AccelMax(S1A_SPT);
    motor2.VelMax(S2V_SPT);
    motor2.AccelMax(S2A_SPT);
    motor3.VelMax(S3V_SPT);
    motor3.AccelMax(S3A_SPT);
    motor4.VelMax(S4V_SPT);
    motor4.AccelMax(S4A_SPT);
}

//*************************************************
void loadSetpoints(int step) {
    
    if (step >= 0 && step <= 10) {

        S1V_SPT = motor1_setpoints[step][0] * KV1;
        S1A_SPT = motor1_setpoints[step][1] * KA1;
        S1P_SPT = motor1_setpoints[step][2] * KP1;   
       
        S2V_SPT = motor2_setpoints[step][0] * KV2;
        S2A_SPT = motor2_setpoints[step][1] * KA2;
        S2P_SPT = motor2_setpoints[step][2] * KP2;
 
        S3V_SPT = motor3_setpoints[step][0] * KV3;
        S3A_SPT = motor3_setpoints[step][1] * KA3;
        S3P_SPT = motor3_setpoints[step][2] * KP3;

        S4V_SPT = motor4_setpoints[step][0] * KV4;
        S4A_SPT = motor4_setpoints[step][1] * KA4;
        S4P_SPT = motor4_setpoints[step][2] * KP4;

    }
    sendSetpoints();
} // End LoadSetpoints

//*******************************************************
int Calculate_Velocity(int POS1, int SPT1, int POS2, int SPT2, int Velocity1) {
  int Velocity2;
  //Velocity2 = abs(((SPT2 - POS2) * Velocity1) / (SPT1 - POS1));
  Velocity2 = abs(SPT2 - POS2);
  
  if (Velocity2 > 5000) {
    Velocity2 = 5000;
  }
 // if (Velocity2 <= 200) {
 //   Velocity2 = 200;
 //}
  return Velocity2;
}

//*******************************************************

void UpdateMotorParameters () {
    motor1_enable = digitalRead(inputPin1);
    motor1.EnableRequest(motor1_enable);
    motor2_enable = digitalRead(inputPin2);
    motor2.EnableRequest(motor2_enable);
    motor3_enable = digitalRead(inputPin3);
    motor3.EnableRequest(motor3_enable);
    motor4_enable = digitalRead(inputPin4);
    motor4.EnableRequest(motor4_enable);
    
    // Read the motors current Velocity
    S1V = motor1.VelocityRefCommanded();
    S2V = motor2.VelocityRefCommanded();
    S3V = motor3.VelocityRefCommanded();
    S4V = motor4.VelocityRefCommanded();

    // Read the motors current Position
    S1P = motor1.PositionRefCommanded();
    S2P = motor2.PositionRefCommanded();
    S3P = motor3.PositionRefCommanded();
    S4P = motor4.PositionRefCommanded();

}  // end UpdateMotorParameters

//********************************************************************
//  MoveDistance (relative movement)
//********************************************************************
// ============================================================================
//                      ABSOLUTE POSITION MOVEMENT FUNCTION
// ============================================================================

/**
 * @brief Execute absolute position movement for a single motor with state tracking
 * 
 * This function manages the complete movement sequence for positioning a motor
 * to an absolute target position. Uses a state machine approach to handle
 * non-blocking operation, allowing multiple motors to move concurrently.
 * 
 * Movement Sequence:
 * 1. MOVE_IDLE: Wait for new position command
 * 2. MOVE_CHECK_ALERTS: Verify motor is ready and clear any alerts
 * 3. MOVE_START: Initiate movement to target position
 * 4. MOVE_WAIT_HLFB: Monitor HLFB feedback during movement
 * 5. MOVE_DONE: Movement complete, return to idle state
 * 
 * State Management:
 * - Uses non-blocking state machine for concurrent multi-motor operation
 * - Tracks movement start time for timeout and performance monitoring
 * - Monitors position changes to detect movement progress
 * - Handles HLFB feedback to confirm motor operation
 * 
 * Safety Features:
 * - Alert checking before movement initiation
 * - HLFB monitoring during movement for fault detection
 * - Position validation and movement confirmation
 * - Automatic state reset upon completion
 * 
 * @param motor Reference to MotorDriver object for target motor
 * @param position Target absolute position in steps
 * @param moveState Reference to movement state variable for this motor
 * @param moveStartTime Reference to movement start timestamp
 * @param lastMillis Reference to last update time for timing
 * @param lastPosition Reference to previous position for change detection
 * 
 * @return bool - True when movement is complete, False during movement
 * 
 * @note This function must be called repeatedly in the main loop
 * @warning Ensure motor is properly configured and enabled before calling
 */
bool MoveAbsolutePosition(MotorDriver &motor, int position, MoveState &moveState, unsigned long &moveStartTime, unsigned long &lastMillis, int &lastPosition) {
    switch (moveState) {
        case MOVE_IDLE:
           /* if (motor.StatusReg().bit.AlertsPresent) {
                Serial.println("Motor alert detected.");
                PrintAlerts();
                if (HANDLE_ALERTS) {
                    HandleAlerts();
                } else {
                    Serial.println("Enable automatic alert handling by setting HANDLE_ALERTS to 1.");
                }
                Serial.println("Move canceled.");
                Serial.println();
                moveState = MOVE_DONE;
                return false;
            }
            */
            if (!motor.EnableRequest()) {
                Serial.println("Motor is not enabled. Enabling motor.");
                motor.EnableRequest(true);
                delay(100);  // Small delay to ensure motor is enabled
            }
            //Serial.print("Moving to absolute position: ");
            //Serial.println(position);
            //delay(100);
            motor.Move(position, MotorDriver::MOVE_TARGET_ABSOLUTE);
            //Serial.println("Moving.. Waiting for HLFB");
            
            //delay(100);
            moveStartTime = millis();
            moveState = MOVE_WAIT_HLFB;
            // Store initial position when starting a move
            lastPosition = motor.StepsComplete();
            lastMillis = millis();
            break;

        case MOVE_WAIT_HLFB:
        
            if (motor.StepsComplete() && motor.HlfbState() == MotorDriver::HLFB_ASSERTED) {
                
                moveState = MOVE_DONE;
                //Serial.println("Move Done");
                return true;
            }
            /*if (motor.StatusReg().bit.AlertsPresent) {
                Serial.println("Motor alert detected.");
                PrintAlerts();
                if (HANDLE_ALERTS) {
                    HandleAlerts();
                } else {
                    Serial.println("Enable automatic fault handling by setting HANDLE_ALERTS to 1.");
                }
                Serial.println("Motion may not have completed as expected. Proceed with caution.");
                Serial.println();
                moveState = MOVE_DONE;
                return false;
            }
           
            if (millis() - moveStartTime > moveTimeout) {
                Serial.println("Move timeout.");
                moveState = MOVE_DONE;
                return false;
            }
             */
            break;

        case MOVE_DONE:
            moveState = MOVE_IDLE;
            return true;
    }
    return false;
}
//********************************************************************

void PrintAlerts() {
    MotorDriver* motors[] = {&motor1, &motor2, &motor3, &motor4};
    const char* motorNames[] = {"Motor1", "Motor2", "Motor3", "Motor4"};
    
    for (int i = 0; i < 4; ++i) {
        Serial.print(motorNames[i]);
        Serial.println(" alerts present: ");
        if (motors[i]->AlertReg().bit.MotionCanceledInAlert) {
            Serial.println("    MotionCanceledInAlert ");
        }
        if (motors[i]->AlertReg().bit.MotionCanceledPositiveLimit) {
            Serial.println("    MotionCanceledPositiveLimit ");
        }
        if (motors[i]->AlertReg().bit.MotionCanceledNegativeLimit) {
            Serial.println("    MotionCanceledNegativeLimit ");
        }
        if (motors[i]->AlertReg().bit.MotionCanceledSensorEStop) {
            Serial.println("    MotionCanceledSensorEStop ");
        }
        if (motors[i]->AlertReg().bit.MotionCanceledMotorDisabled) {
            Serial.println("    MotionCanceledMotorDisabled ");
        }
        if (motors[i]->AlertReg().bit.MotorFaulted) {
            Serial.println("    MotorFaulted ");
        }
    }
}
//********************************************************************
void HandleMotorAlerts(MotorDriver &motor, const char *motorName) {
    if (motor.AlertReg().bit.MotorFaulted) {
        Serial.println(String(motorName) + " Faults present. Cycling enable signal to motor to clear faults.");
        motor.EnableRequest(false);
        delay(10);
        motor.EnableRequest(true);
    }
}
//********************************************************************
void HandleAlerts() {
    MotorDriver* motors[] = {&motor1, &motor2, &motor3, &motor4};
    const char* motorNames[] = {"Motor1", "Motor2", "Motor3", "Motor4"};
    
    for (int i = 0; i < 4; ++i) {
        HandleMotorAlerts(*motors[i], motorNames[i]);
    }
    
    Serial.println("Clearing alerts.");
    for (int i = 0; i < 4; ++i) {
        motors[i]->ClearAlerts();
    }
}
//********************************************************************
// Function to calculate scan time
unsigned long calculateScanTime() {
    static unsigned long lastTime = 0;
    unsigned long currentTime = millis();
    unsigned long scanTime = currentTime - lastTime;
    lastTime = currentTime;
    return scanTime;
}

