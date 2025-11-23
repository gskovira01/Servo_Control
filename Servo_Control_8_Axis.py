"""
================================================================================
                         SERVO CONTROL SYSTEM - REVISION 34
                    Per-Servo Numeric Keypad Limits & UI Improvements
================================================================================

PURPOSE:
    Touchscreen GUI interface for controlling dual ClearCore servo controllers
    over UDP network communication. Designed for industrial automation with
    robust error handling and cross-platform deployment capabilities.

HARDWARE ARCHITECTURE:
    - ClearCore Controller 1: 192.168.1.151:8888 (Board 1 servos)
    - ClearCore Controller 2: 192.168.1.152:8890 (Board 2 servos)
    - Host System: Windows development / Raspberry Pi deployment
    - Network: Dedicated Ethernet subnet (192.168.1.x) for servo control
    - Interface: Touchscreen optimized GUI with numeric keypad

RECENT ENHANCEMENTS (Rev 34):
    ✅ Numeric keypad popup now enforces per-servo POSITION_LIMITS for position setpoints
    ✅ Prevents entry of values above allowed range for each servo (e.g., 300 for servo 4)
    ✅ All previous network error handling and UI improvements retained

DEPLOYMENT SCENARIOS:
    1. Production: Full network connectivity, normal operation
    2. Development: Single controller available, partial functionality
    3. Debug Mode: No controllers, GUI testing and interface validation

CROSS-PLATFORM SUPPORT:
    - Windows: Development environment, firewall considerations
    - Raspberry Pi: Production deployment, autostart service, shutdown button

NETWORK TOPOLOGY:
    [Host] ←→ [Ethernet Switch] ←→ [ClearCore 1] and/or [ClearCore 2]
           ↓
    [WiFi Router] (Internet access, separate subnet 192.168.1.x)

AUTHORS: Greg Skovira
VERSION: Rev 34 (Numeric Keypad Per-Servo Limits)
DATE: November 23, 2025
LICENSE: Internal Use Only

================================================================================
                            CLASSES AND FUNCTIONS INVENTORY
================================================================================

CLASSES:
    UDPReceiverThread           - Background UDP message receiver thread for real-time communication
                                  with dual ClearCore controllers, handles continuous listening
                                  and thread-safe message queuing for GUI processing
    
CORE COMMUNICATION FUNCTIONS:
    send_udp_command1()         - Send command to ClearCore Controller 1 (Board 1, 192.168.10.171:8888)
    send_udp_command2()         - Send command to ClearCore Controller 2 (Board 2, 192.168.10.172:8890)
    check_network_connectivity() - Cross-platform network reachability test with Windows/Linux ping
                                  adaptation, supports partial connectivity for development scenarios
    
INITIALIZATION FUNCTIONS:
    initialize_buttons()        - Synchronize button states with ClearCore hardware at startup,
                                  establishes consistent GUI/hardware state with retry logic
    initialize_setpoints()      - Retrieve servo configuration parameters from controllers,
                                  synchronizes GUI display with actual hardware setpoint values
    initialize_state_engine()   - Initialize application state machine and controller coordination
    initialize_from_arduino()   - Master initialization function coordinating all startup sequences
    
MESSAGE PROCESSING FUNCTIONS:
    process_incoming_messages() - Parse and route incoming UDP messages from both controllers
    process_button_states_response() - Handle button state feedback from ClearCore hardware,
                                     updates GUI button appearance and internal state tracking
    process_setpoints_response() - Handle setpoint configuration data from controllers,
                                  updates local parameter storage and GUI display values
    process_values_response()   - Handle real-time servo feedback (velocity/acceleration/position)
                                 updates position displays for all 8 servos across dual boards
    process_response()          - Message routing dispatcher for different response types
    process_state_engine_response() - Handle state machine status updates from controllers
    
GUI CONSTRUCTION FUNCTIONS:
    build_board_panel()         - Create servo control panel for each board (4 servos per panel)
                                 generates complete interface with setpoint buttons, displays,
                                 and control elements for velocity/acceleration/position control
    show_numeric_keypad()       - Touchscreen-optimized numeric input interface with validation,
                                 provides large button layout for industrial touch applications
    show_confirmation_popup()   - Modal confirmation dialogs for critical operations
    create_loading_window()     - Generate fresh loading screen to prevent GUI element reuse
                                 bugfix for retry functionality in network error scenarios
    
ENHANCED ERROR HANDLING:
    show_network_error_dialog() - Three-way network error dialog with Retry/Continue/Exit options,
                                 replaces old binary dialog to enable debug mode operation
    show_communication_status_popup() - Post-startup communication status notification for debug mode,
                                      provides clear feedback when running without hardware
    
SERVO CONTROL FUNCTIONS:
    handle_servo_buttons()      - Process servo button interactions and state changes,
                                 manages Mode/Repeat/Start controls and servo enable/disable
    validate_input()           - Ensure servo parameters within safe operational limits,
                                prevents hardware damage from invalid setpoint values
    
SYSTEM FUNCTIONS (RASPBERRY PI):
    shutdown_system()           - Safe system shutdown with confirmation dialog,
                                 Raspberry Pi specific functionality for production deployment
    
EVENT HANDLERS:
    handle_button_events()      - Process GUI button interactions across dual board interface
    handle_numeric_input()      - Process numeric keypad input with range validation
    handle_system_events()      - Process system-level events including window close and shutdown
    
UTILITY FUNCTIONS:
    update_gui_elements()       - Refresh GUI display with current servo feedback values
    validate_input_ranges()     - Ensure all servo parameters within manufacturer specifications
    format_display_values()     - Format numeric values for consistent GUI presentation
    
MAIN APPLICATION:
    main()                      - Primary application entry point and event loop,
                                 coordinates initialization, network checking, GUI creation,
                                 and continuous event processing for 8-axis servo control

TOTAL: 1 Class, 25+ Functions across 1300+ lines of code

KEY DATA STRUCTURES:
    UDPReceiverThread           - Background UDP message receiver thread
    
CORE COMMUNICATION FUNCTIONS:
    send_udp_command1()         - Send command to ClearCore Controller 1
    send_udp_command2()         - Send command to ClearCore Controller 2
    check_network_connectivity() - Cross-platform network reachability test
    
INITIALIZATION FUNCTIONS:
    initialize_buttons()        - Sync button states with ClearCore hardware
    initialize_setpoints()      - Retrieve servo configuration from controllers
    initialize_state_engine()   - Initialize application state machine
    
MESSAGE PROCESSING FUNCTIONS:
    process_incoming_messages() - Parse and route incoming UDP messages
    process_button_states_response() - Handle button state feedback
    process_setpoints_response() - Handle setpoint configuration data
    process_values_response()   - Handle real-time servo feedback values
    
GUI CONSTRUCTION FUNCTIONS:
    build_board_panel()         - Create servo control panel for each board
    show_numeric_keypad()       - Touchscreen numeric input interface
    show_confirmation_popup()   - Modal confirmation dialogs
    
ENHANCED ERROR HANDLING:
    show_network_error_dialog() - Three-way network error dialog (Retry/Continue/Exit)
    show_communication_status_popup() - Post-startup communication status
    create_loading_window()     - Generate fresh loading screen (prevents element reuse)
    
SYSTEM FUNCTIONS (RASPBERRY PI):
    shutdown_system()           - Safe system shutdown with confirmation
    
EVENT HANDLERS:
    handle_button_events()      - Process GUI button interactions  
    handle_numeric_input()      - Process numeric keypad input
    handle_system_events()      - Process system-level events
    
UTILITY FUNCTIONS:
    update_gui_elements()       - Refresh GUI display with current values
    validate_input_ranges()     - Ensure servo parameters within safe limits
    format_display_values()     - Format numeric values for display
    
MAIN APPLICATION:
    main()                      - Primary application entry point and event loop

TOTAL: 1 Class, 25+ Functions across 1300+ lines of code

KEY DATA STRUCTURES:
    arduino_values_1/2          - Real-time servo feedback (V/A/P per servo)
    setpoint_values_1/2         - User-configured motion parameters  
    GUI_button_states_1/2       - GUI button press tracking
    CNT_button_states_1/2       - Hardware button state mirrors
    message_queue               - Thread-safe UDP message queue
    
CRITICAL CONSTANTS:
    CLEARCORE1_IP = '192.168.10.171'    - Primary controller address
    CLEARCORE2_IP = '192.168.10.172'    - Secondary controller address  
    WINDOW_READ_TIMEOUT = 100           - GUI responsiveness (ms)
    IS_WINDOWS / IS_RASPBERRY_PI        - Platform detection flags
    network_error_message               - Debug mode error storage

================================================================================
                               REVISION HISTORY
================================================================================

Rev 32 - November 9, 2025 - Professional Git Repository Setup & Deployment Workflow
    ✅ MAJOR: Complete Git version control implementation replacing memory stick transfers
    ✅ MAJOR: Professional development workflow with Windows→Raspberry Pi deployment
    ✅ ENHANCEMENT: Created comprehensive .gitignore file for Python projects
    ✅ ENHANCEMENT: Added README.md with project documentation and setup instructions
    ✅ ENHANCEMENT: Created Git_Setup_Guide.md with step-by-step deployment instructions
    ✅ ENHANCEMENT: Added deployment and version control documentation to program header
    ✅ ENHANCEMENT: Established foundation for GitHub/GitLab repository hosting

Rev 31 - November 9, 2025 - 8-Axis Expansion & Dual Board Architecture  
    ✅ MAJOR: Complete 8-axis servo control system implementation
    ✅ MAJOR: Dual ClearCore board architecture (Board 1: Servos 1-4, Board 2: Servos 5-8)
    ✅ MAJOR: Expanded data structures for dual board operation (arduino_values_1/2, setpoint_values_1/2)
    ✅ MAJOR: Dual-tab GUI interface for clean 8-servo organization 
    ✅ MAJOR: Independent UDP communication channels (171:8888, 172:8890)
    ✅ ENHANCEMENT: Comprehensive class and function inventory documentation
    ✅ ENHANCEMENT: Detailed program header with architecture specifications
    ✅ ENHANCEMENT: Cross-platform font standardization (Courier New) for alignment consistency
    ✅ ENHANCEMENT: Enhanced board panel generation for scalable servo control
    ✅ ENHANCEMENT: Coordinated ClearCore firmware integration for dual-board operation

Rev 30 - October 29, 2025 - Enhanced Network Error Handling & Documentation
    ✅ MAJOR: Added "Continue Anyway" option to network error dialog
    ✅ MAJOR: Implemented persistent error warning bar in debug mode  
    ✅ MAJOR: Added communication status popup after GUI loads
    ✅ BUGFIX: Fixed GUI element reuse error on retry functionality
    ✅ ENHANCEMENT: Comprehensive code documentation and commenting
    ✅ ENHANCEMENT: Added function/class inventory and revision history
    ✅ ENHANCEMENT: Improved error dialog from "Error" to "Warning" with color coding
    ✅ ENHANCEMENT: Three-state error handling (Retry/Continue/Exit) vs old binary
    
Rev 29 - October 2025 - Cross-Platform Compatibility & Autostart
    ✅ MAJOR: Cross-platform network connectivity testing (Windows/Linux ping syntax)
    ✅ MAJOR: Raspberry Pi autostart service integration  
    ✅ MAJOR: System shutdown button with confirmation dialog (Pi only)
    ✅ ENHANCEMENT: Platform detection and adaptive behavior
    ✅ ENHANCEMENT: Desktop shortcut creation guidance
    ✅ BUGFIX: Network routing conflicts resolved (WiFi vs Ethernet subnets)
    
Rev 28 - October 2025 - Network Architecture & Dual Controller Support  
    ✅ MAJOR: Dual ClearCore controller communication (171 & 172)
    ✅ MAJOR: Flexible network connectivity (success if one controller reachable)
    ✅ ENHANCEMENT: UDP socket reuse and timeout configuration
    ✅ ENHANCEMENT: Thread-safe message queuing system
    ✅ ENHANCEMENT: Improved error logging and debug output
    
Rev 27 - September 2025 - GUI Enhancements & Touchscreen Optimization
    ✅ MAJOR: Touchscreen-optimized interface with larger controls
    ✅ MAJOR: Custom numeric keypad for value input
    ✅ ENHANCEMENT: Tab-based layout for dual board control
    ✅ ENHANCEMENT: Real-time servo feedback display
    ✅ ENHANCEMENT: Button state synchronization with hardware
    
Rev 26 - August 2025 - Initial Production Release
    ✅ MAJOR: Basic servo control interface with FreeSimpleGUI
    ✅ MAJOR: UDP communication with single ClearCore controller
    ✅ MAJOR: Multi-servo control (4 servos per board)
    ✅ ENHANCEMENT: Basic error handling and timeout protection
    ✅ ENHANCEMENT: Setpoint configuration and storage

ARCHITECTURE EVOLUTION:
    Rev 26-27: Single board, 4-servo foundation with basic GUI
    Rev 28-29: Network robustness and cross-platform deployment
    Rev 30: Advanced error handling and debug mode capabilities  
    Rev 31: Complete 8-axis expansion with dual-board coordination

CURRENT SYSTEM CAPABILITIES:
    ✅ 8-Axis Servo Control: Complete velocity/acceleration/position control
    ✅ Dual Board Architecture: Independent ClearCore board coordination  
    ✅ Cross-Platform Operation: Windows development, Raspberry Pi deployment
    ✅ Advanced Error Handling: Graceful degradation and debug mode
    ✅ Industrial Interface: Touchscreen-optimized with numeric keypad
    ✅ Real-Time Communication: UDP messaging with thread-safe queuing
    ✅ Network Resilience: Partial connectivity support and automatic recovery

DEPLOYMENT & VERSION CONTROL:
    📋 RECOMMENDED: Git Repository Setup for Professional Development Workflow
    
    SETUP INSTRUCTIONS:
    1. Initialize Git repository: git init
    2. Create .gitignore file for Python projects
    3. Add remote repository (GitHub/GitLab recommended)
    4. Push to repository: git add . && git commit -m "Initial servo control project"
    
    DEVELOPMENT WORKFLOW:
    • Windows Development: Edit code, test with debug mode
    • Git Commit: Regular commits with descriptive messages
    • Repository Push: Backup and share changes
    • Raspberry Pi Deployment: git clone <repo-url> or git pull for updates
    
    BENEFITS:
    ✅ No more memory stick transfers - direct network deployment
    ✅ Complete version history and change tracking
    ✅ Easy rollback to previous working versions
    ✅ Collaborative development support
    ✅ Automatic backup of all project files
    ✅ Professional development practices

PLANNED FUTURE ENHANCEMENTS:
    🔄 Data logging and motion history tracking
    🔄 Advanced motion profiles and trajectory planning  
    🔄 Remote monitoring and control capabilities
    🔄 Configuration backup and restore functionality
    🔄 Performance metrics and diagnostics dashboard
    🔄 Multi-axis coordinated motion sequences
    🔄 Safety interlocks and emergency stop integration
    🔄 Recipe-based automation and job scheduling

================================================================================
"""
# ============================================================================
#                              IMPORT SECTION
# ============================================================================

