import PySimpleGUI as sg
import serial
import threading
import queue
import time
import sys  # Add sys import

# Global state
state_engine_step = 0
arduino_values = {f'S{i}{p}': '0' for i in range(1, 5) for p in ['V', 'A', 'P']}
button_states = {f'S{i}B{j}': False for i in range(1, 5) for j in range(1, 3)}
servo_states = button_states.copy()
 
# Button States
S1B1 = False  # Servo1 Button 1
S1B2 = False  # Servo1 Button 2
S2B1 = False  # Servo2 Button 1 
S2B2 = False  # Servo2 Button 2
S3B1 = False  # Servo3 Button 1
S3B2 = False  # Servo3 Button 2
S4B1 = False  # Servo4 Button 1
S4B2 = False  # Servo4 Button 2

# Current Values
S1V = 0  # Servo1 Velocity
S1A = 0  # Servo1 Actual
S1P = 0  # Servo1 Position
S2V = 0  # Servo2 Velocity
S2A = 0  # Servo2 Actual
S2P = 0  # Servo2 Position
S3V = 0  # Servo3 Velocity
S3A = 0  # Servo3 Actual
S3P = 0  # Servo3 Position
S4V = 0  # Servo4 Velocity
S4A = 0  # Servo4 Actual
S4P = 0  # Servo4 Position

# Setpoints
S1V_SPT = 1000  # Servo1 Velocity Setpoint
S1A_SPT = 2000  # Servo1 Actual Setpoint
S1P_SPT = 0  # Servo1 Position Setpoint
S2V_SPT = 1000  # Servo2 Velocity Setpoint
S2A_SPT = 2000  # Servo2 Actual Setpoint
S2P_SPT = 0  # Servo2 Position Setpoint
S3V_SPT = 1000  # Servo3 Velocity Setpoint
S3A_SPT = 2000  # Servo3 Actual Setpoint
S3P_SPT = 0  # Servo3 Position Setpoint
S4V_SPT = 1000  # Servo4 Velocity Setpoint
S4A_SPT = 2000  # Servo4 Actual Setpoint
S4P_SPT = 0  # Servo4 Position Setpoint

arduino_values = {f'S{i}{p}': '0' for i in range(1, 5) for p in ['V', 'A', 'P']}
last_request_time = 0
REQUEST_INTERVAL = 2.0  # seconds between Arduino updates
BATCH_SIZE = 5  # messages to process per cycle
last_request_time = 0

# Add performance optimization constants
WINDOW_READ_TIMEOUT = 10     # Faster window response (ms)
REQUEST_INTERVAL = 0.5      # More frequent Arduino updates (sec)
GUI_UPDATE_INTERVAL = 0.1    # Faster display updates (sec)
BATCH_SIZE = 5 

class SerialThread(threading.Thread):
    """Async serial port monitoring thread."""
    def __init__(self, serial_port, message_queue):
        """
        Args:
            serial_port: Serial connection instance
            message_queue: Queue for received messages
        """
        threading.Thread.__init__(self)
        self.serial_port = serial_port
        self.message_queue = message_queue
        self.running = True

    def run(self):
        """Monitor serial port and queue messages."""
        while self.running:
            if self.serial_port.in_waiting > 0:
                try:
                    line = self.serial_port.readline().decode('utf-8').rstrip()
                    print(f"Debug - Serial received: {line}")
                    self.message_queue.put(line)
                except Exception as e:
                    print(f"Debug - Serial error: {e}")
            time.sleep(0.1)

    def stop(self):
        """Stop thread execution."""
        self.running = False

def initialize_serial_connection(port, baudrate=9600, timeout=1):
    """Initialize serial connection with error handling.
    
    Args:
        port (str): COM port name
        baudrate (int): Communication speed
        timeout (int): Read timeout in seconds
        
    Returns:
        serial.Serial: Configured serial port instance
    """
    try:
        print(f"Debug - Opening {port}")
        serial_inst = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
        serial_inst.reset_input_buffer()
        print("Debug - Serial port opened")
        return serial_inst
    except Exception as e:
        print(f"Debug - Serial port error: {e}")
        raise

