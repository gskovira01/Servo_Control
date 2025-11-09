import PySimpleGUI as sg # type: ignore
import serial # type: ignore
import threading
import queue
import time
import sys

# Global state
state_engine_step = 0
DEBUG = True  # Global debug flag to control debug output
arduino_values = {f'S{i}{p}': '0' for i in range(1, 5) for p in ['V', 'A', 'P']}
button_states = {f'S{i}B{j}': False for i in range(1, 5) for j in range(1, 3)}  # Changed to range(1, 3)
servo_states = button_states.copy()
current_values = {}  # Initialize current_values dictionary

values_received = False
states_received = False  
setpoints_received = False

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
S1P_SPT = 0     # Servo1 Position Setpoint
S2V_SPT = 1000  # Servo2 Velocity Setpoint
S2A_SPT = 2000  # Servo2 Actual Setpoint
S2P_SPT = 0     # Servo2 Position Setpoint
S3V_SPT = 1000  # Servo3 Velocity Setpoint
S3A_SPT = 2000  # Servo3 Actual Setpoint
S3P_SPT = 0     # Servo3 Position Setpoint
S4V_SPT = 1000  # Servo4 Velocity Setpoint
S4A_SPT = 2000  # Servo4 Actual Setpoint
S4P_SPT = 0     # Servo4 Position Setpoint

def initialize_serial_connection(port, baudrate=9600, timeout=1):
    """Initialize serial connection with error handling."""
    try:
        print(f"Debug - Opening {port}")
        serial_inst = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
        serial_inst.reset_input_buffer()
        print("Debug - Serial port opened")
        return serial_inst
    except Exception as e:
        print(f"Debug - Serial port error: {e}")
        raise

# Function to handle momentary pulse for start buttons
def momentary_pulse(button_key, duration=0.25):
    window[button_key].update(button_color=('white', 'green'))  # Change button color to indicate press
    time.sleep(duration)  # Wait for the specified duration
    window[button_key].update(button_color=('white', 'grey'))  # Reset button color

def initialize_from_arduino():
    """Initialize all values from Arduino."""
    global values_received, states_received, setpoints_received, servo_states, current_values
    MAX_RETRIES = 3
    TIMEOUT = 5
    
    for attempt in range(MAX_RETRIES):
        print(f"Debug - Starting Arduino initialization (attempt {attempt + 1}/{MAX_RETRIES})")
        
        # Reset state
        values_received = False
        states_received = False
        setpoints_received = False
        
        # Clear buffers
        serialInst.reset_input_buffer()
        serialInst.reset_output_buffer()
        while not message_queue.empty():
            message_queue.get()
            
        # Request initialization data
        for request, expected in [
            ("CMD:REQUEST_VALUES\n", "VALUES:"),
            ("CMD:REQUEST_BUTTON_STATES\n", "BUTTON_STATES:"),
            ("CMD:REQUEST_SETPOINTS\n", "SETPOINTS:")
        ]:
            print(f"Debug - Sending: {request.strip()}")
            serialInst.write(request.encode('utf-8'))
            serialInst.flush()
            time.sleep(0.5)
            
            # Wait for response
            timeout = time.time() + TIMEOUT
            while time.time() < timeout:
                try:
                    message = message_queue.get(timeout=0.5)
                    print(f"Debug - Received: {message}")
                    
                    if message.startswith(expected):
                        if process_response(message, expected):
                            print(f"Debug - Valid {expected} received")
                            break
                except queue.Empty:
                    continue
            else:
                print(f"Debug - Timeout waiting for {expected}")
                break
            
            time.sleep(0.2)
        
        if all([values_received, states_received, setpoints_received]):
            print("Debug - Initialization successful")
            servo_states = button_states.copy()  # Sync servo_states with button_states
            print(f"Debug - Servo states initialized to: {servo_states}")
            # Add setpoints to current_values
            current_values.update({
                'S1V_SPT': S1V_SPT, 'S1A_SPT': S1A_SPT, 'S1P_SPT': S1P_SPT,
                'S2V_SPT': S2V_SPT, 'S2A_SPT': S2A_SPT, 'S2P_SPT': S2P_SPT,
                'S3V_SPT': S3V_SPT, 'S3A_SPT': S3A_SPT, 'S3P_SPT': S3P_SPT,
                'S4V_SPT': S4V_SPT, 'S4A_SPT': S4A_SPT, 'S4P_SPT': S4P_SPT
            })
            return True
            
        print(f"Debug - Initialization attempt {attempt + 1} failed")
        time.sleep(2)
    
    return False