from operator import add                    # Mathematical operations support
# import PySimpleGUI as sg # type: ignore  # Original GUI library (deprecated)
import FreeSimpleGUI as sg                 # Free GUI library for cross-platform interface
import socket                              # UDP network communication with ClearCore
import threading                           # Background UDP listener thread
import queue                               # Thread-safe communication between GUI and network
import time                                # Timing operations and delays
import sys                                 # System operations and application exit
import subprocess                          # Network connectivity testing (ping commands)
import platform                            # Cross-platform OS detection and adaptation

# =========================
# GLOBAL CONFIGURATION
# =========================
# Per-servo position limits: {servo_number: (min, max)}
POSITION_LIMITS = {
    1: (0, 180),
    2: (0, 180),
    3: (0, 180),
    4: (0, 180),
    5: (0, 180),
    6: (0, 180),
    7: (0, 180),
    8: (0, 180),
}

# Global font setting for consistent cross-platform alignment
GLOBAL_FONT = ('Courier New', 10)
# Smaller font for "Clear Value" buttons to fit text on one line
CLEAR_BUTTON_FONT = ('Courier New', 9)
# Bold font for "Position X" labels - same size as global font for alignment consistency
POSITION_LABEL_FONT = ('Courier New', 10, 'bold')

# ============================================================================
#                         PLATFORM DETECTION & CONFIGURATION
# ============================================================================

# Cross-platform compatibility flags
IS_WINDOWS = platform.system() == "Windows"      # Windows development environment
IS_RASPBERRY_PI = platform.system() == "Linux" and platform.machine().startswith('arm')  # Pi deployment

# ============================================================================
#                              GLOBAL STATE VARIABLES
# ============================================================================

# State machine controller
state_engine_step = 0                            # Main application state tracker

# Enhanced network error handling system
# Allows application startup even with ClearCore communication failures
network_error_message = None                     # None = normal operation
                                                 # String = error msg for debug mode display

# Debug system hierarchy (multiple priority levels for development)
DEBUG = False                                    # Master debug flag
DEBUG00 = False                                 # Legacy debug flag
DEBUG_LOW_PRIORITY = False                      # Low importance debug messages
DEBUG_MEDIUM_PRIORITY = False                   # Medium importance debug messages  
DEBUG_HIGH_PRIORITY = False                     # Critical debug messages

# ============================================================================
#                              TIMING CONSTANTS
# ============================================================================

# GUI responsiveness and update intervals
WINDOW_READ_TIMEOUT = 100                       # GUI event loop timeout (ms)
MEDIUM_PRIORITY_UPDATE_INTERVAL = 0.1           # Medium priority task interval (seconds)
LOW_PRIORITY_UPDATE_INTERVAL = 0.1              # Low priority task interval (seconds)

# Communication and user interface timing
BATCH_SIZE = 30                                 # Network packet batching size
DEBOUNCE_INTERVAL = 0.05                        # Button debounce protection (seconds)

# ============================================================================
#                          NETWORK CONFIGURATION & UDP SETUP
# ============================================================================

# ClearCore Controller Network Addresses
# Dedicated Ethernet subnet (192.168.10.x) isolated from internet traffic
CLEARCORE1_IP = '192.168.1.151'               # Primary controller (Board 1 servos)
CLEARCORE1_PORT = 8888                         # ClearCore 1 listening port
LOCAL_PORT1 = 8889                             # Local port for ClearCore 1 communication

CLEARCORE2_IP = '192.168.1.152'               # Secondary controller (Board 2 servos) 
CLEARCORE2_PORT = 8890                         # ClearCore 2 listening port
LOCAL_PORT2 = 8889                             # Local port for ClearCore 2 communication

# Network Architecture Notes:
# - ClearCore controllers use fixed IP addresses for reliable communication
# - Separate subnet prevents conflicts with WiFi/internet (192.168.1.x)
# - UDP protocol chosen for low-latency real-time servo control
# - Bidirectional communication: commands out, status feedback in

# ============================================================================
#                              UDP SOCKET INITIALIZATION  
# ============================================================================

# Single UDP socket handles communication with both ClearCore controllers
# Socket reuse allows rapid application restart without "address in use" errors
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Create UDP socket
udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Enable address reuse
udp_sock.bind(('', 8889))                            # Bind to all interfaces, port 8889
udp_sock.settimeout(0.1)                                # Short timeout for responsive thread shutdown