# Initialize components
serialInst = initialize_serial_connection('COM10')
message_queue = queue.Queue()
serial_thread = SerialThread(serialInst, message_queue)
serial_thread.start()

def handle_servo_buttons(event, button_id, enable_command, disable_command, enabled):
    """Handle servo button events and state changes.
    
    Args:
        event (str): Event identifier
        button_id (str): Button identifier
        enable_command (str): Command to enable
        disable_command (str): Command to disable
        enabled (bool): Current button state
        
    Returns:
        bool: New button state
    """
    if event == button_id:
        if enabled:
            serialInst.write(f"CMD:{disable_command}\n".encode('utf-8'))
            window[button_id].update(
                text='ENABLE' if 'ENABLE' in enable_command else 'RUN',
                button_color=('white', 'green'))
        else:
            serialInst.write(f"CMD:{enable_command}\n".encode('utf-8'))
            window[button_id].update(
                text='DISABLE' if 'ENABLE' in enable_command else 'STOP',
                button_color=('white', 'red'))
        serialInst.flush()
        return not enabled
    return enabled

def initialize_states():
    """Initialize servo states from Arduino."""
    timeout = time.time() + 5
    values_received = False
    states_received = False
    setpoints_received = False
    
    print("Debug - Starting initialization...")
    while not message_queue.empty():
        message_queue.get()
        
    serialInst.write("CMD:REQUEST_VALUES\n".encode('utf-8'))
    serialInst.flush()
    print("Debug - Requested VALUES")
    time.sleep(0.1)
    
    serialInst.write("CMD:REQUEST_BUTTON_STATES\n".encode('utf-8'))
    serialInst.flush()
    print("Debug - Requested BUTTON_STATES")
    
    serialInst.write("CMD:REQUEST_SETPOINTS\n".encode('utf-8'))
    serialInst.flush()
    print("Debug - Requested SETPOINTS")
    
    while time.time() < timeout:
        try:
            message = message_queue.get_nowait()
            print(f"Debug - Init received: {message}")
            
            if message.startswith("VALUES:"):
                parts = message.split(":")[1].split(",")
                if len(parts) >= 12:
                    for servo in range(1, 5):
                        arduino_values[f'S{servo}V'] = parts[(servo-1)*3]
                        arduino_values[f'S{servo}A'] = parts[(servo-1)*3 + 1]
                        arduino_values[f'S{servo}P'] = parts[(servo-1)*3 + 2]
                        window[f'S{servo}V_display'].update(arduino_values[f'S{servo}V'])
                        window[f'S{servo}A_display'].update(arduino_values[f'S{servo}A'])
                        window[f'S{servo}P_display'].update(arduino_values[f'S{servo}P'])
                    values_received = True
                    
            elif message.startswith("BUTTON_STATES:"):
                parts = message.split(":")[1].split(",")
                if len(parts) >= 8:
                    for servo in range(1, 5):
                        state1 = parts[(servo-1)*2] == '1'
                        state2 = parts[(servo-1)*2 + 1] == '1'
                        servo_states[f'S{servo}B1'] = state1
                        servo_states[f'S{servo}B2'] = state2
                        window[f'S{servo}B1'].update(
                            'DISABLE' if state1 else 'ENABLE',
                            button_color=('white', 'red' if state1 else 'green'))
                        window[f'S{servo}B2'].update(
                            'STOP' if state2 else 'RUN',
                            button_color=('white', 'red' if state2 else 'green'))
                    states_received = True
            
            elif message.startswith("SETPOINTS:"):
                parts = message.split(":")[1].split(",")
                if len(parts) >= 12:
                    global S1V_SPT, S1A_SPT, S1P_SPT, S2V_SPT, S2A_SPT, S2P_SPT
                    global S3V_SPT, S3A_SPT, S3P_SPT, S4V_SPT, S4A_SPT, S4P_SPT
                    S1V_SPT, S1A_SPT, S1P_SPT = int(parts[0]), int(parts[1]), int(parts[2])
                    S2V_SPT, S2A_SPT, S2P_SPT = int(parts[3]), int(parts[4]), int(parts[5])
                    S3V_SPT, S3A_SPT, S3P_SPT = int(parts[6]), int(parts[7]), int(parts[8])
                    S4V_SPT, S4A_SPT, S4P_SPT = int(parts[9]), int(parts[10]), int(parts[11])
                    setpoints_received = True
            
            if values_received and states_received and setpoints_received:
                print("Debug - Initialization complete")
                return True
                
        except queue.Empty:
            time.sleep(0.1)
            
    print("Debug - Initialization timeout")
    return False