def process_response(message, expected):
    """Process and validate Arduino responses."""
    global values_received, states_received, setpoints_received, servo_states, state_engine_step
    
    parts = message.split(":")[1].split(",")
    print(f"Debug - Raw message parts: {parts}")  # Add debug print
    
    if expected == "VALUES:" and len(parts) >= 12:
        for servo in range(1, 5):
            idx = (servo-1)*3
            arduino_values[f'S{servo}V'] = parts[idx]
            arduino_values[f'S{servo}A'] = parts[idx+1]
            arduino_values[f'S{servo}P'] = parts[idx+2]
        values_received = True
        print(f"Debug - Updated arduino_values: {arduino_values}")  # Add debug print
        return True
        
    elif expected == "BUTTON_STATES:" and len(parts) >= 8:
        print(f"Debug - Processing button states: {parts}")
        for servo in range(1, 5):
            # Update both button_states and servo_states
            button_states[f'S{servo}B1'] = parts[(servo-1)*2] == '1'
            button_states[f'S{servo}B2'] = parts[(servo-1)*2 + 1] == '1'
            servo_states[f'S{servo}B1'] = button_states[f'S{servo}B1']
            servo_states[f'S{servo}B2'] = button_states[f'S{servo}B2']
            print(f"Debug - Servo {servo} button states: B1={button_states[f'S{servo}B1']}, B2={button_states[f'S{servo}B2']}")

        states_received = True
        return True
        
    elif expected == "SETPOINTS:" and len(parts) >= 12:
        global S1V_SPT, S1A_SPT, S1P_SPT, S2V_SPT, S2A_SPT, S2P_SPT
        global S3V_SPT, S3A_SPT, S3P_SPT, S4V_SPT, S4A_SPT, S4P_SPT
        try:
            S1V_SPT, S1A_SPT, S1P_SPT = map(int, parts[0:3])
            S2V_SPT, S2A_SPT, S2P_SPT = map(int, parts[3:6])
            S3V_SPT, S3A_SPT, S3P_SPT = map(int, parts[6:9])
            S4V_SPT, S4A_SPT, S4P_SPT = map(int, parts[9:12])
            setpoints_received = True
            print(f"Debug - Updated setpoints: S1V_SPT={S1V_SPT}, S2V_SPT={S2V_SPT}, S3V_SPT={S3V_SPT}, S4V_SPT={S4V_SPT}")  # Add debug print
            return True
        except ValueError:
            print("Debug - Invalid setpoint values received")
            return False

    elif expected == "STATE_ENGINE_STEP:":
        state_engine_step = int(parts[0])
        print(f"Debug - Updated state_engine_step: {state_engine_step}")  # Add debug print
        return True
            
    return False

class SerialThread(threading.Thread):
    """Async serial port monitoring thread."""
    def __init__(self, serial_port, message_queue):
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
                    self.message_queue.put(line)
                except Exception as e:
                    print(f"Debug - Serial error: {e}")
            time.sleep(0.1)

    def stop(self):
        """Stop thread execution."""
        self.running = False

