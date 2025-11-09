import PySimpleGUI as sg # type: ignore
import serial # type: ignore
import threading
import queue
import time
import sys

# Global state
state_engine_step = 0
DEBUG = False  # Global debug flag to control debug output
DEBUG00 = False  # Global debug flag to control debug output
DEBUG_LOW_PRIORITY = False  # Global debug flag to control debug output
DEBUG_MEDIUM_PRIORITY = False  # Global debug flag to control debug output
DEBUG_HIGH_PRIORITY = False  # Global debug flag to control debug output

# Constants
WINDOW_READ_TIMEOUT = 100  # Window read timeout in milliseconds
MEDIUM_PRIORITY_UPDATE_INTERVAL = .25  # Reduced Arduino polling (sec)
LOW_PRIORITY_UPDATE_INTERVAL = .5  # Faster display updates (sec)
BATCH_SIZE = 10
DEBOUNCE_INTERVAL = 0.5  # Debounce interval in seconds


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

# Setpoints INITIAL VALUES
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

# Button States
Mode = 0  # Mode
Repeat = 0  # Repeat
Start = 0  # Start
S1B1 = False  # Servo1 Button 1
S1B2 = False  # Servo1 Button 2
S2B1 = False  # Servo2 Button 1 
S2B2 = False  # Servo2 Button 2
S3B1 = False  # Servo3 Button 1
S3B2 = False  # Servo3 Button 2
S4B1 = False  # Servo4 Button 1
S4B2 = False  # Servo4 Button 2

# Values Dictionary
# The code snippet initializes a dictionary named arduino_values with keys representing different 
# parameters (velocity, acceleration, and position) for four servos (S1, S2, S3, and S4). Each 
# key is associated with an initial value of '0'.
arduino_values ={  
    'S1V': '0', 'S1A': '0', 'S1P': '0',
    'S2V': '0', 'S2A': '0', 'S2P': '0',
    'S3V': '0', 'S3A': '0', 'S3P': '0',
    'S4V': '0', 'S4A': '0', 'S4P': '0'
}

# Setpoint Dictionary
setpoint_values = { 
    'Mode' : Mode,
    'Repeat' : Repeat,
    'Start' : Start,
    'S1V_SPT': S1V_SPT, 
    'S1A_SPT': S1A_SPT, 
    'S1P_SPT': S1P_SPT,
    'S2V_SPT': S2V_SPT, 
    'S2A_SPT': S2A_SPT, 
    'S2P_SPT': S2P_SPT,
    'S3V_SPT': S3V_SPT, 
    'S3A_SPT': S3A_SPT, 
    'S3P_SPT': S3P_SPT,
    'S4V_SPT': S4V_SPT, 
    'S4A_SPT': S4A_SPT, 
    'S4P_SPT': S4P_SPT
}
# Button states dictionary
# The code snippet initializes a dictionary named named GUI_button_states with keys representing 
# the states of buttons for four servos (S1, S2, S3, and S4). Each servo has two buttons (B1 and B2). 
# The initial state of each button # is set to False, indicating that the buttons are not pressed or enabled.
GUI_button_states = {
    'Mode': False,  # False for MANUAL, True for AUTO
    'Repeat': False,  # False for DISABLED, True for ENABLED
    'Start': False,  # False for DISABLED, True for ENABLED
    'S1B1': False, 'S1B2': False,
    'S2B1': False, 'S2B2': False,
    'S3B1': False, 'S3B2': False,
    'S4B1': False, 'S4B2': False
}
CNT_button_states = GUI_button_states.copy()  # Initialize CNT_button_states as a copy of button_states



values_received = False
states_received = False  
setpoints_received = False

#SerialThread(threading.Thread): defines a new class 
# named SerialThread that inherits from threading.Thread. 
# This setup allows the SerialThread class to create and manage
# a separate thread of execution, which is useful for performing tasks concurrently, 
# such as handling serial communication without blocking the main program.
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
                        if DEBUG00:
                            print(f"Debug 0 - Serial message received: {line}")
                else:
                    time.sleep(0.01)  # Prevent CPU hogging
            except Exception as e:
                if DEBUG00:
                    print(f"Debug 1 - Serial error: {e}")
                self.running = False

    def stop(self):
        """Stop thread execution."""
        self.running = False

