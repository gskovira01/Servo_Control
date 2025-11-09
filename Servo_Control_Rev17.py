import PySimpleGUI as sg # type: ignore
import serial # type: ignore
import threading
import queue
import time
import sys

# Global state
state_engine_step = 0
DEBUG = True  # Global debug flag to control debug output

# Constants
WINDOW_READ_TIMEOUT = 100  # Window read timeout in milliseconds
REQUEST_INTERVAL = .5  # Reduced Arduino polling (sec)
GUI_UPDATE_INTERVAL = 0.2  # Faster display updates (sec)
BATCH_SIZE = 30
DEBOUNCE_INTERVAL = 0.5  # Debounce interval in seconds


# The code snippet initializes a dictionary named arduino_values with keys representing different 
# parameters (velocity, acceleration, and position) for four servos (S1, S2, S3, and S4). Each 
# key is associated with an initial value of '0'.
arduino_values ={  
    'S1V': '0', 'S1A': '0', 'S1P': '0',
    'S2V': '0', 'S2A': '0', 'S2P': '0',
    'S3V': '0', 'S3A': '0', 'S3P': '0',
    'S4V': '0', 'S4A': '0', 'S4P': '0'
}
# The code snippet initializes a dictionary named named GUI_button_states with keys representing 
# the states of buttons for four servos (S1, S2, S3, and S4). Each servo has two buttons (B1 and B2). 
# The initial state of each button # is set to False, indicating that the buttons are not pressed or enabled.
GUI_button_states = {
    'Mode': False, 'Mode': False,
    'S1B1': False, 'S1B2': False,
    'S2B1': False, 'S2B2': False,
    'S3B1': False, 'S3B2': False,
    'S4B1': False, 'S4B2': False
}
CNT_button_states = GUI_button_states.copy()  # Initialize CNT_button_states as a copy of button_states

# Current Values
Mode = 0  # Mode
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

current_values = { 
    'Mode' : Mode,
    'S1V_SPT': S1V_SPT, 'S1A_SPT': S1A_SPT, 'S1P_SPT': S1P_SPT,
    'S2V_SPT': S2V_SPT, 'S2A_SPT': S2A_SPT, 'S2P_SPT': S2P_SPT,
    'S3V_SPT': S3V_SPT, 'S3A_SPT': S3A_SPT, 'S3P_SPT': S3P_SPT,
    'S4V_SPT': S4V_SPT, 'S4A_SPT': S4A_SPT, 'S4P_SPT': S4P_SPT
}

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

class SerialThread(threading.Thread):
    def __init__(self, serial_port, message_queue):
        super().__init__()
        self.serial_port = serial_port
        self.message_queue = message_queue
        self.running = True
        
    def run(self):
        while self.running:
            try:
                if self.serial_port.in_waiting:
                    line = self.serial_port.readline().decode('utf-8').rstrip()
                    if line:
                        self.message_queue.put(line)
                        if DEBUG:
                            print(f"Debug - Serial message received: {line}")
                else:
                    time.sleep(0.01)  # Prevent CPU hogging
            except Exception as e:
                print(f"Debug - Serial error: {e}")
                self.running = False

    def stop(self):
        """Stop thread execution."""
        self.running = False

def initialize_serial_connection(port, baudrate=9600, timeout=1):
    """Initialize serial connection with error handling."""
    try:
        print(f"Debug 1 - Opening {port}")
        serial_inst = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
        serial_inst.reset_input_buffer()
        print("Debug 2 - Serial port opened")
        return serial_inst
    except Exception as e:
        print(f"Debug 3 - Serial port error: {e}")
        raise


# Initialize components
serialInst = initialize_serial_connection('COM10')
message_queue = queue.Queue()
serial_thread = SerialThread(serialInst, message_queue)
serial_thread.start()

# Define window read timeout
WINDOW_READ_TIMEOUT = 100  # Set to an appropriate value in milliseconds