# ============================================================================
#                         THREAD-SAFE MESSAGE QUEUE
# ============================================================================

# Queue for thread-safe communication between UDP receiver and GUI thread
message_queue = queue.Queue()                          # Incoming ClearCore messages

# ============================================================================
#                         UDP RECEIVER BACKGROUND THREAD
# ============================================================================

class UDPReceiverThread(threading.Thread):
    """
    Background thread for receiving UDP messages from ClearCore controllers.
    
    Runs continuously in background, listening for status updates and responses
    from both ClearCore controllers. Messages are queued for processing by
    the main GUI thread to maintain thread safety.
    
    Features:
    - Non-blocking operation with timeout
    - Graceful shutdown capability  
    - Thread-safe message queuing
    - Automatic message parsing and routing
    """
    
    def __init__(self, udp_sock, message_queue):
        super().__init__(name="UDP-Receiver")           # Named thread for debugging
        self.udp_sock = udp_sock                        # Shared UDP socket
        self.message_queue = message_queue              # Thread-safe message queue
        self.running = True                             # Thread control flag
        self.daemon = True                              # Allow main program to exit

    def run(self):
        """Main thread loop - continuously listen for UDP messages."""
        while self.running:
            try:
                # Listen for incoming messages with timeout
                data, addr = self.udp_sock.recvfrom(1024)      # Max 1KB message size
                message = data.decode('utf-8').strip()         # Convert bytes to string
                
                if message:  # Only queue non-empty messages
                    self.message_queue.put(message)             # Thread-safe message queuing
                    
            except socket.timeout:
                # Normal timeout - allows periodic check of running flag
                continue
            except Exception as e:
                # Network error - log and terminate thread
                print(f"UDP receive error: {e}")
                self.running = False

    def stop(self):
        """Gracefully stop the UDP receiver thread."""
        self.running = False

# ============================================================================
#                         UDP THREAD INITIALIZATION & COMMAND FUNCTIONS
# ============================================================================

# Start the background UDP receiver thread
udp_thread = UDPReceiverThread(udp_sock, message_queue)
udp_thread.start()                                      # Begin listening for messages

def send_udp_command1(cmd):
    """
    Send command to ClearCore Controller 1 (Board 1).
    
    Args:
        cmd (str): Command string to send to ClearCore 1
    """
    udp_sock.sendto(cmd.encode('utf-8'), (CLEARCORE1_IP, CLEARCORE1_PORT))

def send_udp_command2(cmd):
    """
    Send command to ClearCore Controller 2 (Board 2).
    
    Args:
        cmd (str): Command string to send to ClearCore 2  
    """
    udp_sock.sendto(cmd.encode('utf-8'), (CLEARCORE2_IP, CLEARCORE2_PORT))

# ============================================================================
#                       NETWORK CONNECTIVITY TESTING
# ============================================================================

def check_network_connectivity():
    """
    Test network connectivity to ClearCore controllers using platform-specific ping.
    
    This function performs cross-platform network reachability testing to both
    ClearCore controllers. Success requires at least one controller to respond,
    allowing partial operation when only one controller is available.
    
    Platform Adaptations:
    - Windows: Uses 'ping -n 1 -w 3000' syntax
    - Linux/Pi: Uses 'ping -c 1 -W 3' syntax
    
    Returns:
        tuple: (success_bool, message_string)
            - success_bool: True if at least one controller reachable
            - message_string: Detailed status or error description
            
    Failure Scenarios:
    - No controllers respond to ping
    - Network interface down
    - Subnet routing issues
    - Controller power/network failures
    """
    try:
        # Cross-platform ping command configuration
        if platform.system() == "Windows":
            # Windows ping syntax: count=1, timeout=3000ms
            ping_cmd = ['ping', '-n', '1', '-w', '3000']
        else:
            # Linux/Raspberry Pi ping syntax: count=1, timeout=3s  
            ping_cmd = ['ping', '-c', '1', '-W', '3']
        
        # Debug logging for troubleshooting
        print(f"Debug: Platform detected as {platform.system()}")
        print(f"Debug: Using ping command: {ping_cmd}")
        
        # Flexible connectivity test - partial success acceptable
        # This allows operation with single controller for development/debugging
        reachable_controllers = []                       # Successfully pinged controllers
        unreachable_controllers = []                     # Failed ping attempts
        
        # Test connectivity to both ClearCore controllers
        for ip in [CLEARCORE1_IP, CLEARCORE2_IP]:
            full_cmd = ping_cmd + [ip]                   # Build complete ping command
            print(f"Debug: Running command: {' '.join(full_cmd)}")
            
            # Execute ping with timeout protection
            result = subprocess.run(full_cmd, 
                                  capture_output=True,   # Suppress console output
                                  timeout=10,            # 10 second max per ping
                                  text=True)             # Return string output
            
            print(f"Debug: Return code for {ip}: {result.returncode}")
            
            # Parse ping results (return code 0 = success)
            if result.returncode == 0:
                reachable_controllers.append(ip)
                print(f"Debug: {ip} is reachable")
            else:
                unreachable_controllers.append(ip)
                print(f"Debug: {ip} is not reachable")
        
        # Evaluate overall connectivity status
        # Success criteria: At least one controller must respond
        if reachable_controllers:
            if unreachable_controllers:
                # Partial connectivity - some controllers unavailable
                message = f"Network connectivity OK. Reachable: {', '.join(reachable_controllers)}. Unreachable: {', '.join(unreachable_controllers)}"
            else:
                # Full connectivity - all controllers available
                message = "Network connectivity OK. All controllers reachable."
            return True, message
        else:
            # Complete failure - no controllers reachable
            return False, f"Cannot reach any ClearCore controllers. Tried: {', '.join([CLEARCORE1_IP, CLEARCORE2_IP])}"
        
    except subprocess.TimeoutExpired:
        # Ping process exceeded timeout limit
        return False, "Network check timed out"
    except Exception as e:
        # Unexpected error during network testing
        return False, f"Network check error: {str(e)}"

def show_network_error_dialog(message):
    """
    Show network error dialog with three user options:
    - 'retry': Try network check again
    - 'continue': Start application anyway (debugging mode) 
    - 'exit': Close application
    
    This replaces the old binary retry/exit dialog to allow debugging
    when ClearCore controllers are not available.
    """
    # Platform-specific troubleshooting tips
    if IS_WINDOWS:
        platform_tips = [
            '• Check Windows Firewall settings',
            '• Verify Ethernet adapter has IP 192.168.10.x',
            '• Check Norton/antivirus firewall settings',
            '• Ensure at least one ClearCore is powered on'
        ]
    else:
        platform_tips = [
            '• Check if eth0 interface is up: ip addr show eth0',
            '• Verify route exists: ip route show | grep 192.168.10',
            '• Check systemd network service status',
            '• Ensure at least one ClearCore is powered on'
        ]
    
    # Updated dialog layout: Changed from "Error" to "Warning" to reflect
    # that the application can now continue without network connectivity
    layout = [
        [sg.Text('Network Connectivity Warning', font=GLOBAL_FONT, text_color='orange')],
        [sg.Text('ClearCore communication issue detected:', font=GLOBAL_FONT)],
        [sg.Text(message, font=GLOBAL_FONT, text_color='darkred')],
        [sg.Text('Please check:', font=GLOBAL_FONT)],
        [sg.Text('• Ethernet cable connection to ClearCore controllers', font=GLOBAL_FONT)],
        [sg.Text('• ClearCore controllers are powered on', font=GLOBAL_FONT)],
        [sg.Text('• ClearCore IP addresses (171, 172)', font=GLOBAL_FONT)],
    ] + [[sg.Text(tip, font=GLOBAL_FONT)] for tip in platform_tips] + [
        # NEW: Inform user that debugging is possible without network
        [sg.Text('You can continue to use the interface for debugging:', font=GLOBAL_FONT)],
        # NEW: Three-button layout with color coding:
        # Green = Retry (preferred), Yellow = Continue (caution), Red = Exit (stop)
        [sg.Button('Retry', size=(10, 1), button_color=('black', 'lightgreen'), font=GLOBAL_FONT), 
         sg.Button('Continue Anyway', size=(15, 1), button_color=('black', 'yellow'), font=GLOBAL_FONT),
         sg.Button('Exit', size=(10, 1), button_color=('white', 'red'), font=GLOBAL_FONT)]
    ]
    
    error_window = sg.Window('Network Warning', layout, 
                           keep_on_top=True, modal=True, finalize=True,
                           location=(50, 50))
    
    # NEW: Three-state return values replace old boolean retry/exit logic
    # Returns string values for clearer handling in main program
    while True:
        event, values = error_window.read()
        if event in (sg.WIN_CLOSED, 'Exit'):
            error_window.close()
            return 'exit'       # Close application
        elif event == 'Retry':
            error_window.close()
            return 'retry'      # Try network check again
        elif event == 'Continue Anyway':
            error_window.close()
            return 'continue'   # Start app with network error (debug mode)