#initialize_serial_connection that sets up a serial connection. 
# The function takes three parameters: port (required), baudrate (optional, with a default value of 9600), 
# and timeout (optional, with a default value of 1 second). 
# This function is likely used to configure and establish a serial communication link with a specified device.
def initialize_serial_connection(port, baudrate=9600, timeout=1):
    """Initialize serial connection with error handling."""
    try:
        print(f"Debug 2 - Opening {port}")
        serial_inst = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
        serial_inst.reset_input_buffer()
        print("Debug 3 - Serial port opened")
        return serial_inst
    except Exception as e:
        print(f"Debug 4 - Serial port error: {e}")
        raise


# Initialize components
#initializes a serial connection on port 'COM10', creates a message queue, 
# and starts a separate thread to handle serial communication. The SerialThread 
# reads data from the serial port and places it into the message queue, allowing 
# the main program to process the data concurrently without blocking.
serialInst = initialize_serial_connection('COM6')
message_queue = queue.Queue()
serial_thread = SerialThread(serialInst, message_queue)
serial_thread.start()

# Define window read timeout
WINDOW_READ_TIMEOUT = 100  # Set to an appropriate value in milliseconds

#The function initialize_from_arduino(window) is designed to initialize 
# all values from an Arduino device. It communicates with the Arduino to 
# request and receive various data, such as current values, button states, 
# and setpoints. The function ensures that the GUI is synchronized with the 
# Arduino's state.

def clear_buffers(serialInst, message_queue):
    """Clear the input and output buffers of the serial instance and the message queue."""
    serialInst.reset_input_buffer()
    serialInst.reset_output_buffer()
    while not message_queue.empty():
        message_queue.get()

def initialize_buttons(window):
    """Initialize button states from Arduino."""
    global states_received, CNT_button_states, GUI_button_states
    MAX_RETRIES = 3
    TIMEOUT = 5
    
    for attempt in range(MAX_RETRIES):
        print(f"Debug 5a - Starting Arduino button states initialization (attempt {attempt + 1}/{MAX_RETRIES})")
        
        # Reset state
        states_received = False
        
        # Clear buffers
        clear_buffers(serialInst, message_queue)
            
        # Request button states
        request = "CMD:REQUEST_BUTTON_STATES\n"
        expected = "BUTTON_STATES:"
        print(f"Debug 6a - Sending: {request.strip()}")
        serialInst.write(request.encode('utf-8'))
        serialInst.flush()
        time.sleep(.5)
        
        # Wait for response
        timeout = time.time() + TIMEOUT
        while time.time() < timeout:
            try:
                message = message_queue.get(timeout=0.5)
                print(f"Debug 7a - Received: {message}")
                
                if message.startswith(expected):
                    if process_button_states_response(message, window):
                        print(f"Debug 8a - Valid {expected} received")
                        CNT_button_states = GUI_button_states.copy()  # Sync CNT_button_states with GUI_button_states
                        print(f"Debug 9a - Servo states initialized to: {CNT_button_states}")
                        return True
            except queue.Empty:
                continue
        else:
            print(f"Debug 10a - Timeout waiting for {expected}")
        
        time.sleep(2)
    
    # print("Failed to initialize button states from Arduino.")
    return False

def initialize_values(window):
    """Initialize values from Arduino."""
    global values_received, setpoint_values, arduino_values
    MAX_RETRIES = 3
    TIMEOUT = 5
    
    for attempt in range(MAX_RETRIES):
        # print(f"Debug 5b - Starting Arduino values initialization (attempt {attempt + 1}/{MAX_RETRIES})")
        
        # Reset state
        values_received = False
        
        # Clear buffers
        clear_buffers(serialInst, message_queue)
            
        # Request values
        request = "CMD:REQUEST_VALUES\n"
        expected = "VALUES:"
        # print(f"Debug 6 - Sending: {request.strip()} (attempt {attempt + 1}/{MAX_RETRIES})")
        serialInst.write(request.encode('utf-8'))
        serialInst.flush()
        time.sleep(0.5)
        
        # Wait for response
        timeout = time.time() + TIMEOUT
        while time.time() < timeout:
            try:
                message = message_queue.get(timeout=0.5)
                # print(f"Debug 7b - Received: {message}")
                
                if message.startswith(expected):
                    if process_values_response(message, window):
                        # print(f"Debug 8b - Valid {expected} received")
                        # Update setpoint_values dictionary
                        setpoint_values.update({
                            'S1V': arduino_values['S1V'],
                            'S1A': arduino_values['S1A'],
                            'S1P': arduino_values['S1P'],
                            'S2V': arduino_values['S2V'],
                            'S2A': arduino_values['S2A'],
                            'S2P': arduino_values['S2P'],
                            'S3V': arduino_values['S3V'],
                            'S3A': arduino_values['S3A'],
                            'S3P': arduino_values['S3P'],
                            'S4V': arduino_values['S4V'],
                            'S4A': arduino_values['S4A'],
                            'S4P': arduino_values['S4P']
                        })
                        return True
            except queue.Empty:
                continue
        else:
            # print(f"Debug 9b - Timeout waiting for {expected}")
        
            time.sleep(2)
    
    # print("Failed to initialize values from Arduino.")
    return False