def initialize_from_arduino(window):
    """Initialize all values from Arduino."""
    #The function initialize_from_arduino(window) is designed to initialize 
    # all values from an Arduino device. It communicates with the Arduino to 
    # request and receive various data, such as current values, button states, 
    # and setpoints. The function ensures that the GUI is synchronized with the 
    # Arduino's state.

    global values_received, states_received, setpoints_received, CNT_button_states, current_values
    MAX_RETRIES = 3
    TIMEOUT = 5
    
    for attempt in range(MAX_RETRIES):
        print(f"Debug 4 - Starting Arduino initialization (attempt {attempt + 1}/{MAX_RETRIES})")
        
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
            print(f"Debug 5 - Sending: {request.strip()}")
            serialInst.write(request.encode('utf-8'))
            serialInst.flush()
            time.sleep(0.5)
            
            # Wait for response
            timeout = time.time() + TIMEOUT
            while time.time() < timeout:
                try:
                    message = message_queue.get(timeout=0.5)
                    print(f"Debug 6 - Received: {message}")
                    
                    if message.startswith(expected):
                        if process_response(message, expected, window):
                            print(f"Debug 7 - Valid {expected} received")
                            break
                except queue.Empty:
                    continue
            else:
                print(f"Debug 8 - Timeout waiting for {expected}")
                break
            
            time.sleep(0.2)
        
        if all([values_received, states_received, setpoints_received]):
            print("Debug 9 - Initialization successful")
            CNT_button_states = GUI_button_states.copy()  # Sync CNT_button_states with GUI_button_states
            print(f"Debug 10 - Servo states initialized to: {CNT_button_states}")
            # Add setpoints to current_values
            current_values.update({
                'S1V_SPT': S1V_SPT, 'S1A_SPT': S1A_SPT, 'S1P_SPT': S1P_SPT,
                'S2V_SPT': S2V_SPT, 'S2A_SPT': S2A_SPT, 'S2P_SPT': S2P_SPT,
                'S3V_SPT': S3V_SPT, 'S3A_SPT': S3A_SPT, 'S3P_SPT': S3P_SPT,
                'S4V_SPT': S4V_SPT, 'S4A_SPT': S4A_SPT, 'S4P_SPT': S4P_SPT
            })
            return True
            
        print(f"Debug 11 - Initialization attempt {attempt + 1} failed")
        time.sleep(2)
    
    return False