def validate_input(key, values, min_val, max_val):
    """Validate numeric input values.
    
    Args:
        key (str): Input field key
        values (dict): Input values
        min_val (int): Minimum allowed value
        max_val (int): Maximum allowed value
        
    Returns:
        int: Validated value or None if invalid
    """
    try:
        value = int(values[key])
        if min_val <= value <= max_val:
            return value
        print(f"Value out of range for {key}: {value}")
    except ValueError:
        print(f"Invalid value for {key}")
    return None


def initialize_from_arduino():
    """Initialize all values from Arduino."""
    print("Debug - Starting Arduino initialization...")
    
    # Clear message queue
    while not message_queue.empty():
        message_queue.get()
    
    # Request values with delays
    requests = [
        "CMD:REQUEST_VALUES\n",
        "CMD:REQUEST_BUTTON_STATES\n", 
        "CMD:REQUEST_SETPOINTS\n"
    ]
    
    for request in requests:
        print(f"Debug - Sending {request.strip()}")
        serialInst.write(request.encode('utf-8'))
        serialInst.flush()
        time.sleep(0.2)  # Allow time for Arduino response
    
    timeout = time.time() + 5  # 5 second timeout
    values_received = False
    states_received = False 
    setpoints_received = False

    while time.time() < timeout:
        try:
            message = message_queue.get(timeout=0.1)
            print(f"Debug - Received: {message}")
            
            if message.startswith("VALUES:"):
                parts = message.split(":")[1].split(",")
                if len(parts) >= 12:
                    for servo in range(1, 5):
                        idx = (servo-1)*3
                        arduino_values[f'S{servo}V'] = parts[idx]
                        arduino_values[f'S{servo}A'] = parts[idx+1]
                        arduino_values[f'S{servo}P'] = parts[idx+2]
                    values_received = True
                    print("Debug - Values received")
                    
            elif message.startswith("BUTTON_STATES:"):
                parts = message.split(":")[1].split(",")
                if len(parts) >= 8:
                    for servo in range(1, 5):
                        servo_states[f'S{servo}B1'] = parts[(servo-1)*2] == '1'
                        servo_states[f'S{servo}B2'] = parts[(servo-1)*2 + 1] == '1'
                    states_received = True
                    print("Debug - Button states received")
            
            elif message.startswith("SETPOINTS:"):
                parts = message.split(":")[1].split(",")
                if len(parts) >= 12:
                    global S1V_SPT, S1A_SPT, S1P_SPT, S2V_SPT, S2A_SPT, S2P_SPT
                    global S3V_SPT, S3A_SPT, S3P_SPT, S4V_SPT, S4A_SPT, S4P_SPT
                    S1V_SPT, S1A_SPT, S1P_SPT = int(parts[0]), int(parts[1]), int(parts[2])
                    S2V_SPT, S2A_SPT, S2P_SPT = int(parts[3]), int(parts[4]), int(parts[5])
                    S3V_SPT, S3A_SPT, S3P_SPT = int(parts[6]), int(parts[7]), int(parts[8])
                    S4V_SPT, S4A_SPT, S4P_SPT = int(parts[9]), int(parts[10]), int(parts[11])
                    setpoints_received = True
                    print("Debug - Setpoints received")
            
            if values_received and states_received and setpoints_received:
                print("Debug - All data received successfully")
                return True
                
        except queue.Empty:
            continue
            
    print("Debug - Initialization timeout")
    return False