def initialize_setpoints(window):
    """Initialize setpoints from Arduino."""
    global setpoints_received, setpoint_values
    MAX_RETRIES = 3
    TIMEOUT = 5
    
    for attempt in range(MAX_RETRIES):
        # print(f"Debug 5c - Starting Arduino setpoints initialization (attempt {attempt + 1}/{MAX_RETRIES})")
        
        # Reset state
        setpoints_received = False
        
        # Clear buffers
        clear_buffers(serialInst, message_queue)
            
        # Request setpoints
        request = "CMD:REQUEST_SETPOINTS\n"
        expected = "SETPOINTS:"
        # print(f"Debug 6c - Sending: {request.strip()}")
        serialInst.write(request.encode('utf-8'))
        serialInst.flush()
        time.sleep(0.5)
        
        # Wait for response
        timeout = time.time() + TIMEOUT
        while time.time() < timeout:
            try:
                message = message_queue.get(timeout=0.5)
                # print(f"Debug 7c - Received: {message}")
                
                if message.startswith(expected):
                    if process_setpoints_response(message, window):
                        # print(f"Debug 8c - Valid {expected} received")
                        # Add setpoints to setpoint_values
                        setpoint_values.update({
                            'S1V_SPT': S1V_SPT, 'S1A_SPT': S1A_SPT, 'S1P_SPT': S1P_SPT,
                            'S2V_SPT': S2V_SPT, 'S2A_SPT': S2A_SPT, 'S2P_SPT': S2P_SPT,
                            'S3V_SPT': S3V_SPT, 'S3A_SPT': S3A_SPT, 'S3P_SPT': S3P_SPT,
                            'S4V_SPT': S4V_SPT, 'S4A_SPT': S4A_SPT, 'S4P_SPT': S4P_SPT
                        })
                        return True
            except queue.Empty:
                continue
        else:
            print(f"Debug 9c - Timeout waiting for {expected}")
        
        time.sleep(2)
    
    # print("Failed to initialize setpoints from Arduino.")
    return False

def initialize_state_engine(window):
    """Initialize state engine from Arduino."""
    global state_engine_step
    MAX_RETRIES = 3
    TIMEOUT = 5
    
    for attempt in range(MAX_RETRIES):
        # print(f"Debug 5d - Starting Arduino state engine initialization (attempt {attempt + 1}/{MAX_RETRIES})")
        
        # Reset state
        state_engine_step = None
        
        # Clear buffers
        clear_buffers(serialInst, message_queue)
            
        # Request state engine step
        request = "CMD:REQUEST_STATE_ENGINE\n"
        expected = "STATE_ENGINE:"
        # print(f"Debug 6d - Sending: {request.strip()}")
        serialInst.write(request.encode('utf-8'))
        serialInst.flush()
        time.sleep(0.5)
        
        # Wait for response
        timeout = time.time() + TIMEOUT
        while time.time() < timeout:
            try:
                message = message_queue.get(timeout=0.5)
                # print(f"Debug 7d - Received: {message}")
                
                if message.startswith(expected):
                    if process_state_engine_response(message, window):
                        # print(f"Debug 8d - Valid {expected} received")
                        return True
            except queue.Empty:
                continue
        else:
            # print(f"Debug 9d - Timeout waiting for {expected}")
        
            time.sleep(2)
    
    print("Failed to initialize state engine from Arduino.")
    return False

def initialize_from_arduino(window):
    """Initialize all values from Arduino."""
    if not initialize_values(window):
        return False
    
    if not initialize_buttons(window):
        return False
    
    if not initialize_setpoints(window):
        return False
    
    if not initialize_state_engine(window):
        return False

    # print("Debug 11 - Initialization successful")
    return True


    #The function process_response(message, expected, window) is designed
    #to process and validate responses received from the Arduino. It updates 
    # the global state and GUI elements based on the type of response received.
def process_values_response(message, window):
    """Process and validate Arduino values response."""
    global values_received, arduino_values
    
    # print(f"Debug 15 - Processing values message: {message}")
    parts = message.split(":")[1].split(",")
    
    if len(parts) >= 12:
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
        # print(f"Debug 16 - Updated arduino_values: {arduino_values}")
        
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
        return True
    return False