def process_response(message, expected, window):

    """Process and validate Arduino responses."""
    #The function process_response(message, expected, window) is designed
    #to process and validate responses received from the Arduino. It updates 
    # the global state and GUI elements based on the type of response received.
    
    global values_received, states_received, setpoints_received, CNT_button_states, state_engine_step
    
    print(f"Debug 12 - Processing message: {message}")  # Add debug print
    parts = message.split(":")[1].split(",")
    print(f"Debug 13 - Raw message parts: {parts}")  # Add debug print
    
    if expected == "VALUES:" and len(parts) >= 12:
        print("Debug 14 - Entered VALUES block")  # Add debug print
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
        values_received = True
        print(f"Debug 15 - Updated arduino_values: {arduino_values}")  # Add debug print
        
        # Update the GUI with the new values
        window['S1V_display'].update(arduino_values['S1V'])
        window['S1A_display'].update(arduino_values['S1A'])
        window['S1P_display'].update(arduino_values['S1P'])
        window['S2V_display'].update(arduino_values['S2V'])
        window['S2A_display'].update(arduino_values['S2A'])
        window['S2P_display'].update(arduino_values['S2P'])
        window['S3V_display'].update(arduino_values['S3V'])
        window['S3A_display'].update(arduino_values['S3A'])
        window['S3P_display'].update(arduino_values['S3P'])
        window['S4V_display'].update(arduino_values['S4V'])
        window['S4A_display'].update(arduino_values['S4A'])
        window['S4P_display'].update(arduino_values['S4P'])
        
        window.refresh()  # Refresh the GUI

        print("Debug 16 - Returning True for VALUES:")  # Add debug print
        return True
        
    elif expected == "BUTTON_STATES:" and len(parts) >= 8:
        print(f"Debug 17 - Processing button states: {parts}")
        GUI_button_states['Mode'] = True if parts[0] == '1' else False
        GUI_button_states['S1B1'] = True if parts[0] == '1' else False
        GUI_button_states['S1B2'] = True if parts[1] == '1' else False
        GUI_button_states['S2B1'] = True if parts[2] == '1' else False
        GUI_button_states['S2B2'] = True if parts[3] == '1' else False
        GUI_button_states['S3B1'] = True if parts[4] == '1' else False
        GUI_button_states['S3B2'] = True if parts[5] == '1' else False
        GUI_button_states['S4B1'] = True if parts[6] == '1' else False
        GUI_button_states['S4B2'] = True if parts[7] == '1' else False
        CNT_button_states['Mode'] = GUI_button_states['Mode']
        CNT_button_states['S1B1'] = GUI_button_states['S1B1']
        CNT_button_states['S1B2'] = GUI_button_states['S1B2']
        CNT_button_states['S2B1'] = GUI_button_states['S2B1']
        CNT_button_states['S2B2'] = GUI_button_states['S2B2']
        CNT_button_states['S3B1'] = GUI_button_states['S3B1']
        CNT_button_states['S3B2'] = GUI_button_states['S3B2']
        CNT_button_states['S4B1'] = GUI_button_states['S4B1']
        CNT_button_states['S4B2'] = GUI_button_states['S4B2']
        print(f"Debug 18 - Servo button states updated")
        states_received = True
        return True
        
    elif expected == "SETPOINTS:" and len(parts) >= 12:
        global S1V_SPT, S1A_SPT, S1P_SPT, S2V_SPT, S2A_SPT, S2P_SPT
        global S3V_SPT, S3A_SPT, S3P_SPT, S4V_SPT, S4A_SPT, S4P_SPT
        try:
        # Map and assign setpoints
            S1V_SPT, S1A_SPT, S1P_SPT = map(int, parts[0:3])
            S2V_SPT, S2A_SPT, S2P_SPT = map(int, parts[3:6])
            S3V_SPT, S3A_SPT, S3P_SPT = map(int, parts[6:9])
            S4V_SPT, S4A_SPT, S4P_SPT = map(int, parts[9:12])
            setpoints_received = True

            # Debug prints
            print(f"Debug 19 - Updated setpoints: S1V_SPT={S1V_SPT}, S2V_SPT={S2V_SPT}, S3V_SPT={S3V_SPT}, S4V_SPT={S4V_SPT}")
            print(f"Debug 19a - Updating setpoints in GUI")

            # Update current_values dictionary
            current_values['S1V_SPT'] = S1V_SPT
            current_values['S1A_SPT'] = S1A_SPT
            current_values['S1P_SPT'] = S1P_SPT
            current_values['S2V_SPT'] = S2V_SPT
            current_values['S2A_SPT'] = S2A_SPT
            current_values['S2P_SPT'] = S2P_SPT
            current_values['S3V_SPT'] = S3V_SPT
            current_values['S3A_SPT'] = S3A_SPT
            current_values['S3P_SPT'] = S3P_SPT
            current_values['S4V_SPT'] = S4V_SPT
            current_values['S4A_SPT'] = S4A_SPT
            current_values['S4P_SPT'] = S4P_SPT

            # Update GUI elements
            window['S1V_SPT_display'].update(current_values['S1V_SPT'])
            window['S1A_SPT_display'].update(current_values['S1A_SPT'])
            window['S1P_SPT_display'].update(current_values['S1P_SPT'])
            window['S2V_SPT_display'].update(current_values['S2V_SPT'])
            window['S2A_SPT_display'].update(current_values['S2A_SPT'])
            window['S2P_SPT_display'].update(current_values['S2P_SPT'])
            window['S3V_SPT_display'].update(current_values['S3V_SPT'])
            window['S3A_SPT_display'].update(current_values['S3A_SPT'])
            window['S3P_SPT_display'].update(current_values['S3P_SPT'])
            window['S4V_SPT_display'].update(current_values['S4V_SPT'])
            window['S4A_SPT_display'].update(current_values['S4A_SPT'])
            window['S4P_SPT_display'].update(current_values['S4P_SPT']) # Add debug print  
            return True
        except ValueError:
            print("Debug 21 - Invalid setpoint values received")
            return False

    elif expected == "STATE_ENGINE_STEP:":
        state_engine_step = int(parts[0])
        window['state_engine_step_display'].update(state_engine_step)
        print(f"Debug 22 - Updated state_engine_step: {state_engine_step}")  # Add debug print
        print("Debug 23 - Returning True for STATE_ENGINE_STEP:")  # Add debug print
        return True
            
    print("Debug 24 - Returning False")  # Add debug print
    return False