# Initialize Arduino values before window creation
if not initialize_from_arduino():
    print("Error: Failed to initialize from Arduino")
    sys.exit(1)

def create_servo_row(servo_number, current_values, button_states):
    """Create dual-row servo controls with value display.
    
    Args:
        servo_number (int): Servo identifier (1-4)
        current_values (dict): Current parameter values
        button_states (dict): Button states
        
    Returns:
        list: GUI elements for servo row
    """
    # Use setpoint values for initialization
    setpoint_values = {
        1: (S1V_SPT, S1A_SPT, S1P_SPT),
        2: (S2V_SPT, S2A_SPT, S2P_SPT),
        3: (S3V_SPT, S3A_SPT, S3P_SPT),
        4: (S4V_SPT, S4A_SPT, S4P_SPT)
    }
    
    V_SPT, A_SPT, P_SPT = setpoint_values[servo_number]
    
    row1 = [
        sg.Text(f'Servo {servo_number}', size=(8, 1)),
        sg.Button('ENABLE', key=f'S{servo_number}B1', button_color=('white', 'green')),
        sg.Button('RUN', key=f'S{servo_number}B2', button_color=('white', 'green')),
        sg.Input(V_SPT, size=(10, 1), key=f'S{servo_number}V'),
        sg.Input(A_SPT, size=(10, 1), key=f'S{servo_number}A'),
        sg.Input(P_SPT, size=(10, 1), key=f'S{servo_number}P'),
        sg.Button('OK', key=f'S{servo_number}B3', button_color=('white', 'blue'))
    ]
    
    row2 = [
        sg.Text(' ', size=(20, 1)),
        sg.Text('Current Value'),
        sg.Text(' ', size=(2, 1)),
        sg.Text(arduino_values[f'S{servo_number}V'], size=(10, 1), key=f'S{servo_number}V_display'),
        sg.Text(arduino_values[f'S{servo_number}A'], size=(10, 1), key=f'S{servo_number}A_display'),
        sg.Text(arduino_values[f'S{servo_number}P'], size=(10, 1), key=f'S{servo_number}P_display')
    ]
    
    return [row1, row2]

# Setup GUI
current_values = {f'S{i}{p}': '0' for i in range(1, 5) for p in ['V', 'A', 'P']}
button_states = {f'S{i}B{j}': False for i in range(1, 5) for j in range(1, 3)}
servo_states = button_states.copy()

layout = [
    [sg.Text(' ', size=(34, 1)), sg.Text('Velocity', size=(8, 1)), sg.Text('Acceleration', size=(9, 1)),
     sg.Text('Position', size=(6, 1))],
    [sg.Text(' ', size=(34, 1)), sg.Text('(0-10000)', size=(8, 1)), sg.Text('(0-20000)', size=(9, 1)),
     sg.Text('(0-6000)', size=(12, 1)), sg.Text('', size=(8, 1))],
    *[row for i in range(1, 5) for row in create_servo_row(i, current_values, button_states)]
]

window = sg.Window("Servo Control", layout,
                  default_element_size=(6, 5),
                  size=(700, 500),
                  auto_size_text=True,
                  auto_size_buttons=False,
                  finalize=True)


    