def process_button_states_response(message, window):
    """Process and validate Arduino button states response."""
    global states_received, GUI_button_states, CNT_button_states
    
    # print(f"Debug 17 - Processing button states message: {message}")
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

         # Sync CNT_button_states with GUI_button_states
        CNT_button_states = GUI_button_states.copy()
        
        # print(f"Debug 18 - Servo button states updated")
        states_received = True
        
        # Update the GUI with the new button states
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
        
        window.refresh()  # Refresh the GUI
        return True
    return False



def process_setpoints_response(message, window):
    """Process and validate Arduino setpoints response."""
    global setpoints_received, setpoint_values
    global S1V_SPT, S1A_SPT, S1P_SPT, S2V_SPT, S2A_SPT, S2P_SPT
    global S3V_SPT, S3A_SPT, S3P_SPT, S4V_SPT, S4A_SPT, S4P_SPT
    
    # print(f"Debug 19 - Processing setpoints message: {message}")
    parts = message.split(":")[1].split(",")
    
    if len(parts) >= 12:
        try:
            S1V_SPT, S1A_SPT, S1P_SPT = map(int, parts[0:3])
            S2V_SPT, S2A_SPT, S2P_SPT = map(int, parts[3:6])
            S3V_SPT, S3A_SPT, S3P_SPT = map(int, parts[6:9])
            S4V_SPT, S4A_SPT, S4P_SPT = map(int, parts[9:12])
            setpoints_received = True

            # Debug prints
            # print(f"Debug 19 - Updated setpoints: S1V_SPT={S1V_SPT}, S2V_SPT={S2V_SPT}, S3V_SPT={S3V_SPT}, S4V_SPT={S4V_SPT}")
            # print(f"Debug 19a - Updating setpoints in GUI")

            # Update setpoint_values dictionary
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

            # Update the GUI with the new setpoints
            window['S1V_SPT_display'].update(S1V_SPT)
            window['S1A_SPT_display'].update(S1A_SPT)
            window['S1P_SPT_display'].update(S1P_SPT)
            window['S2V_SPT_display'].update(S2V_SPT)
            window['S2A_SPT_display'].update(S2A_SPT)
            window['S2P_SPT_display'].update(S2P_SPT)
            window['S3V_SPT_display'].update(S3V_SPT)
            window['S3A_SPT_display'].update(S3A_SPT)
            window['S3P_SPT_display'].update(S3P_SPT)
            window['S4V_SPT_display'].update(S4V_SPT)
            window['S4A_SPT_display'].update(S4A_SPT)
            window['S4P_SPT_display'].update(S4P_SPT)
            
            window.refresh()  # Refresh the GUI
            return True
        except ValueError:
           print("Error processing setpoints response")
    return False

def process_state_engine_response(message, window):
    """Process and validate Arduino state engine response."""
    global state_engine_step
    
    # print(f"Debug 20 - Processing state engine message: {message}")
    parts = message.split(":")[1].split(",")
    
    if len(parts) >= 1:
        state_engine_step = int(parts[0])
        # print(f"Debug 21 - Updated state engine step: {state_engine_step}")
        
        # Update the GUI with the new state engine step
        window['state_engine_step'].update(state_engine_step)
        window.refresh()  # Refresh the GUI
        return True
    return False


