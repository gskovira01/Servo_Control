"""
Servo Control Application
------------------------
Controls multiple servos via Arduino serial interface.
Handles parameter setting and state monitoring.
"""

import PySimpleGUI as sg
import serial
import threading
import queue
import time

class SerialThread(threading.Thread):
    """Serial port monitoring thread."""
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
                    self.message_queue.put(line)
                except Exception as e:
                    print(f"Debug - Serial error: {e}")
            time.sleep(0.1)

    def stop(self):
        """Stop thread execution."""
        self.running = False

def initialize_serial_connection(port, baudrate=9600, timeout=1):
    """
    Setup serial connection.
    
    Args:
        port (str): COM port name
        baudrate (int): Communication speed
        timeout (int): Read timeout seconds
        
    Returns:
        serial.Serial: Configured connection
    """
    try:
        serial_inst = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
        serial_inst.reset_input_buffer()
        return serial_inst
    except Exception as e:
        print(f"Debug - Serial port error: {e}")
        raise

def create_servo_row(servo_number, current_values, button_states):
    """Create GUI elements for one servo with blank row."""
    row1 = [
        sg.Text(f'Servo {servo_number}', size=(8, 1)),
        sg.Button('ENABLE', key=f'S{servo_number}B1', button_color=('white', 'green')),
        sg.Button('RUN', key=f'S{servo_number}B2', button_color=('white', 'green')),
        sg.Input(current_values.get(f'S{servo_number}V', '0'), size=(10, 1), key=f'S{servo_number}V'),
        sg.Input(current_values.get(f'S{servo_number}A', '0'), size=(10, 1), key=f'S{servo_number}A'),
        sg.Input(current_values.get(f'S{servo_number}P', '0'), size=(10, 1), key=f'S{servo_number}P'),
        sg.Button('OK', key=f'S{servo_number}B3', button_color=('white', 'blue'))
    ]
    
    row2 = [
        sg.Text('', size=(8, 1)),  # Servo label space
        sg.Text('', size=(15, 1)),  # ENABLE button space
        sg.Text('', size=(8, 1)),   # RUN button space
        sg.Text(current_values.get(f'S{servo_number}V', '0'), size=(10, 1), key=f'S{servo_number}V_display'),
        sg.Text(current_values.get(f'S{servo_number}A', '0'), size=(10, 1), key=f'S{servo_number}A_display'),
        sg.Text(current_values.get(f'S{servo_number}P', '0'), size=(10, 1), key=f'S{servo_number}P_display')
    ]
    

def initialize_states():
    """
    Get initial states from Arduino.
    
    Returns:
        bool: Success status
    """
    timeout = time.time() + 5
    values_received = False
    states_received = False
    
    print("Debug - Starting initialization...")
    
    while not message_queue.empty():
        message_queue.get()
    
    serialInst.write("CMD:REQUEST_VALUES\n".encode('utf-8'))
    serialInst.flush()
    time.sleep(0.1)
    
    serialInst.write("CMD:REQUEST_BUTTON_STATES\n".encode('utf-8'))
    serialInst.flush()
    
    while time.time() < timeout:
        try:
            message = message_queue.get_nowait()
            print(f"Debug - Init received: {message}")
            
            if message.startswith("VALUES:"):
                parts = message.split(":")[1].split(",")
                if len(parts) >= 12:
                    for servo in range(1, 5):
                        window[f'S{servo}V'].update(parts[(servo-1)*3])
                        window[f'S{servo}A'].update(parts[(servo-1)*3 + 1])
                        window[f'S{servo}P'].update(parts[(servo-1)*3 + 2])
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
            
            if values_received and states_received:
                print("Debug - Initialization complete")
                return True
                
        except queue.Empty:
            time.sleep(0.1)
            
    print("Debug - Initialization timeout")
    return False

def handle_servo_buttons(event, button_id, enable_command, disable_command, enabled):
    """
    Handle servo button events.
    
    Args:
        event (str): Event identifier
        button_id (str): Button identifier
        enable_command (str): Enable command string
        disable_command (str): Disable command string
        enabled (bool): Current state
        
    Returns:
        bool: New state
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

def validate_input(key, values, min_val, max_val):
    """
    Validate numeric input.
    
    Args:
        key (str): Input field key
        values (dict): Input values
        min_val (int): Minimum allowed value
        max_val (int): Maximum allowed value
        
    Returns:
        int: Validated value or None
    """
    try:
        value = int(values[key])
        if min_val <= value <= max_val:
            return value
    except ValueError:
        pass
    print(f"Invalid value for {key}")
    return None

# Initialize serial connection
serialInst = initialize_serial_connection('COM10')
message_queue = queue.Queue()
serial_thread = SerialThread(serialInst, message_queue)
serial_thread.start()

# Setup GUI
current_values = {f'S{i}{p}': '0' for i in range(1, 5) for p in ['V', 'A', 'P']}
button_states = {f'S{i}B{j}': False for i in range(1, 5) for j in range(1, 3)}
servo_states = button_states.copy()

layout = [
    [sg.Push(), sg.Text('Velocity', size=(12, 1)), sg.Text('Acceleration', size=(12, 1)),
     sg.Text('Position', size=(14, 1)), sg.Text('', size=(8, 1))],
    [sg.Push(), sg.Text('(0-10000)', size=(12, 1)), sg.Text('(0-20000)', size=(12, 1)),
     sg.Text('(0-6000)', size=(14, 1)), sg.Text('', size=(8, 1))],
    *[create_servo_row(i, current_values, button_states) for i in range(1, 5)]
]

window = sg.Window("Servo Control", layout,
                  default_element_size=(10, 5),
                  size=(700, 500),
                  auto_size_text=False,
                  auto_size_buttons=False,
                  finalize=True)

if not initialize_states():
    print("Warning: Failed to get initial states")

# Event Loop
while True:
    try:
        event, values = window.read(timeout=100)
        
        if event in (sg.WIN_CLOSED, 'Exit'):
            break
            
        # Handle button events
        for servo in range(1, 5):
            servo_states[f'S{servo}B1'] = handle_servo_buttons(
                event, f'S{servo}B1',
                f"S{servo}B1 ENABLE", f"S{servo}B1 DISABLE",
                servo_states[f'S{servo}B1'])
            servo_states[f'S{servo}B2'] = handle_servo_buttons(
                event, f'S{servo}B2',
                f"S{servo}B2 START", f"S{servo}B2 STOP",
                servo_states[f'S{servo}B2'])
            
            if event == f'S{servo}B3':
                V_data = validate_input(f'S{servo}V', values, 0, 10000)
                A_data = validate_input(f'S{servo}A', values, 0, 20000)
                P_data = validate_input(f'S{servo}P', values, 0, 6000)
                if all(x is not None for x in (V_data, A_data, P_data)):
                    cmd = f"CMD:S{servo}_Parameters:{V_data},{A_data},{P_data}\n"
                    print(f"Debug - Sending: {cmd}")
                    serialInst.write(cmd.encode('utf-8'))
                    serialInst.flush()
        
        # Process messages
        try:
            while True:
                message = message_queue.get_nowait()
                print(f"Debug - Received: {message}")
                window.refresh()
        except queue.Empty:
            pass
            
    except Exception as e:
        print(f"Debug - Error in event loop: {e}")
        break

# Cleanup
print("Debug - Cleaning up...")
window.close()
serial_thread.stop()
serial_thread.join()
serialInst.close()