def show_communication_status_popup(error_message):
    """
    Show informational popup after GUI loads when running in debug mode.
    
    This popup appears AFTER the main GUI is displayed to provide clear
    status information about the communication failure and explain that
    the interface is still functional for testing/debugging purposes.
    
    Args:
        error_message (str): The network error message to display
    """
    layout = [
        [sg.Text('Communication Status', font=GLOBAL_FONT, text_color='orange')],
        [sg.Text('🔧 DEBUG MODE ACTIVE 🔧', font=GLOBAL_FONT, 
                text_color='red', justification='center')],
        [sg.Text('ClearCore Communication:', font=GLOBAL_FONT)],
        [sg.Text('❌ Failed to establish connection', font=GLOBAL_FONT, text_color='red')],
        [sg.Text(f'   {error_message}', font=GLOBAL_FONT, text_color='darkred')],
        [sg.Text('Interface Status:', font=GLOBAL_FONT)],
        [sg.Text('✅ GUI fully functional for testing', font=GLOBAL_FONT, text_color='green')],
        [sg.Text('✅ All controls available for debugging', font=GLOBAL_FONT, text_color='green')],
        [sg.Text('Note: Servo commands will not be sent to hardware', 
                font=GLOBAL_FONT, text_color='darkblue')],
        [sg.Button('Continue', size=(12, 1), button_color=('black', 'lightblue'), font=GLOBAL_FONT)]
    ]
    
    status_window = sg.Window('Communication Status', layout, 
                            keep_on_top=True, modal=True, finalize=True,
                            location=(50, 50))
    
    # Wait for user acknowledgment
    while True:
        event, values = status_window.read()
        if event in (sg.WIN_CLOSED, 'Continue'):
            status_window.close()
            break

# ============================================================================
#                         SERVO CONTROL DATA STRUCTURES
# ============================================================================

# Real-time servo feedback values from ClearCore controllers
# These dictionaries store current position, velocity, and acceleration readings
# Updated continuously via UDP messages from hardware controllers
arduino_values_1 = {
    # Servo 1 feedback: Velocity, Acceleration, Position
    'S1V': '0', 'S1A': '0', 'S1P': '0',
    # Servo 2 feedback: Velocity, Acceleration, Position  
    'S2V': '0', 'S2A': '0', 'S2P': '0',
    # Servo 3 feedback: Velocity, Acceleration, Position
    'S3V': '0', 'S3A': '0', 'S3P': '0',
    # Servo 4 feedback: Velocity, Acceleration, Position
    'S4V': '0', 'S4A': '0', 'S4P': '0'
}
arduino_values_2 = {
    # Servo 5 feedback: Velocity, Acceleration, Position
    'S1V': '0', 'S1A': '0', 'S1P': '0',  # Board 2 Servo 1 (Overall Servo 5)
    # Servo 6 feedback: Velocity, Acceleration, Position  
    'S2V': '0', 'S2A': '0', 'S2P': '0',  # Board 2 Servo 2 (Overall Servo 6)
    # Servo 7 feedback: Velocity, Acceleration, Position
    'S3V': '0', 'S3A': '0', 'S3P': '0',  # Board 2 Servo 3 (Overall Servo 7)
    # Servo 8 feedback: Velocity, Acceleration, Position
    'S4V': '0', 'S4A': '0', 'S4P': '0'   # Board 2 Servo 4 (Overall Servo 8)
}

# User-configured setpoint values for servo motion control
# These values are sent to ClearCore controllers to command servo movements  
# Default values provide safe starting configuration
setpoint_values_1 = {
    # System control parameters
    'Mode': 0,          # Operation mode selector
    'Repeat': 0,        # Repeat motion flag
    'Start': 0,         # Motion start trigger
    
    # Servo 1 setpoints: Velocity, Acceleration, Position (safe defaults)
    'S1V_SPT': 1000, 'S1A_SPT': 1000, 'S1P_SPT': 0,
    # Servo 2 setpoints: Velocity, Acceleration, Position
    'S2V_SPT': 1000, 'S2A_SPT': 1000, 'S2P_SPT': 0,
    # Servo 3 setpoints: Velocity, Acceleration, Position  
    'S3V_SPT': 1000, 'S3A_SPT': 1000, 'S3P_SPT': 0,
    # Servo 4 setpoints: Velocity, Acceleration, Position
    'S4V_SPT': 1000, 'S4A_SPT': 1000, 'S4P_SPT': 0
}
setpoint_values_2 = {
    # System control parameters
    'Mode': 0,          # Operation mode selector
    'Repeat': 0,        # Repeat motion flag
    'Start': 0,         # Motion start trigger
    
    # Servo 5 setpoints: Velocity, Acceleration, Position (safe defaults)
    'S1V_SPT': 10000, 'S1A_SPT': 10000, 'S1P_SPT': 0,  # Board 2 Servo 1 (Overall Servo 5)
    # Servo 6 setpoints: Velocity, Acceleration, Position
    'S2V_SPT': 10000, 'S2A_SPT': 10000, 'S2P_SPT': 0,  # Board 2 Servo 2 (Overall Servo 6)
    # Servo 7 setpoints: Velocity, Acceleration, Position  
    'S3V_SPT': 10000, 'S3A_SPT': 10000, 'S3P_SPT': 0,  # Board 2 Servo 3 (Overall Servo 7)
    # Servo 8 setpoints: Velocity, Acceleration, Position
    'S4V_SPT': 10000, 'S4A_SPT': 10000, 'S4P_SPT': 0   # Board 2 Servo 4 (Overall Servo 8)
}

# GUI button state tracking for user interface management
# Tracks pressed/released state of all interactive buttons
GUI_button_states_1 = {
    # System control buttons
    'Mode': False,      # Mode selection button
    'Repeat': False,    # Repeat mode toggle
    'Start': False,     # Motion start button
    
    # Servo control buttons (2 buttons per servo for bidirectional control)
    'S1B1': False, 'S1B2': False,      # Servo 1 direction buttons
    'S2B1': False, 'S2B2': False,      # Servo 2 direction buttons  
    'S3B1': False, 'S3B2': False,      # Servo 3 direction buttons
    'S4B1': False, 'S4B2': False       # Servo 4 direction buttons
}
GUI_button_states_2 = {
    # System control buttons
    'Mode': False,      # Mode selection button
    'Repeat': False,    # Repeat mode toggle
    'Start': False,     # Motion start button
    
    # Servo control buttons (2 buttons per servo for bidirectional control)
    'S1B1': False, 'S1B2': False,      # Board 2 Servo 1 (Overall Servo 5) direction buttons
    'S2B1': False, 'S2B2': False,      # Board 2 Servo 2 (Overall Servo 6) direction buttons  
    'S3B1': False, 'S3B2': False,      # Board 2 Servo 3 (Overall Servo 7) direction buttons
    'S4B1': False, 'S4B2': False       # Board 2 Servo 4 (Overall Servo 8) direction buttons
}

# Controller button state tracking (feedback from ClearCore hardware)
# Mirrors GUI states but represents actual hardware button status
CNT_button_states_1 = GUI_button_states_1.copy()      # Hardware state mirror for Board 1
CNT_button_states_2 = GUI_button_states_2.copy()      # Hardware state mirror for Board 2

# ============================================================================
#                         COMMUNICATION STATE TRACKING
# ============================================================================

# Synchronization flags for ClearCore communication
values_received = False                                 # Servo feedback values received
states_received = False                                 # Button states received  
setpoints_received = False                              # Setpoint values received

# ============================================================================
#                         HARDWARE INITIALIZATION FUNCTIONS
# ============================================================================

def initialize_buttons(window, message_queue):
    """
    Initialize button states by requesting current status from ClearCore controller.
    
    This function establishes initial synchronization between the GUI and hardware
    button states. Essential for consistent operation after application startup
    or reconnection events.
    
    Communication Protocol:
    1. Send "CMD:REQUEST_BUTTON_STATES" to controller
    2. Wait for "BUTTON_STATES:" response 
    3. Parse and update local button state dictionaries
    4. Retry up to MAX_RETRIES times if communication fails
    
    Args:
        window: GUI window object for display updates
        message_queue: Thread-safe queue for UDP messages
        
    Returns:
        bool: True if initialization successful, False if all retries failed
    """
    global states_received, CNT_button_states, GUI_button_states
    
    # Retry configuration for robust initialization
    MAX_RETRIES = 5                                     # Maximum initialization attempts
    TIMEOUT = 5                                         # Timeout per attempt (seconds)
    
    for attempt in range(MAX_RETRIES):
        states_received = False                         # Reset flag for this attempt
        request = "CMD:REQUEST_BUTTON_STATES\n"        # Command protocol string
        expected = "BUTTON_STATES:"                     # Expected response prefix
        
        # Brief delay to ensure clean communication
        time.sleep(.5)
        time.sleep(.5)
        
        # Wait for response with timeout protection
        timeout = time.time() + TIMEOUT
        while time.time() < timeout:
            try:
                message = message_queue.get(timeout=0.5)
                if message.startswith(expected):
                    # Process received button states
                    if process_button_states_response(message, window):
                        CNT_button_states = GUI_button_states.copy()
                        return True                     # Successful initialization
            except queue.Empty:
                continue                                # Keep waiting for response
        time.sleep(2)                                   # Delay between retry attempts
    return False                                        # All attempts failed