def process_response(message, expected, window):
    """Process and validate Arduino responses."""
    if expected == "VALUES:":
        return process_values_response(message, window)
    elif expected == "BUTTON_STATES:":
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
            serialInst.write(f"CMD:Mode MANUAL\n".encode('utf-8'))
            window[event].update(text='Auto', button_color=('white', 'green'))
            GUI_button_states[event] = False
        else:
            # print(f"Debugs 27 - Sending enable command for Mode: AUTO")   
            serialInst.write(f"CMD:Mode AUTO\n".encode('utf-8'))
            window[event].update(text='Manual', button_color=('black', 'yellow'))
            GUI_button_states[event] = True

    elif event == 'Repeat':  # Repeat is either enabled or disabled
        if enabled:
            # print(f"Debugs 28 - Sending disable command for Repeat: DISABLE")   
            serialInst.write(f"CMD:Repeat DISABLE\n".encode('utf-8'))
            window[event].update(text='Repeat', button_color=('white', 'green'))
            GUI_button_states[event] = False
        else:
            # print(f"Debugs 29 - Sending enable command for Repeat: ENABLE")   
            serialInst.write(f"CMD:Repeat ENABLE\n".encode('utf-8'))
            window[event].update(text='Single', button_color=('black', 'yellow'))
            GUI_button_states[event] = True

    elif event == 'Start':  # Start is either enabled or disabled
        if enabled:
            # print(f"Debugs 30 - Sending disable command for Start: DISABLE")   
            serialInst.write(f"CMD:Start DISABLE\n".encode('utf-8'))
            window[event].update(text='Disable Start', button_color=('white', 'green'))
            GUI_button_states[event] = False
        else:
            # print(f"Debugs 31 - Sending enable command for Start: ENABLE")   
            serialInst.write(f"CMD:Start ENABLE\n".encode('utf-8'))
            window[event].update(text='Enable Start', button_color=('black', 'yellow'))
            GUI_button_states[event] = True
    
    elif event.endswith('B1'):  # B1 is either ENABLE or DISABLE
        if enabled:
            # print(f"Debugs 32 - Sending disable command for {event}: DISABLE")   
            serialInst.write(f"CMD:{event} DISABLE\n".encode('utf-8'))
            window[event].update(text='ENabled', button_color=('white', 'green'))
            GUI_button_states[event] = False
        else:
            # print(f"Debugs 33 - Sending enable command for {event}: ENABLE")   
            serialInst.write(f"CMD:{event} ENABLE\n".encode('utf-8'))
            window[event].update(text='DISabled', button_color=('black', 'yellow'))
            GUI_button_states[event] = True
    
    elif event.endswith('B2'):  # B2 is either Run or Stop
        if enabled:
            # print(f"Debugs 34 - Sending disable command for {event}: STOP")   
            serialInst.write(f"CMD:{event} STOP\n".encode('utf-8'))
            window[event].update(text='Spare', button_color=('black', 'gray'))
            GUI_button_states[event] = False
        else:
            # print(f"Debugs 35 - Sending enable command for {event}: Start")   
            serialInst.write(f"CMD:{event} Start\n".encode('utf-8'))
            window[event].update(text='Spare', button_color=('white', 'gray'))
            GUI_button_states[event] = True
    
    elif event.endswith('B3'):
        servo = int(event[1])
        V_data = validate_input(f'S{servo}V_SPT', values, 0, 20000)
        A_data = validate_input(f'S{servo}A_SPT', values, 0, 20000)
        P_data = validate_input(f'S{servo}P_SPT', values, 0, 20000)
        if all(x is not None for x in (V_data, A_data, P_data)):
            cmd = f"CMD:S{servo}_Parameters:{V_data},{A_data},{P_data}\n"
            # print(f"Debugs 36 - Sending command: {cmd.strip()}")   
            serialInst.write(cmd.encode('utf-8'))
            serialInst.flush()
            # Update setpoint_values and corresponding sg.Text elements
            setpoint_values[f'S{servo}V_SPT'] = V_data
            setpoint_values[f'S{servo}A_SPT'] = A_data
            setpoint_values[f'S{servo}P_SPT'] = P_data
            window[f'S{servo}V_SPT_display'].update(V_data)
            window[f'S{servo}A_SPT_display'].update(A_data)
            window[f'S{servo}P_SPT_display'].update(P_data)
            window.refresh()
            # print(f"Debugs 37 - Updated setpoints for S{servo}: V_SPT={V_data}, A_SPT={A_data}, P_SPT={P_data}")   
    
    serialInst.flush()
    return not enabled


def validate_input(key, values, min_val, max_val):
    """Validate numeric input values."""
    try:
        value = int(values[key])
        if min_val <= value <= max_val:
            return value
        # print(f"Value out of range for {key}: {value}")
    except ValueError:
        print(f"Invalid value for {key}")
    return None