def handle_servo_buttons(event, button_id, enable_command, disable_command, enabled):
    """Handle servo button events and state changes."""
    if event == button_id:
        if enabled:
            serialInst.write(f"CMD:{disable_command}\n".encode('utf-8'))
            window[button_id].update(
                text='ENABLE' if 'ENABLE' in enable_command else 'RUN',
                button_color=('white', 'green'))
            button_states[button_id] = False  # Update button_states
        else:
            serialInst.write(f"CMD:{enable_command}\n".encode('utf-8'))
            window[button_id].update(
                text='DISABLE' if 'ENABLE' in enable_command else 'STOP',
                button_color=('white', 'red'))
            button_states[button_id] = True  # Update button_states
        serialInst.flush()
        return not enabled
    return enabled

def validate_input(key, values, min_val, max_val):
    """Validate numeric input values."""
    try:
        value = int(values[key])
        if min_val <= value <= max_val:
            return value
        print(f"Value out of range for {key}: {value}")
    except ValueError:
        print(f"Invalid value for {key}")
    return None

# Initialize components
serialInst = initialize_serial_connection('COM10')
message_queue = queue.Queue()
serial_thread = SerialThread(serialInst, message_queue)
serial_thread.start()

# Initialize Arduino values before window creation
current_values = {}  # Initialize current_values dictionary
if not initialize_from_arduino():
    print("Error: Failed to initialize from Arduino")
    sys.exit(1)

# Debug print to verify button states
print(f"Debug - Button states after initialization: {button_states}")

# Setup GUI
current_values = arduino_values.copy()  # Use fetched values for current_values
# Add setpoints to current_values
current_values.update({
    'S1V_SPT': S1V_SPT, 'S1A_SPT': S1A_SPT, 'S1P_SPT': S1P_SPT,
    'S2V_SPT': S2V_SPT, 'S2A_SPT': S2A_SPT, 'S2P_SPT': S2P_SPT,
    'S3V_SPT': S3V_SPT, 'S3A_SPT': S3A_SPT, 'S3P_SPT': S3P_SPT,
    'S4V_SPT': S4V_SPT, 'S4A_SPT': S4A_SPT, 'S4P_SPT': S4P_SPT
})
# button_states is already populated by initialize_from_arduino()