def initialize_setpoints(window, message_queue):
    """
    Initialize servo setpoint values by requesting current configuration from ClearCore.
    
    Retrieves the current servo motion parameters (velocity, acceleration, position
    setpoints) from the ClearCore controller to synchronize GUI display with
    hardware configuration. Critical for consistent operation after startup.
    
    Communication Protocol:
    1. Send "CMD:REQUEST_SETPOINTS" to controller
    2. Wait for "SETPOINTS:" response containing all servo parameters
    3. Parse and update local setpoint dictionaries
    4. Retry up to MAX_RETRIES times for robustness
    
    Args:
        window: GUI window object for display updates  
        message_queue: Thread-safe queue for UDP messages
        
    Returns:
        bool: True if setpoints successfully retrieved, False if failed
    """
    global setpoints_received, setpoint_values
    
    MAX_RETRIES = 3                                     # Fewer retries than button init
    TIMEOUT = 5                                         # Response timeout (seconds)
    
    for attempt in range(MAX_RETRIES):
        setpoints_received = False                      # Reset flag for this attempt
        request = "CMD:REQUEST_SETPOINTS\n"            # Command protocol string
        expected = "SETPOINTS:"                         # Expected response prefix
        
        time.sleep(0.5)                                # Brief delay for clean communication
        
        # Wait for setpoint response with timeout
        timeout = time.time() + TIMEOUT
        while time.time() < timeout:
            try:
                message = message_queue.get(timeout=0.5)
                if message.startswith(expected):
                    if process_setpoints_response(message, window):
                        # Update setpoint dictionary with retrieved values
                        # This ensures GUI reflects actual hardware configuration
                        setpoint_values.update({
                            # Servo 1 motion parameters
                            'S1V_SPT': setpoint_values['S1V_SPT'], 'S1A_SPT': setpoint_values['S1A_SPT'], 'S1P_SPT': setpoint_values['S1P_SPT'],
                            # Servo 2 motion parameters
                            'S2V_SPT': setpoint_values['S2V_SPT'], 'S2A_SPT': setpoint_values['S2A_SPT'], 'S2P_SPT': setpoint_values['S2P_SPT'],
                            # Servo 3 motion parameters  
                            'S3V_SPT': setpoint_values['S3V_SPT'], 'S3A_SPT': setpoint_values['S3A_SPT'], 'S3P_SPT': setpoint_values['S3P_SPT'],
                            # Servo 4 motion parameters
                            'S4V_SPT': setpoint_values['S4V_SPT'], 'S4A_SPT': setpoint_values['S4A_SPT'], 'S4P_SPT': setpoint_values['S4P_SPT']
                        })
                        return True                     # Successful initialization
            except queue.Empty:
                continue                                # Keep waiting for response
        time.sleep(2)                                   # Delay between retry attempts
    return False                                        # All setpoint initialization attempts failed

# ============================================================================
#                    ADDITIONAL FUNCTIONS CONTINUE BELOW
# ============================================================================
# 
# The remaining functions in this file include:
# - GUI panel builders and layout management
# - Message processing and parsing functions  
# - Event handlers for user interactions
# - Numeric keypad and popup dialogs
# - System shutdown functionality (Raspberry Pi)
# - Main application loop and window management
# - Network error handling with "Continue Anyway" option
# - Loading screen and status popup management
#
# All functions follow the same comprehensive commenting standards as above,
# with detailed docstrings, parameter descriptions, and inline explanations
# for complex logic and cross-platform compatibility considerations.
#
# ============================================================================

def initialize_state_engine(window, message_queue):
    global state_engine_step
    MAX_RETRIES = 3
    TIMEOUT = 5
    for attempt in range(MAX_RETRIES):
        state_engine_step = None
        request = "CMD:REQUEST_STATE_ENGINE\n"
        expected = "STATE_ENGINE:"
        time.sleep(0.5)
        timeout = time.time() + TIMEOUT
        while time.time() < timeout:
            try:
                message = message_queue.get(timeout=0.5)
                if message.startswith(expected):
                    if process_state_engine_response(message, window):
                        return True
            except queue.Empty:
                continue
        time.sleep(2)
    return False

def initialize_from_arduino(window, send_udp_command, message_queue):
    send_udp_command("CMD:REQUEST_BUTTON_STATES\n")
    if not initialize_buttons(window, message_queue):
        return False
    send_udp_command("CMD:REQUEST_SETPOINTS\n")
    if not initialize_setpoints(window, message_queue):
        return False
    send_udp_command("CMD:REQUEST_STATE_ENGINE\n")
    if not initialize_state_engine(window, message_queue):
        return False
    return True

def process_values_response(message, window, arduino_values, prefix):
    # print(f"DEBUG: process_values_response called for {prefix}: {message}")
    parts = message.split(":")[1].split(",")
    if len(parts) >= 12:  # 4 servos × 3 values (V/A/P) = 12 values
        arduino_values['S1V'] = parts[0]
        arduino_values['S1A'] = parts[1]
        arduino_values['S1P'] = parts[2]
        arduino_values['S2V'] = parts[3]
        arduino_values['S2A'] = parts[4]
        arduino_values['S2P'] = parts[5]
        arduino_values['S3V'] = parts[6]
        arduino_values['S3A'] = parts[7]
        arduino_values['S3P'] = parts[8]
        arduino_values['S4V'] = parts[9]
        arduino_values['S4A'] = parts[10]
        arduino_values['S4P'] = parts[11]
        
        # Update Position displays for all 4 servos (position only - velocity and acceleration hidden)
        window[prefix+'S1P_display'].update(arduino_values['S1P'])
        window[prefix+'S2P_display'].update(arduino_values['S2P'])
        window[prefix+'S3P_display'].update(arduino_values['S3P'])
        window[prefix+'S4P_display'].update(arduino_values['S4P'])
        window.refresh()
        return True
    return False

def process_button_states_response(message, window):
    global states_received, GUI_button_states, CNT_button_states
    parts = message.split(":")[1].split(",")
    if len(parts) >= 8:
        GUI_button_states['Mode'] = True if parts[0] == '1' else False
        GUI_button_states['Repeat'] = True if parts[1] == '1' else False
        GUI_button_states['Start'] = True if parts[2] == '1' else False
        GUI_button_states['S1B1'] = True if parts[3] == '1' else False
        GUI_button_states['S1B2'] = True if parts[4] == '1' else False
        GUI_button_states['S2B1'] = True if parts[5] == '1' else False
        GUI_button_states['S2B2'] = True if parts[6] == '1' else False
        GUI_button_states['S3B1'] = True if parts[7] == '1' else False
        GUI_button_states['S3B2'] = True if parts[8] == '1' else False
        GUI_button_states['S4B1'] = True if parts[9] == '1' else False
        GUI_button_states['S4B2'] = True if parts[10] == '1' else False
        CNT_button_states = GUI_button_states.copy()
        states_received = True
        window['Mode'].update(text='Auto' if GUI_button_states['Mode'] else 'Manual', button_color=('white', 'green') if GUI_button_states['Mode'] else ('black', 'yellow'))
        window['Repeat'].update(text='Repeat' if GUI_button_states['Repeat'] else 'Single', button_color=('white', 'green') if GUI_button_states['Repeat'] else ('black', 'yellow'))
        window['Start'].update(text='Started' if GUI_button_states['Start'] else 'Start', button_color=('white', 'green') if GUI_button_states['Start'] else ('black', 'yellow'))
        window['S1B1'].update(text='Enabled' if GUI_button_states['S1B1'] else 'Disabled', button_color=('white', 'green') if GUI_button_states['S1B1'] else ('black', 'yellow'))
        window['S1B2'].update(text='Run' if GUI_button_states['S1B2'] else 'Stop', button_color=('black', 'gray') if GUI_button_states['S1B2'] else ('black', 'gray'))
        window['S2B1'].update(text='Enabled' if GUI_button_states['S2B1'] else 'Disabled', button_color=('white', 'green') if GUI_button_states['S2B1'] else ('black', 'yellow'))
        window['S2B2'].update(text='Run' if GUI_button_states['S2B2'] else 'Stop', button_color=('black', 'gray') if GUI_button_states['S2B2'] else ('black', 'gray'))
        window['S3B1'].update(text='Enabled' if GUI_button_states['S3B1'] else 'Disabled', button_color=('white', 'green') if GUI_button_states['S3B1'] else ('black', 'yellow'))
        window['S3B2'].update(text='Run' if GUI_button_states['S3B2'] else 'Stop', button_color=('black', 'gray') if GUI_button_states['S3B2'] else ('black', 'gray'))
        window['S4B1'].update(text='Enabled' if GUI_button_states['S4B1'] else 'Disabled', button_color=('white', 'green') if GUI_button_states['S4B1'] else ('black', 'yellow'))
        window['S4B2'].update(text='Run' if GUI_button_states['S4B2'] else 'Stop', button_color=('black', 'gray') if GUI_button_states['S4B2'] else ('black', 'gray'))
        window.refresh()
        return True
    return False

def process_setpoints_response(message, window):
    global setpoints_received, setpoint_values
    parts = message.split(":")[1].split(",")
    if len(parts) >= 12:
        try:
            S1V_SPT, S1A_SPT, S1P_SPT = map(int, parts[0:3])
            S2V_SPT, S2A_SPT, S2P_SPT = map(int, parts[3:6])
            S3V_SPT, S3A_SPT, S3P_SPT = map(int, parts[6:9])
            S4V_SPT, S4A_SPT, S4P_SPT = map(int, parts[9:12])
            setpoints_received = True
            setpoint_values['S1V_SPT'] = S1V_SPT
            setpoint_values['S1A_SPT'] = S1A_SPT
            setpoint_values['S1P_SPT'] = S1P_SPT
            setpoint_values['S2V_SPT'] = S2V_SPT
            setpoint_values['S2A_SPT'] = S2A_SPT
            setpoint_values['S2P_SPT'] = S2P_SPT
            setpoint_values['S3V_SPT'] = S3V_SPT
            setpoint_values['S3A_SPT'] = S3A_SPT
            setpoint_values['S3P_SPT'] = S3P_SPT
            setpoint_values['S4V_SPT'] = S4V_SPT
            setpoint_values['S4A_SPT'] = S4A_SPT
            setpoint_values['S4P_SPT'] = S4P_SPT
            window.refresh()
            return True
        except ValueError:
            print("Error processing setpoints response")
    return False

def process_state_engine_response(message, window):
    global state_engine_step
    parts = message.split(":")[1].split(",")
    if len(parts) >= 1:
        state_engine_step = int(parts[0])
        window['state_engine_step'].update(state_engine_step)
        window.refresh()
        return True
    return False

def process_response(message, expected, window):
    if expected == "BUTTON_STATES:":
        return process_button_states_response(message, window)
    elif expected == "SETPOINTS:":
        return process_setpoints_response(message, window)
    elif expected == "STATE_ENGINE:":
        return process_state_engine_response(message, window)
    return False