# Before creating the window, modify the layout initialization to explicitly set button colors
layout = [
    [sg.Text('State Engine Step:', size=(15, 1), justification='right', font=('Helvetica', 12, 'bold')), sg.Text('0', size=(3, 1), key='state_engine_step', font=('Helvetica', 12, 'bold'))],
    [sg.Text(' ', size=(33, 1)), sg.Text('Velocity', size=(6, 1)), sg.Text('Acceleration', size=(9, 1)), sg.Text('Position', size=(6, 1))],
    [sg.Text(' ', size=(8, 1)), 
     sg.Button('Auto' if GUI_button_states['Mode'] else 'Manual', key='Mode', button_color=('white', 'green') if GUI_button_states['Mode'] else ('black', 'yellow')),
     sg.Button('Step Enabled' if GUI_button_states['Start'] else 'Step Disabled', key='Start', button_color=('white', 'green') if GUI_button_states['Start'] else ('black', 'yellow')),
     sg.Text('(0-5000)', size=(8, 1)),
     sg.Text('(0-5000)', size=(7, 1)), 
     sg.Text('(0-6000)', size=(6, 1)), 
     sg.Button('Repeat' if GUI_button_states['Repeat'] else 'Single', key='Repeat', button_color=('white', 'green') if GUI_button_states['Repeat'] else ('black', 'yellow'))],

    # Servo 1 Row
    [sg.Text('Servo 1', size=(8, 1)), 
     sg.Button('Enabled' if GUI_button_states['S1B1'] else 'Disabled', 
              key='S1B1', 
              button_color=('white', 'green') if GUI_button_states['S1B1'] else ('black', 'yellow')),
     sg.Button('Run' if GUI_button_states['S1B2'] else 'Stop',
            key='S1B2',
            button_color=('white', 'green') if GUI_button_states['S2B2'] else ('black', 'yellow')),
     sg.InputText(setpoint_values['S1V_SPT'], key='S1V_SPT', size=(8, 1), justification='right'),
     sg.InputText(setpoint_values['S1A_SPT'], key='S1A_SPT', size=(8, 1), justification='right'),
     sg.InputText(setpoint_values['S1P_SPT'], key='S1P_SPT', size=(8, 1), justification='right'),
     sg.Button('OK', key='S1B3')],
    [sg.Text(' ', size=(17, 1)), sg.Text('Setpoint', size=(14, 1), justification='right'),  # Adjusted size
     sg.Text(setpoint_values['S1V_SPT'], size=(7, 1), key='S1V_SPT_display', justification='right'),
     sg.Text(setpoint_values['S1A_SPT'], size=(7, 1), key='S1A_SPT_display', justification='right'),
     sg.Text(setpoint_values['S1P_SPT'], size=(7, 1), key='S1P_SPT_display', justification='right')],
    [sg.Text(' ', size=(17, 1)), sg.Text('Current Value', size=(14, 1), justification='right'),  # Adjusted size
     sg.Text(arduino_values['S1V'], size=(7, 1), key='S1V_display', justification='right'),
     sg.Text(arduino_values['S1A'], size=(7, 1), key='S1A_display', justification='right'),
     sg.Text(arduino_values['S1P'], size=(7, 1), key='S1P_display', justification='right')], #Adjusted size
    
    # Servo 2 Row
    [sg.Text('Servo 2', size=(8, 1)), 
    sg.Button('Enabled' if GUI_button_states['S2B1'] else 'Disabled', 
            key='S2B1', 
            button_color=('white', 'green') if GUI_button_states['S2B1'] else ('black', 'yellow')),
    sg.Button('Run' if GUI_button_states['S2B2'] else 'Stop',
            key='S2B2',
            button_color=('white', 'green') if GUI_button_states['S2B2'] else ('black', 'yellow')),
    sg.InputText(setpoint_values['S2V_SPT'], key='S2V_SPT', size=(8, 1), justification='right'),
    sg.InputText(setpoint_values['S2A_SPT'], key='S2A_SPT', size=(8, 1), justification='right'),
    sg.InputText(setpoint_values['S2P_SPT'], key='S2P_SPT', size=(8, 1), justification='right'),
    sg.Button('OK', key='S2B3')],
    [sg.Text(' ', size=(17, 1)), sg.Text('Setpoint', size=(14, 1), justification='right'),  # Adjusted size
    sg.Text(setpoint_values['S2V_SPT'], size=(7, 1), key='S2V_SPT_display', justification='right'),
    sg.Text(setpoint_values['S2A_SPT'], size=(7, 1), key='S2A_SPT_display', justification='right'),
    sg.Text(setpoint_values['S2P_SPT'], size=(7, 1), key='S2P_SPT_display', justification='right')],
    [sg.Text(' ', size=(17, 1)), sg.Text('Current Value', size=(14, 1), justification='right'),  # Adjusted size
    sg.Text(arduino_values['S2V'], size=(7, 1), key='S2V_display', justification='right'),
    sg.Text(arduino_values['S2A'], size=(7, 1), key='S2A_display', justification='right'),
    sg.Text(arduino_values['S2P'], size=(7, 1), key='S2P_display', justification='right')],  # Adjusted size

    # Servo 3 Row
    [sg.Text('Servo 3', size=(8, 1)), 
    sg.Button('Enabled' if GUI_button_states['S3B1'] else 'Disabled', 
            key='S3B1', 
            button_color=('white', 'green') if GUI_button_states['S3B1'] else ('black', 'yellow')),
    sg.Button('Run' if GUI_button_states['S3B2'] else 'Stop',
            key='S3B2',
            button_color=('white', 'green') if GUI_button_states['S3B2'] else ('black', 'yellow')),
    sg.InputText(setpoint_values['S3V_SPT'], key='S3V_SPT', size=(8, 1), justification='right'),
    sg.InputText(setpoint_values['S3A_SPT'], key='S3A_SPT', size=(8, 1), justification='right'),
    sg.InputText(setpoint_values['S3P_SPT'], key='S3P_SPT', size=(8, 1), justification='right'),
    sg.Button('OK', key='S3B3')],
    [sg.Text(' ', size=(17, 1)), sg.Text('Setpoint', size=(14, 1), justification='right'),  # Adjusted size
    sg.Text(setpoint_values['S3V_SPT'], size=(7, 1), key='S3V_SPT_display', justification='right'),
    sg.Text(setpoint_values['S3A_SPT'], size=(7, 1), key='S3A_SPT_display', justification='right'),
    sg.Text(setpoint_values['S3P_SPT'], size=(7, 1), key='S3P_SPT_display', justification='right')],
    [sg.Text(' ', size=(17, 1)), sg.Text('Current Value', size=(14, 1), justification='right'),  # Adjusted size
    sg.Text(arduino_values['S3V'], size=(7, 1), key='S3V_display', justification='right'),
    sg.Text(arduino_values['S3A'], size=(7, 1), key='S3A_display', justification='right'),
    sg.Text(arduino_values['S3P'], size=(7, 1), key='S3P_display', justification='right')],  # Adjusted size

    # Servo 4 Row
    [sg.Text('Servo 4', size=(8, 1)), 
    sg.Button('Enabled' if GUI_button_states['S4B1'] else 'Disabled', 
            key='S4B1', 
            button_color=('white', 'green') if GUI_button_states['S4B1'] else ('black', 'yellow')),
    sg.Button('Run' if GUI_button_states['S4B2'] else 'Stop',
            key='S4B2',
            button_color=('white', 'green') if GUI_button_states['S4B2'] else ('black', 'yellow')),
    sg.InputText(setpoint_values['S4V_SPT'], key='S4V_SPT', size=(8, 1), justification='right'),
    sg.InputText(setpoint_values['S4A_SPT'], key='S4A_SPT', size=(8, 1), justification='right'),
    sg.InputText(setpoint_values['S4P_SPT'], key='S4P_SPT', size=(8, 1), justification='right'),
    sg.Button('OK', key='S4B3')],
    [sg.Text(' ', size=(17, 1)), sg.Text('Setpoint', size=(14, 1), justification='right'),  # Adjusted size
    sg.Text(setpoint_values['S4V_SPT'], size=(7, 1), key='S4V_SPT_display', justification='right'),
    sg.Text(setpoint_values['S4A_SPT'], size=(7, 1), key='S4A_SPT_display', justification='right'),
    sg.Text(setpoint_values['S4P_SPT'], size=(7, 1), key='S4P_SPT_display', justification='right')],
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

# Run the initialization function
if not initialize_from_arduino(window):
    # print("Initialization failed. Exiting program.")
    window.close()
    serialInst.close()
    exit(1)


last_request_time = time.time()
last_gui_update = time.time()
last_event_time = {}  # Track the last time each event was processed

# Event Loop
updates = []

while True:
    try:
        event, values = window.read(timeout=WINDOW_READ_TIMEOUT)
        if event in (sg.WIN_CLOSED, 'Exit'):
            print("Debug 40 - Window closed or Exit event triggered")
            break

         # High Priority - Button Events
        if event and isinstance(event, str):
            current_time = time.time()
            if event != '__TIMEOUT__':
                print(f"Debug 41 - Event: {event}")

            # Debounce mechanism
            if event not in last_event_time or (current_time - last_event_time[event] > DEBOUNCE_INTERVAL):
                last_event_time[event] = current_time
                match event:
                    case 'Mode':
                        GUI_button_states[event] = not GUI_button_states[event]
                        CNT_button_states[event] = handle_servo_buttons(event, "Mode AUTO", "Mode MANUAL", CNT_button_states[event], window)
                        window[event].update(text='Auto' if GUI_button_states[event] else 'Manual', button_color=('white', 'green') if GUI_button_states[event] else ('black', 'yellow'))
                        window.refresh()
                        print(f"Debug 42 - Sending command: {'Manual Mode' if GUI_button_states[event] else 'Auto'}")
                    case 'Repeat':
                        GUI_button_states[event] = not GUI_button_states[event]
                        CNT_button_states[event] = handle_servo_buttons(event, "Repeat", "Single", CNT_button_states[event], window)
                        window[event].update(text='Repeat' if GUI_button_states[event] else 'Single', button_color=('white', 'green') if GUI_button_states[event] else ('black', 'yellow'))
                        window.refresh()
                        print(f"Debug 43 - Sending command: {'Repeat' if GUI_button_states[event] else 'Single'}")
                    case 'Start':
                        GUI_button_states[event] = not GUI_button_states[event]
                        CNT_button_states[event] = handle_servo_buttons(event, "Start ENABLED", "Start DISABLED", CNT_button_states[event], window)
                        window[event].update(text='Step Enabled' if GUI_button_states[event] else 'Step Disabled', button_color=('white', 'green') if GUI_button_states[event] else ('black', 'yellow'))
                        window.refresh()
                        print(f"Debug 44 - Updating command: {'Step Enabled' if GUI_button_states[event] else 'Step Disabled'}")
                    case 'S1B1' | 'S2B1' | 'S3B1' | 'S4B1':
                        servo = int(event[1])
                        GUI_button_states[event] = not GUI_button_states[event]
                        CNT_button_states[event] = handle_servo_buttons(event, "ENABLE", "DISABLE", CNT_button_states[event], window)
                        window[event].update(text='Enabled' if GUI_button_states[event] else 'Disabled', button_color=('white', 'green') if GUI_button_states[event] else ('black', 'yellow'))
                        window.refresh()
                    case 'S1B2' | 'S2B2' | 'S3B2' | 'S4B2':
                        servo = int(event[1])
                        GUI_button_states[event] = not GUI_button_states[event]
                        CNT_button_states[event] = handle_servo_buttons(event, "RUN", "STOP", CNT_button_states[event], window)
                        window[event].update(text='STOP' if GUI_button_states[event] else 'RUN', button_color=('black', 'gray') if GUI_button_states[event] else ('white', 'gray'))
                        window.refresh()
                    case _ if event.endswith('B3'): # Handle Setpoint Update                                
                        servo = int(event[1])
                        V_data = validate_input(f'S{servo}V_SPT', values, 0, 80000)
                        A_data = validate_input(f'S{servo}A_SPT', values, 0, 100000)
                        P_data = validate_input(f'S{servo}P_SPT', values, 0, 8000)
                        if all(x is not None for x in (V_data, A_data, P_data)):
                            cmd = f"CMD:S{servo}_Parameters:{V_data},{A_data},{P_data}\n"
                            print(f"Debug 45 - Sending command: {cmd.strip()}")   
                            serialInst.write(cmd.encode('utf-8'))
                            serialInst.flush()
                            # Update setpoint_values and corresponding sg.Text elements
                            setpoint_values[f'S{servo}V_SPT'] = V_data
                            setpoint_values[f'S{servo}A_SPT'] = A_data
                            setpoint_values[f'S{servo}P_SPT'] = P_data
                            window[f'S{servo}V_SPT_display'].update(V_data)
                            window[f'S{servo}A_SPT_display'].update(A_data)
                            window[f'S{servo}P_SPT_display'].update(P_data)
                            window.refresh()
                            print(f"Debug 46 - Updated setpoints for S{servo}: V_SPT={V_data}, A_SPT={A_data}, P_SPT={P_data}")   


        # Background Tasks - Only process if no pending events
        current_time = time.time()
        
        # Medium Priority - Process Messages (reduced frequency)
        if current_time - last_request_time > MEDIUM_PRIORITY_UPDATE_INTERVAL:
            # print("Debug 50 - Sending CMD:REQUEST_VALUES to Arduino")   
            serialInst.write("CMD:REQUEST_VALUES\n".encode('utf-8'))
            serialInst.flush()
            last_request_time = current_time
       
        # Low Priority - Batch Update Display
        current_time = time.time()
        if current_time - last_gui_update > LOW_PRIORITY_UPDATE_INTERVAL:
            updates = []
            try:
                for _ in range(BATCH_SIZE):
                    message = message_queue.get_nowait()
                    if DEBUG_LOW_PRIORITY:
                       print(f"Debug 51 - Processing message: {message}")
                    if message.startswith("STATE_ENGINE:"):
                        process_response(message, "STATE_ENGINE:", window)
                    elif message.startswith("VALUES:"):
                        process_response(message, "VALUES:", window)
                    elif message.startswith("SETPOINTS:"):
                        process_response(message, "SETPOINTS:", window)
                    elif message.startswith("BUTTON_STATES:"):
                        process_response(message, "BUTTON_STATES:", window)
                        
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
        print(f"Debug 99 - Unexpected error in event loop: {str(e)}")
        break

# Cleanup
serial_thread.stop()
serial_thread.join()
serialInst.close()
window.close()