# Before creating the window, modify the layout initialization to explicitly set button colors
layout = [
    [sg.Text('State Engine Step:', size=(15, 1), justification='right', font=('Helvetica', 12, 'bold')), sg.Text('0', size=(3, 1), key='state_engine_step_display', font=('Helvetica', 12, 'bold'))],
    [sg.Text(' ', size=(30, 1)), sg.Text('Velocity', size=(8, 1)), sg.Text('Acceleration', size=(9, 1)),
     sg.Text('Position', size=(6, 1))],
    [sg.Text(' ', size=(30, 1)), sg.Text('(0-10000)', size=(8, 1)), sg.Text('(0-20000)', size=(9, 1)),
     sg.Text('(0-6000)', size=(12, 1)), sg.Text('', size=(8, 1))],

    # Servo 1 Row
    [sg.Text('Servo 1', size=(8, 1)), 
     sg.Button('DISABLE' if button_states['S1B1'] else 'ENABLE', 
              key='S1B1', 
              button_color=('white', 'red') if button_states['S1B1'] else ('white', 'green')),
     sg.Button('STOP' if button_states['S1B2'] else 'RUN',
              key='S1B2',
              button_color=('white', 'red') if button_states['S1B2'] else ('white', 'green')),
     sg.InputText(current_values['S1V_SPT'], key='S1V_SPT', size=(8, 1), justification='right'),
     sg.InputText(current_values['S1A_SPT'], key='S1A_SPT', size=(8, 1), justification='right'),
     sg.InputText(current_values['S1P_SPT'], key='S1P_SPT', size=(8, 1), justification='right'),
     sg.Button('OK', key='S1B3')],
    [sg.Text(' ', size=(17, 1)), sg.Text('Setpoint', size=(14, 1), justification='right'),  # Adjusted size
     sg.Text(current_values['S1V_SPT'], size=(7, 1), key='S1V_SPT_display', justification='right'),
     sg.Text(current_values['S1A_SPT'], size=(7, 1), key='S1A_SPT_display', justification='right'),
     sg.Text(current_values['S1P_SPT'], size=(7, 1), key='S1P_SPT_display', justification='right')],
    [sg.Text(' ', size=(17, 1)), sg.Text('Current Value', size=(14, 1), justification='right'),  # Adjusted size
     sg.Text(arduino_values['S1V'], size=(7, 1), key='S1V_display', justification='right'),
     sg.Text(arduino_values['S1A'], size=(7, 1), key='S1A_display', justification='right'),
     sg.Text(arduino_values['S1P'], size=(7, 1), key='S1P_display', justification='right')],

    # Servo 2 Row
    [sg.Text('Servo 2', size=(8, 1)), 
     sg.Button('DISABLE' if button_states['S2B1'] else 'ENABLE', 
              key='S2B1', 
              button_color=('white', 'red') if button_states['S2B1'] else ('white', 'green')),
     sg.Button('STOP' if button_states['S2B2'] else 'RUN',
              key='S2B2',
              button_color=('white', 'red') if button_states['S2B2'] else ('white', 'green')),
     sg.InputText(current_values['S2V_SPT'], key='S2V_SPT', size=(8, 1), justification='right'),
     sg.InputText(current_values['S2A_SPT'], key='S2A_SPT', size=(8, 1), justification='right'),
     sg.InputText(current_values['S2P_SPT'], key='S2P_SPT', size=(8, 1), justification='right'),
     sg.Button('OK', key='S2B3')],
    [sg.Text(' ', size=(17, 1)), sg.Text('Setpoint', size=(14, 1), justification='right'),  # Adjusted size
     sg.Text(current_values['S2V_SPT'], size=(7, 1), key='S2V_SPT_display', justification='right'),
     sg.Text(current_values['S2A_SPT'], size=(7, 1), key='S2A_SPT_display', justification='right'),
     sg.Text(current_values['S2P_SPT'], size=(7, 1), key='S2P_SPT_display', justification='right')],
    [sg.Text(' ', size=(17, 1)), sg.Text('Current Value', size=(14, 1), justification='right'),  # Adjusted size
     sg.Text(arduino_values['S2V'], size=(7, 1), key='S2V_display', justification='right'),
     sg.Text(arduino_values['S2A'], size=(7, 1), key='S2A_display', justification='right'),
     sg.Text(arduino_values['S2P'], size=(7, 1), key='S2P_display', justification='right')],

    # Servo 3 Row
    [sg.Text('Servo 3', size=(8, 1)), 
     sg.Button('DISABLE' if button_states['S3B1'] else 'ENABLE', 
              key='S3B1', 
              button_color=('white', 'red') if button_states['S3B1'] else ('white', 'green')),
     sg.Button('STOP' if button_states['S3B2'] else 'RUN',
              key='S3B2',
              button_color=('white', 'red') if button_states['S3B2'] else ('white', 'green')),
     sg.InputText(current_values['S3V_SPT'], key='S3V_SPT', size=(8, 1), justification='right'),
     sg.InputText(current_values['S3A_SPT'], key='S3A_SPT', size=(8, 1), justification='right'),
     sg.InputText(current_values['S3P_SPT'], key='S3P_SPT', size=(8, 1), justification='right'),
     sg.Button('OK', key='S3B3')],
    [sg.Text(' ', size=(17, 1)), sg.Text('Setpoint', size=(14, 1), justification='right'),  # Adjusted size
     sg.Text(current_values['S3V_SPT'], size=(7, 1), key='S3V_SPT_display', justification='right'),
     sg.Text(current_values['S3A_SPT'], size=(7, 1), key='S3A_SPT_display', justification='right'),
     sg.Text(current_values['S3P_SPT'], size=(7, 1), key='S3P_SPT_display', justification='right')],
    [sg.Text(' ', size=(17, 1)), sg.Text('Current Value', size=(14, 1), justification='right'),  # Adjusted size
     sg.Text(arduino_values['S3V'], size=(7, 1), key='S3V_display', justification='right'),
     sg.Text(arduino_values['S3A'], size=(7, 1), key='S3A_display', justification='right'),
     sg.Text(arduino_values['S3P'], size=(7, 1), key='S3P_display', justification='right')],

    # Servo 4 Row
    [sg.Text('Servo 4', size=(8, 1)), 
     sg.Button('DISABLE' if button_states['S4B1'] else 'ENABLE', 
              key='S4B1', 
              button_color=('white', 'red') if button_states['S4B1'] else ('white', 'green')),
     sg.Button('STOP' if button_states['S4B2'] else 'RUN',
              key='S4B2',
              button_color=('white', 'red') if button_states['S4B2'] else ('white', 'green')),
     sg.InputText(current_values['S4V_SPT'], key='S4V_SPT', size=(8, 1), justification='right'),
     sg.InputText(current_values['S4A_SPT'], key='S4A_SPT', size=(8, 1), justification='right'),
     sg.InputText(current_values['S4P_SPT'], key='S4P_SPT', size=(8, 1), justification='right'),
     sg.Button('OK', key='S4B3')],
    [sg.Text(' ', size=(17, 1)), sg.Text('Setpoint', size=(14, 1), justification='right'),  # Adjusted size
     sg.Text(current_values['S4V_SPT'], size=(7, 1), key='S4V_SPT_display', justification='right'),
     sg.Text(current_values['S4A_SPT'], size=(7, 1), key='S4A_SPT_display', justification='right'),
     sg.Text(current_values['S4P_SPT'], size=(7, 1), key='S4P_SPT_display', justification='right')],
    [sg.Text(' ', size=(17, 1)), sg.Text('Current Value', size=(14, 1), justification='right'),  # Adjusted size
     sg.Text(arduino_values['S4V'], size=(7, 1), key='S4V_display', justification='right'),
     sg.Text(arduino_values['S4A'], size=(7, 1), key='S4A_display', justification='right'),
     sg.Text(arduino_values['S4P'], size=(7, 1), key='S4P_display', justification='right')]
]