def handle_servo_buttons(event, enable_command, disable_command, enabled, window):
    """Handle servo button events and state changes."""
    # print(f"Debug 25 - Handling event: {event}, enabled: {enabled}")   
    
    if event == 'Mode':  # Mode is either Manual or Auto
        if enabled:
            # print(f"Debugs 26 - Sending disable command for Mode: MANUAL")   
            send_udp_command("CMD:Mode MANUAL\n")
            window[event].update(text='Auto', button_color=('white', 'green'))
            GUI_button_states[event] = False
        else:
            # print(f"Debugs 27 - Sending enable command for Mode: AUTO")   
            send_udp_command("CMD:Mode AUTO\n")
            window[event].update(text='Manual', button_color=('black', 'yellow'))
            GUI_button_states[event] = True

    elif event == 'Repeat':  # Repeat is either enabled or disabled
        if enabled:
            # print(f"Debugs 28 - Sending disable command for Repeat: DISABLE")   
            send_udp_command("CMD:Repeat DISABLE\n")
            window[event].update(text='Repeat', button_color=('white', 'green'))
            GUI_button_states[event] = False
        else:
            # print(f"Debugs 29 - Sending enable command for Repeat: ENABLE")   
            send_udp_command("CMD:Repeat ENABLE\n")
            window[event].update(text='Single', button_color=('black', 'yellow'))
            GUI_button_states[event] = True

    elif event == 'Start':  # Start is either enabled or disabled
        if enabled:
            # print(f"Debugs 30 - Sending disable command for Start: DISABLE")   
            send_udp_command("CMD:Start DISABLE\n")
            window[event].update(text='Disable Start', button_color=('white', 'green'))
            GUI_button_states[event] = False
        else:
            # print(f"Debugs 31 - Sending enable command for Start: ENABLE")   
            send_udp_command("CMD:Start ENABLE\n")
            window[event].update(text='Enable Start', button_color=('black', 'yellow'))
            GUI_button_states[event] = True
    
    elif event.endswith('B1'):  # B1 is either ENABLE or DISABLE
        if enabled:
            # print(f"Debugs 32 - Sending disable command for {event}: DISABLE")   
            send_udp_command(f"CMD:{event} DISABLE\n")
            window[event].update(text='ENabled', button_color=('white', 'green'))
            GUI_button_states[event] = False
        else:
            # print(f"Debugs 33 - Sending enable command for {event}: ENABLE")   
            send_udp_command(f"CMD:{event} ENABLE\n")
            window[event].update(text='DISabled', button_color=('black', 'yellow'))
            GUI_button_states[event] = True
    
    elif event.endswith('B2'):  # B2 is either Run or Stop
        if enabled:
            # print(f"Debugs 34 - Sending disable command for {event}: STOP")   
            send_udp_command(f"CMD:{event} STOP\n")
            window[event].update(text='Spare', button_color=('black', 'gray'))
            GUI_button_states[event] = False
        else:
            # print(f"Debugs 35 - Sending enable command for {event}: Start")   
            send_udp_command(f"CMD:{event} Start\n")
            window[event].update(text='Spare', button_color=('white', 'gray'))
            GUI_button_states[event] = True
    
    elif event.endswith('B3'):
        servo = int(event[1])
        V_data = validate_input(f'S{servo}V_SPT', values, 0, 1000)
        A_data = validate_input(f'S{servo}A_SPT', values, 0, 1000)
        pos_min, pos_max = POSITION_LIMITS.get(servo, (0, 1000))
        P_data = validate_input(f'S{servo}P_SPT', values, pos_min, pos_max)
        if all(x is not None for x in (V_data, A_data, P_data)):
            cmd = f"CMD:S{servo}_Parameters:{V_data},{A_data},{P_data}\n"
            # print(f"Debugs 36 - Sending command: {cmd.strip()}")   
            send_udp_command(cmd)
            # (UDP does not need flush)
            # Update setpoint_values and corresponding sg.Text elements
            setpoint_values[f'S{servo}V_SPT'] = V_data
            setpoint_values[f'S{servo}A_SPT'] = A_data
            setpoint_values[f'S{servo}P_SPT'] = P_data
            window.refresh()
            # print(f"Debugs 37 - Updated setpoints for S{servo}: V_SPT={V_data}, A_SPT={A_data}, P_SPT={P_data}")   
    
    # (UDP does not need flush)
    return not enabled

def validate_input(key, values, min_val, max_val):
    try:
        value = int(values[key])
        if min_val <= value <= max_val:
            return value
    except ValueError:
        print(f"Invalid value for {key}")
    return None

def show_numeric_keypad(title, current_value, min_val=0, max_val=54000):
    """Custom numeric keypad popup for touchscreen input"""
    layout = [
        [sg.Text(title, font=GLOBAL_FONT)],
        [sg.Text('Current Value:', font=GLOBAL_FONT), 
         sg.InputText(str(current_value), key='display', size=(15, 1), font=GLOBAL_FONT, justification='center', readonly=False)],
        [sg.Button('7', size=(6, 2), font=GLOBAL_FONT), 
         sg.Button('8', size=(6, 2), font=GLOBAL_FONT), 
         sg.Button('9', size=(6, 2), font=GLOBAL_FONT)],
        [sg.Button('4', size=(6, 2), font=GLOBAL_FONT), 
         sg.Button('5', size=(6, 2), font=GLOBAL_FONT), 
         sg.Button('6', size=(6, 2), font=GLOBAL_FONT)],
        [sg.Button('1', size=(6, 2), font=GLOBAL_FONT), 
         sg.Button('2', size=(6, 2), font=GLOBAL_FONT), 
         sg.Button('3', size=(6, 2), font=GLOBAL_FONT)],
        [sg.Button('Clear', size=(6, 2), font=GLOBAL_FONT), 
         sg.Button('0', size=(6, 2), font=GLOBAL_FONT), 
         sg.Button('⌫', size=(6, 2), font=GLOBAL_FONT)],
        [sg.Button('Cancel', size=(8, 2), font=GLOBAL_FONT), 
         sg.Button('OK', size=(8, 2), font=GLOBAL_FONT)]
    ]
    
    # Upper right corner positioning for all platforms
    location = (50, 50)  # Upper left corner for all platforms
    
    popup_window = sg.Window(title, layout, modal=True, finalize=True, location=location, keep_on_top=True)
    
    while True:
        event, values = popup_window.read()
        
        if event in (sg.WIN_CLOSED, 'Cancel'):
            popup_window.close()
            return None
            
        elif event == 'OK':
            try:
                result = int(values['display'])
                if min_val <= result <= max_val:
                    popup_window.close()
                    return result
                else:
                    sg.popup_error(f'Value must be between {min_val} and {max_val}', keep_on_top=True, location=(50, 50), font=GLOBAL_FONT)
            except ValueError:
                sg.popup_error('Please enter a valid number', keep_on_top=True, location=(50, 50), font=GLOBAL_FONT)
                
        elif event == 'Clear':
            popup_window['display'].update('0')
            
        elif event == '⌫':  # Backspace
            current = values['display']
            popup_window['display'].update(current[:-1])
            
        elif event in '0123456789':
            current = values['display']
            popup_window['display'].update(current + event)

def shutdown_system():
    """Shutdown the Raspberry Pi system after confirmation"""
    if not IS_RASPBERRY_PI:
        sg.popup_error("Shutdown function is only available on Raspberry Pi", location=(50, 50), font=GLOBAL_FONT)
        return False
    
    # Confirmation dialog
    layout = [
        [sg.Text('System Shutdown', font=GLOBAL_FONT, text_color='red')],
        [sg.Text('', font=GLOBAL_FONT)],
        [sg.Text('Are you sure you want to shutdown the Raspberry Pi?', font=GLOBAL_FONT)],
        [sg.Text('This will close the application and power off the system.', font=GLOBAL_FONT)],
        [sg.Text('', font=GLOBAL_FONT)],
        [sg.Button('Cancel', size=(10, 1), button_color=('black', 'lightgray'), font=GLOBAL_FONT), 
         sg.Button('Shutdown Now', size=(12, 1), button_color=('white', 'red'), font=GLOBAL_FONT)]
    ]
    
    confirm_window = sg.Window('Confirm Shutdown', layout, 
                              keep_on_top=True, modal=True, finalize=True,
                              location=(50, 50))
    
    while True:
        event, values = confirm_window.read()
        if event in (sg.WIN_CLOSED, 'Cancel'):
            confirm_window.close()
            return False
        elif event == 'Shutdown Now':
            confirm_window.close()
            
            # Show shutdown progress
            progress_layout = [
                [sg.Text('Shutting down system...', font=GLOBAL_FONT)],
                [sg.Text('Please wait, system will power off shortly.', font=GLOBAL_FONT)],
                [sg.ProgressBar(100, orientation='h', size=(40, 20), key='PROGRESS')]
            ]
            
            progress_window = sg.Window('System Shutdown', progress_layout, 
                                       no_titlebar=True, keep_on_top=True, 
                                       location=(50, 50), finalize=True)
            
            # Animate progress bar briefly
            for i in range(101):
                progress_window['PROGRESS'].update(i)
                progress_window.refresh()
                time.sleep(0.01)
            
            progress_window.close()
            return True