def handle_servo_buttons(event, enable_command, disable_command, enabled, window):
    """Handle servo button events and state changes."""
    print(f"Debug - Handling event: {event}, enabled: {enabled}")  # Add debug print
    
    if event == 'Mode':  # Mode is either Manual or Auto
        if enabled:
            print(f"Debug - Sending disable command for Mode: MANUAL")  # Add debug print
            serialInst.write(f"CMD:Mode MANUAL\n".encode('utf-8'))
            window[event].update(text='Auto', button_color=('white', 'green'))
            GUI_button_states[event] = False
        else:
            print(f"Debug - Sending enable command for Mode: AUTO")  # Add debug print
            serialInst.write(f"CMD:Mode AUTO\n".encode('utf-8'))
            window[event].update(text='Manual', button_color=('black', 'yellow'))
            GUI_button_states[event] = True
    
    elif event.endswith('B1'):  # B1 is either ENABLE or DISABLE
        if enabled:
            print(f"Debug - Sending disable command for {event}: DISABLE")  # Add debug print
            serialInst.write(f"CMD:{event} DISABLE\n".encode('utf-8'))
            window[event].update(text='ENABLE', button_color=('white', 'green'))
            GUI_button_states[event] = False
        else:
            print(f"Debug - Sending enable command for {event}: ENABLE")  # Add debug print
            serialInst.write(f"CMD:{event} ENABLE\n".encode('utf-8'))
            window[event].update(text='DISABLE', button_color=('white', 'red'))
            GUI_button_states[event] = True
    
    elif event.endswith('B2'):  # B2 is either Run or Stop
        if enabled:
            print(f"Debug - Sending disable command for {event}: STOP")  # Add debug print
            serialInst.write(f"CMD:{event} STOP\n".encode('utf-8'))
            window[event].update(text='RUN', button_color=('white', 'green'))
            GUI_button_states[event] = False
        else:
            print(f"Debug - Sending enable command for {event}: START")  # Add debug print
            serialInst.write(f"CMD:{event} START\n".encode('utf-8'))
            window[event].update(text='STOP', button_color=('white', 'red'))
            GUI_button_states[event] = True
    
    elif event.endswith('B3'):
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
    
    serialInst.flush()
    return not enabled

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


# GUI_button_states is already populated by initialize_from_arduino()

# Before creating the window, modify the layout initialization to explicitly set button colors
layout = [
    [sg.Text('State Engine Step:', size=(15, 1), justification='right', font=('Helvetica', 12, 'bold')), sg.Text('0', size=(3, 1), key='state_engine_step_display', font=('Helvetica', 12, 'bold'))],
    [sg.Text(' ', size=(33, 1)), sg.Text('Velocity', size=(7, 1)), sg.Text('Acceleration', size=(9, 1)), sg.Text('Position', size=(6, 1))],
    [sg.Text(' ', size=(8, 1)), sg.Button('Auto' if GUI_button_states['Mode'] else 'Manual',key='Mode', button_color=('black', 'green') if GUI_button_states['Mode'] else ('black', 'yellow')),
     sg.Text(' ', size=(11, 1)), sg.Text('(0-5000)', size=(9, 1)),
     sg.Text('(0-5000)', size=(8, 1)), 
     sg.Text('(0-6000)', size=(12, 1)), sg.Text('', size=(8, 1))],

    # Servo 1 Row
    [sg.Text('Servo 1', size=(8, 1)), 
     sg.Button('DISABLE' if GUI_button_states['S1B1'] else 'ENABLE', 
              key='S1B1', 
              button_color=('white', 'red') if GUI_button_states['S1B1'] else ('white', 'green')),
     sg.Button('STOP' if GUI_button_states['S1B2'] else 'RUN',
              key='S1B2',
              button_color=('white', 'red') if GUI_button_states['S1B2'] else ('white', 'green')),
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
     sg.Text(arduino_values['S1P'], size=(7, 1), key='S1P_display', justification='right')], #Adjusted size
    
    # Servo 2 Row
    [sg.Text('Servo 2', size=(8, 1)), 
    sg.Button('DISABLE' if GUI_button_states['S2B1'] else 'ENABLE', 
            key='S2B1', 
            button_color=('white', 'red') if GUI_button_states['S2B1'] else ('white', 'green')),
    sg.Button('STOP' if GUI_button_states['S2B2'] else 'RUN',
            key='S2B2',
            button_color=('white', 'red') if GUI_button_states['S2B2'] else ('white', 'green')),
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
    sg.Text(arduino_values['S2P'], size=(7, 1), key='S2P_display', justification='right')],  # Adjusted size

    # Servo 3 Row
    [sg.Text('Servo 3', size=(8, 1)), 
    sg.Button('DISABLE' if GUI_button_states['S3B1'] else 'ENABLE', 
            key='S3B1', 
            button_color=('white', 'red') if GUI_button_states['S3B1'] else ('white', 'green')),
    sg.Button('STOP' if GUI_button_states['S3B2'] else 'RUN',
            key='S3B2',
            button_color=('white', 'red') if GUI_button_states['S3B2'] else ('white', 'green')),
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
    sg.Text(arduino_values['S3P'], size=(7, 1), key='S3P_display', justification='right')],  # Adjusted size

    # Servo 4 Row
    [sg.Text('Servo 4', size=(8, 1)), 
    sg.Button('DISABLE' if GUI_button_states['S4B1'] else 'ENABLE', 
            key='S4B1', 
            button_color=('white', 'red') if GUI_button_states['S4B1'] else ('white', 'green')),
    sg.Button('STOP' if GUI_button_states['S4B2'] else 'RUN',
            key='S4B2',
            button_color=('white', 'red') if GUI_button_states['S4B2'] else ('white', 'green')),
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
    sg.Text(arduino_values['S4P'], size=(7, 1), key='S4P_display', justification='right')]  # Adjusted size
    ]