window = sg.Window("Servo Control", 
            layout, default_element_size=(8, 5), 
            size=(700, 500), 
            auto_size_text=False, 
            auto_size_buttons=False, 
            finalize=True)

# Force update button states immediately after window creation
print("Debug - Forcing button state updates after window creation")
for servo in range(1, 5):
    for btn in ['B1', 'B2']:
        btn_key = f'S{servo}{btn}'
        is_enabled = button_states[btn_key]
        btn_text = 'DISABLE' if is_enabled else ('ENABLE' if btn == 'B1' else 'RUN')
        btn_color = ('white', 'red') if is_enabled else ('white', 'green')
        window[btn_key].update(text=btn_text, button_color=btn_color)
        print(f"Debug - Initial button update: {btn_key}={is_enabled}, color={btn_color}, text={btn_text}")

# Request button states again to ensure we have latest state
serialInst.write("CMD:REQUEST_BUTTON_STATES\n".encode('utf-8'))
serialInst.flush()

# Event Loop
WINDOW_READ_TIMEOUT = 10     # Faster window response (ms)
REQUEST_INTERVAL = 0.5       # Reduced Arduino polling (sec)
GUI_UPDATE_INTERVAL = 0.2    # Faster display updates (sec)
BATCH_SIZE = 10   

last_request_time = time.time()
last_gui_update = time.time()