while time.time() < timeout and not (values_received and states_received and setpoints_received):
    try:
        message = message_queue.get_nowait()
        
        if message.startswith("VALUES:"):
            parts = message.split(":")[1].split(",")
            if len(parts) >= 12:
                for servo in range(1, 5):
                    idx = (servo-1)*3
                    window[f'S{servo}V_display'].update(parts[idx])
                    window[f'S{servo}A_display'].update(parts[idx+1])
                    window[f'S{servo}P_display'].update(parts[idx+2])
                values_received = True
                
        elif message.startswith("BUTTON_STATES:"):
            parts = message.split(":")[1].split(",")
            if len(parts) >= 8:
                for servo in range(1, 5):
                    state1 = parts[(servo-1)*2] == '1'
                    state2 = parts[(servo-1)*2 + 1] == '1'
                    window[f'S{servo}B1'].update(
                        'DISABLE' if state1 else 'ENABLE',
                        button_color=('white', 'red' if state1 else 'green'))
                    window[f'S{servo}B2'].update(
                        'STOP' if state2 else 'RUN',
                        button_color=('white', 'red' if state2 else 'green'))
                states_received = True
                
        elif message.startswith("SETPOINTS:"):
            parts = message.split(":")[1].split(",")
            if len(parts) >= 12:
                for servo in range(1, 5):
                    idx = (servo-1)*3
                    window[f'S{servo}V'].update(parts[idx])
                    window[f'S{servo}A'].update(parts[idx+1])
                    window[f'S{servo}P'].update(parts[idx+2])
                setpoints_received = True
                
    except queue.Empty:
        time.sleep(0.1)

if not (values_received and states_received and setpoints_received):
    print("Warning: Initialization timeout - some values may not be updated")

# Event Loop
# In event loop
# Replace event loop
# Add debug prints in event loop
# Replace event loop with optimized version
last_gui_update = time.time()

# Replace event loop
# Event Loop
while True:
    try:
        event, values = window.read(timeout=WINDOW_READ_TIMEOUT)
        
        if event in (sg.WIN_CLOSED, 'Exit'):
            print("Debug - Window closing...")
            break
            
        # High Priority - Handle Input Events
        if event and isinstance(event, str):
            if event.endswith('B3'):  # OK button pressed
                servo = int(event[1])
                V_data = validate_input(f'S{servo}V', values, 0, 10000)
                A_data = validate_input(f'S{servo}A', values, 0, 20000)
                P_data = validate_input(f'S{servo}P', values, 0, 6000)
                if all(x is not None for x in (V_data, A_data, P_data)):
                    cmd = f"CMD:S{servo}_Parameters:{V_data},{A_data},{P_data}\n"
                    serialInst.write(cmd.encode('utf-8'))
                    serialInst.flush()
            
            # Button state changes
            elif event.endswith(('B1', 'B2')):
                servo = int(event[1])
                button_type = event[-2:]
                cmd_type = "ENABLE" if button_type == "B1" else "START"
                servo_states[event] = handle_servo_buttons(
                    event, event,
                    f"S{servo}{button_type} {cmd_type}",
                    f"S{servo}{button_type} {'DISABLE' if cmd_type == 'ENABLE' else 'STOP'}",
                    servo_states[event])
        
        # Medium Priority - Process Messages
        current_time = time.time()
        if current_time - last_request_time > REQUEST_INTERVAL:
            serialInst.write("CMD:REQUEST_VALUES\n".encode('utf-8'))
            serialInst.flush()
            last_request_time = current_time

        # Low Priority - Update Display
        if current_time - last_gui_update > GUI_UPDATE_INTERVAL:
            updates_needed = False
            try:
                for _ in range(BATCH_SIZE):
                    message = message_queue.get_nowait()
                    if message.startswith("VALUES:"):
                        parts = message.split(":")[1].split(",")
                        if len(parts) >= 12:
                            updates_needed = True
                            for servo in range(1, 5):
                                idx = (servo-1)*3
                                arduino_values[f'S{servo}V'] = parts[idx]
                                arduino_values[f'S{servo}A'] = parts[idx+1]
                                arduino_values[f'S{servo}P'] = parts[idx+2]
            except queue.Empty:
                pass

            if updates_needed:
                for servo in range(1, 5):
                    window[f'S{servo}V_display'].update(arduino_values[f'S{servo}V'])
                    window[f'S{servo}A_display'].update(arduino_values[f'S{servo}A'])
                    window[f'S{servo}P_display'].update(arduino_values[f'S{servo}P'])
                window.refresh()
                last_gui_update = current_time

    except Exception as e:
        print(f"Debug - Error in event loop: {e}")
        break

# Cleanup
print("Debug - Cleaning up...")
window.close()
serial_thread.stop()
serial_thread.join()
serialInst.close()