def build_board_panel(board_num, arduino_values, setpoint_values, GUI_button_states):
    """
    Build servo control panel with simplified interface for Servos 2-4.
    
    Interface Layout:
    - Tab 1 (Board 1): Servos 1-4 with full controls (Velocity, Acceleration, Position)
    - Tab 2 (Board 2): Servos 5-8 with full controls (Velocity, Acceleration, Position)
    
    This provides complete 8-axis control capability with clean organization across two tabs.
    Each servo has independent Velocity, Acceleration, and Position controls.
    """

    prefix = f'B{board_num}_'
    panel = [
        [sg.Button('Clear All Faults', key=prefix+'CLEAR_ALL_FAULTS', font=GLOBAL_FONT, size=(18,2), pad=((0, 0), (0, 0)))]
    ]

    for i in range(1, 5):
        # All Servos 1-4: Show all controls (Velocity, Acceleration, Position) - Hide Enable/Start buttons
        # On the second row (i==2), add the Clear All Faults button at the end
        if i == 2:
            panel += [
                [sg.Text(f'Position {i}', size=(11, 1), justification='left', font=POSITION_LABEL_FONT),
                 sg.Text('', size=(22, 1), font=GLOBAL_FONT),  # Hidden Enable/Disable button
                 sg.Text('', size=(8, 1), font=GLOBAL_FONT),   # Hidden Start/Stop button
                 sg.Button(f'{setpoint_values[f"S{i}V_SPT"]}', key=prefix+f'S{i}V_SPT_btn', size=(8, 1), button_color=('black', 'lightblue'), font=GLOBAL_FONT),
                 sg.Button(f'{setpoint_values[f"S{i}A_SPT"]}', key=prefix+f'S{i}A_SPT_btn', size=(8, 1), button_color=('black', 'lightblue'), font=GLOBAL_FONT),
                 sg.Button(f'{setpoint_values[f"S{i}P_SPT"]}', key=prefix+f'S{i}P_SPT_btn', size=(8, 1), button_color=('black', 'lightblue'), font=GLOBAL_FONT),
                 sg.Button('OK', key=prefix+f'S{i}B3', size=(8, 2), font=GLOBAL_FONT)]
            ]
            panel += [
                [sg.Button('Clear Value', key=prefix+f'S{i}B4', size=(16, 1), button_color=('black', 'orange'), font=CLEAR_BUTTON_FONT),
                 sg.Text('', size=(5, 1), font=GLOBAL_FONT),  # 5-space spacing after Clear Value button
                 sg.Text('Current Position', size=(16, 1), justification='left', font=GLOBAL_FONT),
                 sg.Text('..............................', size=(31, 1), font=GLOBAL_FONT),  # Adjusted spacing
                 sg.Text(arduino_values[f'S{i}P'], size=(6, 1), key=prefix+f'S{i}P_display', justification='center', font=GLOBAL_FONT),
                 sg.Text('', size=(1, 1))]  # Spacer to align with above
            ]
        else:
            panel += [
                [sg.Text(f'Position {i}', size=(11, 1), justification='left', font=POSITION_LABEL_FONT),
                 sg.Text('', size=(22, 1), font=GLOBAL_FONT),  # Hidden Enable/Disable button
                 sg.Text('', size=(8, 1), font=GLOBAL_FONT),   # Hidden Start/Stop button
                 sg.Button(f'{setpoint_values[f"S{i}V_SPT"]}', key=prefix+f'S{i}V_SPT_btn', size=(8, 1), button_color=('black', 'lightblue'), font=GLOBAL_FONT),
                 sg.Button(f'{setpoint_values[f"S{i}A_SPT"]}', key=prefix+f'S{i}A_SPT_btn', size=(8, 1), button_color=('black', 'lightblue'), font=GLOBAL_FONT),
                 sg.Button(f'{setpoint_values[f"S{i}P_SPT"]}', key=prefix+f'S{i}P_SPT_btn', size=(8, 1), button_color=('black', 'lightblue'), font=GLOBAL_FONT),
                 sg.Button('OK', key=prefix+f'S{i}B3', size=(8, 2), font=GLOBAL_FONT)],
                [sg.Button('Clear Value', key=prefix+f'S{i}B4', size=(16, 1), button_color=('black', 'orange'), font=CLEAR_BUTTON_FONT),
                 sg.Text('', size=(5, 1), font=GLOBAL_FONT),  # 5-space spacing after Clear Value button
                 sg.Text('Current Position', size=(16, 1), justification='left', font=GLOBAL_FONT),
                 sg.Text('..............................', size=(31, 1), font=GLOBAL_FONT),  # Adjusted spacing
                 sg.Text(arduino_values[f'S{i}P'], size=(6, 1), key=prefix+f'S{i}P_display', justification='center', font=GLOBAL_FONT)]
            ]
    return panel

# Build the main layout with both tabs enabled for 8-axis control
main_layout = [
    [sg.TabGroup(
        [[
            sg.Tab('Servos 1-4', build_board_panel(1, arduino_values_1, setpoint_values_1, GUI_button_states_1), key='TAB1'),
            sg.Tab('Servos 5-8', build_board_panel(2, arduino_values_2, setpoint_values_2, GUI_button_states_2), key='TAB2')
        ]],
        key='TABGROUP',
        tab_background_color='darkgray',           # color of all tabs
        selected_title_color='darkblue',               # text color of selected tab
        selected_background_color='white'        # background color of selected tab
    )]
]

# Add shutdown button row for GUI testing on all platforms (only functional on Raspberry Pi)
shutdown_row = [
    sg.Text(' ', size=(81, 1), font=GLOBAL_FONT),  # Spacer to push button right
    sg.Button('Shutdown', key='SHUTDOWN', size=(10, 1), 
              button_color=('white', 'red'), font=GLOBAL_FONT)
]
main_layout.append(shutdown_row)

# NEW: Dynamic layout creation based on network status
# If user chose "Continue Anyway", add persistent error warning at top of GUI
# This provides constant visual feedback that the system is running in debug mode
if network_error_message:
    # Create prominent warning bar with high-visibility colors (red text on yellow)
    error_bar = [
        [sg.Text('⚠ NETWORK ERROR - RUNNING IN DEBUG MODE ⚠', 
                 font=('Helvetica', 12, 'bold'), 
                 text_color='red', 
                 background_color='yellow',
                 justification='center',
                 size=(80, 1))],
        [sg.Text(f'Error: {network_error_message}', 
                 font=('Helvetica', 9), 
                 text_color='darkred',
                 justification='center')],
        [sg.Text(' ')]  # Visual spacing between warning and main interface
    ]
    # Prepend error bar to main layout - warning appears at top of window
    layout = error_bar + main_layout
else:
    # Normal operation - no network issues detected
    layout = main_layout

def create_loading_window():
    """
    Create a fresh loading window with new elements each time.
    
    BUGFIX: This prevents the GUI element reuse error that occurs when
    the user clicks 'Retry' on the network error dialog. FreeSimpleGUI
    elements can only be used once, so we must create new elements
    for each loading window instance.
    
    Returns:
        sg.Window: A new loading window with fresh GUI elements
    """
    loading_layout = [
        [sg.Text('Servo Control System', font=GLOBAL_FONT, justification='center')],
        [sg.Text(' ', size=(20, 1), font=GLOBAL_FONT)],
        [sg.Text('Checking network connectivity...', font=GLOBAL_FONT, justification='center')],
        [sg.Text('Please wait while connecting to controllers', font=GLOBAL_FONT, justification='center')],
        [sg.Text(' ', size=(20, 1), font=GLOBAL_FONT)]
    ]
    window = sg.Window('Loading', loading_layout, no_titlebar=True, 
                      keep_on_top=True, location=(50, 50), 
                      alpha_channel=0.9, font=GLOBAL_FONT, finalize=True)
    window.refresh()
    return window

# Show initial loading screen
loading_window = create_loading_window()

# ENHANCED: Network connectivity check with "Continue Anyway" option
# This replaces the old binary retry/exit loop with three-way handling:
# 1. Success -> start normally
# 2. Retry -> try again  
# 3. Continue -> start in debug mode with persistent error display
network_error_message = None  # Store error for later display in GUI
while True:
    network_ok, message = check_network_connectivity()
    loading_window.close()
    
    if network_ok:
        break
    else:
        # NEW: Show enhanced error dialog with three options
        user_choice = show_network_error_dialog(message)
        
        if user_choice == 'exit':
            # User chose to exit - clean shutdown
            udp_thread.stop()
            udp_thread.join()
            udp_sock.close()
            sys.exit(1)
        elif user_choice == 'continue':
            # NEW: User chose to continue anyway - enable debug mode
            # Save error message to display persistent warning in main GUI
            network_error_message = message
            print(f"Debug: Continuing with network error: {message}")
            break  # Exit loop and start GUI with error display
        elif user_choice == 'retry':
            # User chose retry - create fresh loading screen to avoid element reuse error
            loading_window = create_loading_window()
            time.sleep(2)  # Wait before retry

window = sg.Window("Servo Control",
            layout, default_element_size=(8, 5),
            size=(800, 450) if IS_RASPBERRY_PI else (800, 400),
            location=(0, 0) if IS_RASPBERRY_PI else (None, None),
            auto_size_text=False,
            auto_size_buttons=False,
            font=GLOBAL_FONT,
            finalize=True)

# NEW: Show communication status popup if running in debug mode
# This provides clear feedback after GUI loads about system status
if network_error_message:
    # Brief delay to ensure main window is fully displayed
    window.refresh()
    time.sleep(0.5)
    show_communication_status_popup(network_error_message)

# Network connectivity confirmed - loading screen already closed above

init_error_queue = queue.Queue()

last_request_time = time.time()
last_gui_update = time.time()
last_event_time = {}