# Event Loop
while True:
    try:
        event, values = window.read(timeout=WINDOW_READ_TIMEOUT)
        
        if event in (sg.WIN_CLOSED, 'Exit'):
            print("Debug - Window closed or Exit event triggered")
            break
            
        # High Priority - Button Events
        if event and isinstance(event, str):
            if event != '__TIMEOUT__':
                print(f"Debug - Event: {event}")
            if event.endswith(('B1', 'B2')):  # Enable/Run buttons
                servo = int(event[1])
                button_type = event[-2:]
                cmd_type = "ENABLE" if button_type == "B1" else "START"
                button_states[event] = not button_states[event]  # Toggle state
                servo_states[event] = handle_servo_buttons(
                    event, event,
                    f"S{servo}{button_type} {cmd_type}",
                    f"S{servo}{button_type} {'DISABLE' if cmd_type == 'ENABLE' else 'STOP'}",
                    servo_states[event])
                window.refresh()  # Immediate update
            
            elif event.endswith('B3'):  # OK button - parameter update
                servo = int(event[1])
                V_data = validate_input(f'S{servo}V_SPT', values, 0, 10000)
                A_data = validate_input(f'S{servo}A_SPT', values, 0, 20000)
                P_data = validate_input(f'S{servo}P_SPT', values, 0, 6000)
                if all(x is not None for x in (V_data, A_data, P_data)):
                    cmd = f"CMD:S{servo}_Parameters:{V_data},{A_data},{P_data}\n"
                    print(f"Debug - Sending command: {cmd.strip()}")  # Add debug print
                    serialInst.write(cmd.encode('utf-8'))
                    serialInst.flush()
                    # Update current_values and corresponding sg.Text elements
                    current_values[f'S{servo}V_SPT'] = V_data
                    current_values[f'S{servo}A_SPT'] = A_data
                    current_values[f'S{servo}P_SPT'] = P_data
                    window[f'S{servo}V_SPT_display'].update(V_data)
                    window[f'S{servo}A_SPT_display'].update(A_data)
                    window[f'S{servo}P_SPT_display'].update(P_data)
                    window.refresh()
                    print(f"Debug - Updated setpoints for S{servo}: V_SPT={V_data}, A_SPT={A_data}, P_SPT={P_data}")  # Add debug print
        
        # Background Tasks - Only process if no pending events
        current_time = time.time()
        
        # Medium Priority - Process Messages (reduced frequency)
        if current_time - last_request_time > REQUEST_INTERVAL:
            serialInst.write("CMD:REQUEST_VALUES\n".encode('utf-8'))
            serialInst.flush()
            last_request_time = current_time

        # Low Priority - Batch Update Display
        if current_time - last_gui_update > GUI_UPDATE_INTERVAL:
            updates = []
            try:
                for _ in range(BATCH_SIZE):
                    message = message_queue.get_nowait()
                    if DEBUG:
                        print(f"Debug - Processing message: {message}")
                    if message.startswith("VALUES:"):
                        parts = message.split(":")[1].split(",")
                        if len(parts) >= 12:
                            updates.append((parts, current_time))
                    elif message.startswith("STATE_ENGINE_STEP:"):
                        process_response(message, "STATE_ENGINE_STEP:")
            except queue.Empty:
                pass

            # Apply updates in batch
            if updates:
                latest_update = updates[-1]  # Use most recent update
                parts = latest_update[0]
                for servo in range(1, 5):
                    idx = (servo-1)*3
                    arduino_values[f'S{servo}V'] = parts[idx]
                    arduino_values[f'S{servo}A'] = parts[idx+1]
                    arduino_values[f'S{servo}P'] = parts[idx+2]
                    if DEBUG:
                        print(f"Debug - Updating display for Servo {servo}: V={parts[idx]}, A={parts[idx+1]}, P={parts[idx+2]}")
                    window[f'S{servo}V_display'].update(parts[idx])
                    window[f'S{servo}A_display'].update(parts[idx+1])
                    window[f'S{servo}P_display'].update(parts[idx+2])
                    window[f'S{servo}V_SPT_display'].update(current_values[f'S{servo}V_SPT'])
                    window[f'S{servo}A_SPT_display'].update(current_values[f'S{servo}A_SPT'])
                    window[f'S{servo}P_SPT_display'].update(current_values[f'S{servo}P_SPT'])
                last_gui_update = current_time

        # Update state engine step display
        window['state_engine_step_display'].update(state_engine_step)

    except Exception as e:
        if DEBUG:
            print(f"Debug - Error in event loop: {e}")
        break

# Cleanup
print("Debug - Cleaning up...")
window.close()
serial_thread.stop()
serial_thread.join()
serialInst.close()