window = sg.Window("Servo Control", 
            layout, default_element_size=(8, 5), 
            size=(700, 500), 
            auto_size_text=False, 
            auto_size_buttons=False, 
            finalize=True)


last_request_time = time.time()
last_gui_update = time.time()
last_event_time = {}  # Track the last time each event was processed

# Event Loop
updates = []

while True:
    try:
        event, values = window.read(timeout=WINDOW_READ_TIMEOUT)
        if event in (sg.WIN_CLOSED, 'Exit'):
            print("Debug 34 - Window closed or Exit event triggered")
            break

        # High Priority - Button Events
        if event and isinstance(event, str):
            current_time = time.time()
            if event != '__TIMEOUT__':
                print(f"Debug - Event: {event}")

                   # High Priority - Button Events
        if event and isinstance(event, str):
            current_time = time.time()
            if event != '__TIMEOUT__':
                print(f"Debug - Event: {event}")

            # Debounce mechanism
            if event not in last_event_time or (current_time - last_event_time[event] > DEBOUNCE_INTERVAL):
                last_event_time[event] = current_time
                match event:
                    case 'Mode':
                        GUI_button_states[event] = not GUI_button_states[event]
                        CNT_button_states[event] = handle_servo_buttons(event, "Mode AUTO", "Mode MANUAL", CNT_button_states[event], window)
                        window[event].update(text='Auto' if GUI_button_states[event] else 'Manual', button_color=('white', 'green') if GUI_button_states[event] else ('black', 'yellow'))
                        window.refresh()
                        print(f"Debug - Sending command: {'Manual Mode' if GUI_button_states[event] else 'Auto'}")
                    case 'S1B1' | 'S2B1' | 'S3B1' | 'S4B1':
                        servo = int(event[1])
                        GUI_button_states[event] = not GUI_button_states[event]
                        CNT_button_states[event] = handle_servo_buttons(event, "ENABLE", "DISABLE", CNT_button_states[event], window)
                        window[event].update(text='DISABLE' if GUI_button_states[event] else 'ENABLE', button_color=('white', 'red') if GUI_button_states[event] else ('white', 'green'))
                        window.refresh()
                    case 'S1B2' | 'S2B2' | 'S3B2' | 'S4B2':
                        servo = int(event[1])
                        GUI_button_states[event] = not GUI_button_states[event]
                        CNT_button_states[event] = handle_servo_buttons(event, "RUN", "STOP", CNT_button_states[event], window)
                        window[event].update(text='STOP' if GUI_button_states[event] else 'RUN', button_color=('white', 'red') if GUI_button_states[event] else ('white', 'green'))
                        window.refresh()
                    case _ if event.endswith('B3'): # Handle Setpoint Update                                
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
            print("Debug 99 - Sending CMD:REQUEST_VALUES to Arduino")  # Add debug print
            serialInst.write("CMD:REQUEST_VALUES\n".encode('utf-8'))
            serialInst.flush()
            last_request_time = current_time
       
            # Low Priority - Batch Update Display
        current_time = time.time()
        if current_time - last_gui_update > GUI_UPDATE_INTERVAL:
            updates = []
            try:
                for _ in range(BATCH_SIZE):
                    message = message_queue.get_nowait()
                    if DEBUG:
                        print(f"Debug - Processing message: {message}")
                    if message.startswith("VALUES:"):
                        process_response(message, "VALUES:", window)
                    elif message.startswith("STATE_ENGINE_STEP:"):
                        process_response(message, "STATE_ENGINE_STEP:", window)
                    elif message.startswith("SETPOINTS:"):
                        process_response(message, "SETPOINTS:", window)
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
                        
            last_gui_update = current_time

    except Exception as e:
        print(f"Debug - Unexpected error in event loop: {str(e)}")
        break

# Cleanup
serial_thread.stop()
serial_thread.join()
serialInst.close()
window.close()