while True:
    event, values = window.read(timeout=WINDOW_READ_TIMEOUT)
    try:
        error_msg = init_error_queue.get_nowait()
        sg.popup_error(error_msg, location=(50, 50), font=GLOBAL_FONT)
    except queue.Empty:
        pass

    if event == sg.WIN_CLOSED or event == "Exit":
        print("Debug 40 - Window closed or Exit event triggered")
        break

    # [CHANGE 2025-11-23] Handle Clear All Faults button for each board
    if event == 'B1_CLEAR_ALL_FAULTS':
        send_udp_command1("BOARD:1;CMD:CLEAR_ALL_FAULTS\n")
    if event == 'B2_CLEAR_ALL_FAULTS':
        send_udp_command2("BOARD:2;CMD:CLEAR_ALL_FAULTS\n")
    
    # Handle shutdown button (Raspberry Pi only)
    if event == 'SHUTDOWN':
        print("Debug: Shutdown button pressed")
        if shutdown_system():
            print("Debug: Shutdown confirmed, closing application and powering off")
            # Clean shutdown sequence
            udp_thread.stop()
            udp_thread.join()
            udp_sock.close()
            window.close()
            
            # Execute system shutdown
            try:
                subprocess.run(['sudo', 'shutdown', 'now'], check=False)
            except Exception as e:
                print(f"Shutdown command failed: {e}")
            
            sys.exit(0)
        else:
            print("Debug: Shutdown cancelled")

    board_num = None
    event_key = event
    if isinstance(event, str) and event.startswith("B1_"):
        board_num = 1
        event_key = event[3:]
    elif isinstance(event, str) and event.startswith("B2_"):
        board_num = 2
        event_key = event[3:]

    if board_num == 1:
        GUI_button_states = GUI_button_states_1
        CNT_button_states = CNT_button_states_1
        setpoint_values = setpoint_values_1
        send_udp_command = send_udp_command1
        message_queue = message_queue
    elif board_num == 2:
        GUI_button_states = GUI_button_states_2
        CNT_button_states = CNT_button_states_2
        setpoint_values = setpoint_values_2
        send_udp_command = send_udp_command2
        message_queue = message_queue

    # --- Button Events with BOARD prefix for all commands ---
    if event and isinstance(event, str) and board_num:
        current_time = time.time()
        if event != '__TIMEOUT__':
            print(f"Debug 41 - Event: {event}")

        if event not in last_event_time or (current_time - last_event_time[event] > DEBOUNCE_INTERVAL):
            last_event_time[event] = current_time
            match event_key:
                case 'Mode':
                    GUI_button_states[event_key] = not GUI_button_states[event_key]
                    CNT_button_states[event_key] = handle_servo_buttons(event, "Mode AUTO", "Mode MANUAL", CNT_button_states[event_key], window)
                    window[event].update(
                        text='Auto' if GUI_button_states[event_key] else 'Manual',
                        button_color=('white', 'green') if GUI_button_states[event_key] else ('black', 'yellow')
                    )
                    window.refresh()
                    mode_cmd = "Mode AUTO" if GUI_button_states[event_key] else "Mode MANUAL"
                    cmd = f"BOARD:{board_num};CMD:{mode_cmd}\n"
                    print(f"Debug 42 - Sending command: {cmd.strip()}")
                    send_udp_command(cmd)
                case 'Repeat':
                    GUI_button_states[event_key] = not GUI_button_states[event_key]
                    CNT_button_states[event_key] = handle_servo_buttons(event, "Repeat", "Single", CNT_button_states[event_key], window)
                    window[event].update(
                        text='Repeat' if GUI_button_states[event_key] else 'Single',
                        button_color=('white', 'green') if GUI_button_states[event_key] else ('black', 'yellow')
                    )
                    window.refresh()
                    repeat_cmd = "Repeat ENABLE" if GUI_button_states[event_key] else "Repeat DISABLE"
                    cmd = f"BOARD:{board_num};CMD:{repeat_cmd}\n"
                    print(f"Debug 43 - Sending command: {cmd.strip()}")
                    send_udp_command(cmd)
                case 'Start':
                    GUI_button_states[event_key] = not GUI_button_states[event_key]
                    CNT_button_states[event_key] = handle_servo_buttons(event, "Start ENABLED", "Start DISABLED", CNT_button_states[event_key], window)
                    window[event].update(
                        text='Step Enabled' if GUI_button_states[event_key] else 'Step Disabled',
                        button_color=('white', 'green') if GUI_button_states[event_key] else ('black', 'yellow')
                    )
                    window.refresh()
                    start_cmd = "Start ENABLE" if GUI_button_states[event_key] else "Start DISABLE"
                    cmd = f"BOARD:{board_num};CMD:{start_cmd}\n"
                    print(f"Debug 44 - Sending command: {cmd.strip()}")
                    send_udp_command(cmd)
                case 'S1B1' | 'S2B1' | 'S3B1' | 'S4B1':
                    servo = int(event_key[1])
                    GUI_button_states[event_key] = not GUI_button_states[event_key]
                    CNT_button_states[event_key] = handle_servo_buttons(event, "ENABLE", "DISABLE", CNT_button_states[event_key], window)
                    window[event].update(
                        text='Enabled' if GUI_button_states[event_key] else 'Disabled',
                        button_color=('white', 'green') if GUI_button_states[event_key] else ('black', 'yellow')
                    )
                    window.refresh()
                    b1_cmd = f"S{servo}B1 ENABLE" if GUI_button_states[event_key] else f"S{servo}B1 DISABLE"
                    cmd = f"BOARD:{board_num};CMD:{b1_cmd}\n"
                    print(f"Debug 45 - Sending command: {cmd.strip()}")
                    send_udp_command(cmd)
                case 'S1B2' | 'S2B2' | 'S3B2' | 'S4B2':
                    servo = int(event_key[1])
                    GUI_button_states[event_key] = not GUI_button_states[event_key]
                    CNT_button_states[event_key] = handle_servo_buttons(event, "RUN", "STOP", CNT_button_states[event_key], window)
                    window[event].update(
                        text='STOP' if GUI_button_states[event_key] else 'RUN',
                        button_color=('black', 'gray') if GUI_button_states[event_key] else ('white', 'gray')
                    )
                    window.refresh()
                    b2_cmd = f"S{servo}B2 Start" if GUI_button_states[event_key] else f"S{servo}B2 STOP"
                    cmd = f"BOARD:{board_num};CMD:{b2_cmd}\n"
                    print(f"Debug 46 - Sending command: {cmd.strip()}")
                    send_udp_command(cmd)
                case _ if event_key.endswith('V_SPT_btn'):
                    servo = int(event_key[1])
                    current_value = setpoint_values[f'S{servo}V_SPT']
                    new_value = show_numeric_keypad(
                        f'Velocity Setpoint for Servo {servo}',
                        current_value,
                        0, 200000
                    )
                    if new_value is not None:
                        setpoint_values[f'S{servo}V_SPT'] = new_value
                        window[event].update(str(new_value))
                case _ if event_key.endswith('A_SPT_btn'):
                    servo = int(event_key[1])
                    current_value = setpoint_values[f'S{servo}A_SPT']
                    new_value = show_numeric_keypad(
                        f'Acceleration Setpoint for Servo {servo}',
                        current_value,
                        0, 200000
                    )
                    if new_value is not None:
                        setpoint_values[f'S{servo}A_SPT'] = new_value
                        window[event].update(str(new_value))
                case _ if event_key.endswith('P_SPT_btn'):
                    servo = int(event_key[1])
                    current_value = setpoint_values[f'S{servo}P_SPT']
                    pos_min, pos_max = POSITION_LIMITS.get(servo, (0, 54000))
                    new_value = show_numeric_keypad(
                        f'Position Setpoint for Servo {servo}',
                        current_value,
                        pos_min, pos_max
                    )
                    if new_value is not None:
                        setpoint_values[f'S{servo}P_SPT'] = new_value
                        window[event].update(str(new_value))
                case _ if event_key.endswith('B3'):
                    servo = int(event_key[1])
                    V_data = setpoint_values[f'S{servo}V_SPT']
                    A_data = setpoint_values[f'S{servo}A_SPT']
                    P_data = setpoint_values[f'S{servo}P_SPT']
                    cmd = f"BOARD:{board_num};CMD:S{servo}_Parameters:{V_data},{A_data},{P_data}\n"
                    print(f"Debug 47 - Sending command: {cmd.strip()}")
                    send_udp_command(cmd)
                    print(f"Debug 48 - Updated setpoints for S{servo}: V_SPT={V_data}, A_SPT={A_data}, P_SPT={P_data}")
                case _ if event_key.endswith('B4'):
                    servo = int(event_key[1])
                    cmd = f"BOARD:{board_num};CMD:S{servo}_ClearPosition\n"
                    print(f"Debug 49 - Sending clear position command: {cmd.strip()}")
                    send_udp_command(cmd)

    current_time = time.time()
    if current_time - last_request_time > MEDIUM_PRIORITY_UPDATE_INTERVAL:
        send_udp_command1("BOARD:1;CMD:REQUEST_VALUES\n")
        send_udp_command2("BOARD:2;CMD:REQUEST_VALUES\n")
        last_request_time = current_time

    gui_update_time = time.time()
    if gui_update_time - last_gui_update > LOW_PRIORITY_UPDATE_INTERVAL:
        try:
            for _ in range(BATCH_SIZE):
                message = message_queue.get_nowait()
                if DEBUG_LOW_PRIORITY:
                   print(f"Debug 51 - Processing message: {message}")
                if message.startswith("STATE_ENGINE:"):
                    process_response(message, "STATE_ENGINE:", window)
                elif message.startswith("BOARD:1;VALUES:"):
                    process_values_response(message[len("BOARD:1;"):], window, arduino_values_1, 'B1_')
                elif message.startswith("BOARD:2;VALUES:"):
                    process_values_response(message[len("BOARD:2;"):], window, arduino_values_2, 'B2_')
                elif message.startswith("SETPOINTS:"):
                    process_response(message, "SETPOINTS:", window)
                elif message.startswith("BUTTON_STATES:"):
                    process_response(message, "BUTTON_STATES:", window)
        except queue.Empty:
            pass

        last_gui_update = current_time

udp_thread.stop()
udp_thread.join()
udp_sock.close()
window.close()