import PySimpleGUI as sg
import serial
import threading
import queue
import time

class SerialThread(threading.Thread):
    def __init__(self, serial_port, message_queue):
        threading.Thread.__init__(self)
        self.serial_port = serial_port
        self.message_queue = message_queue
        self.running = True

    def run(self):
        while self.running:
            if self.serial_port.in_waiting > 0:
                try:
                    line = self.serial_port.readline().decode('utf-8').rstrip()
                    self.message_queue.put(line)
                except Exception as e:
                    self.message_queue.put(f"Error: {str(e)}")
            time.sleep(0.1)

    def stop(self):
        self.running = False

def initialize_serial_connection(port, baudrate=9600, timeout=1):
    serial_inst = serial.Serial()
    serial_inst.baudrate = baudrate
    serial_inst.port = port
    serial_inst.timeout = timeout
    serial_inst.open()
    serial_inst.reset_input_buffer()
    return serial_inst

def request_current_values():
    serialInst.write("CMD:REQUEST_VALUES\n".encode('utf-8'))
    serialInst.flush()
    time.sleep(0.5)  # Wait for Arduino to respond
    values = {
        'S1V': '0', 'S1A': '0', 'S1P': '0',
        'S2V': '0', 'S2A': '0', 'S2P': '0',
        'S3V': '0', 'S3A': '0', 'S3P': '0',
        'S4V': '0', 'S4A': '0', 'S4P': '0'
    }
    while serialInst.in_waiting > 0:
        line = serialInst.readline().decode('utf-8').rstrip()
        if line.startswith("VALUES:"):
            parts = line.split(":")[1].split(",")
            values.update({
                'S1V': parts[0],
                'S1A': parts[1],
                'S1P': parts[2],
                'S2V': parts[3],
                'S2A': parts[4],
                'S2P': parts[5],
                'S3V': parts[6],
                'S3A': parts[7],
                'S3P': parts[8],
                'S4V': parts[9],
                'S4A': parts[10],
                'S4P': parts[11],
            })
    return values

def request_button_states():
    serialInst.write("CMD:REQUEST_BUTTON_STATES\n".encode('utf-8'))
    serialInst.flush()
    time.sleep(0.5)  # Wait for Arduino to respond
    states = {
        'S1B1': False, 'S1B2': False,
        'S2B1': False, 'S2B2': False,
        'S3B1': False, 'S3B2': False,
        'S4B1': False, 'S4B2': False
    }
    while serialInst.in_waiting > 0:
        line = serialInst.readline().decode('utf-8').rstrip()
        if line.startswith("BUTTON_STATES:"):
            parts = line.split(":")[1].split(",")
            states.update({
                'S1B1': parts[0] == '1',
                'S1B2': parts[1] == '1',
                'S2B1': parts[2] == '1',
                'S2B2': parts[3] == '1',
                'S3B1': parts[4] == '1',
                'S3B2': parts[5] == '1',
                'S4B1': parts[6] == '1',
                'S4B2': parts[7] == '1'
            })
    return states

def create_layout(low_limit, high_limit, current_values, button_states):
    layout = [
        [sg.Push(), sg.Column(''), sg.Text(' Velocity', size=(12, 1)), sg.Text('Acceleration', size=(12, 1)), sg.Text(' Position', size=(14, 1)), sg.Text(' ', size=(8, 1))],
        [sg.Push(), sg.Column(''), sg.Text(f"({low_limit}-{high_limit})", size=(12, 1)), sg.Text(f"({low_limit}-{high_limit})", size=(12, 1)), sg.Text(f"({low_limit}-{high_limit})", size=(14, 1)), sg.Text(' ', size=(8, 1))],
        
        *[create_servo_row(i, current_values, button_states) for i in range(1, 5)]
    ]
    return layout

def create_servo_row(servo_number, current_values, button_states):
    return [
        sg.Text(f'Servo {servo_number}', size=(8, 1)),
        sg.Button('ENABLE' if not button_states[f'S{servo_number}B1'] else 'DISABLE', button_color=('white', 'green' if not button_states[f'S{servo_number}B1'] else 'red'), key=f'S{servo_number}B1'),
        sg.Button('RUN' if not button_states[f'S{servo_number}B2'] else 'STOP', button_color=('white', 'green' if not button_states[f'S{servo_number}B2'] else 'red'), key=f'S{servo_number}B2'),
        sg.Input(current_values.get(f'S{servo_number}V', '0'), size=(10, 1), enable_events=True, key=f'S{servo_number}V'),
        sg.Input(current_values.get(f'S{servo_number}A', '0'), size=(10, 1), enable_events=True, key=f'S{servo_number}A'),
        sg.Input(current_values.get(f'S{servo_number}P', '0'), size=(10, 1), enable_events=True, key=f'S{servo_number}P'),
        sg.Button('OK', button_color=('white', 'blue'), key=f'S{servo_number}B3')
    ]

# Initialize serial connection
serialInst = initialize_serial_connection('COM10')

# Create message queue and serial thread
message_queue = queue.Queue()
serial_thread = SerialThread(serialInst, message_queue)
serial_thread.start()

# Request current values and button states from Arduino
current_values = request_current_values()
button_states = request_button_states()

# Define the layout of the GUI
low_limit = 0
high_limit = 8000

layout = create_layout(low_limit, high_limit, current_values, button_states)

window = sg.Window("Robo Input", layout,
                   default_element_size=(10, 5),
                   size=(700, 500),
                   text_justification='center',
                   auto_size_text=False,
                   auto_size_buttons=False,
                   default_button_element_size=(8, 3),
                   finalize=True)

# Initialize button states for all servos
servo_states = button_states

# Function to handle servo buttons
def handle_servo_buttons(event, button_id, enable_command, disable_command, enabled):
    if event == button_id:
        if enabled:
            serialInst.write(f"CMD:{disable_command}\n".encode('utf-8'))
            try:
                window[button_id].update(text='ENABLE' if 'ENABLE' in enable_command else 'RUN', button_color=('white', 'green' if 'ENABLE' in enable_command else 'red'))
            except KeyError:
                print(f"Button {button_id} does not exist.")
            except Exception as e:
                print(f"Error updating button {button_id}: {e}")
        else:
            serialInst.write(f"CMD:{enable_command}\n".encode('utf-8'))
            try:
                window[button_id].update(text='DISABLE' if 'ENABLE' in enable_command else 'STOP', button_color=('white', 'red' if 'ENABLE' in enable_command else 'green'))
            except KeyError:
                print(f"Button {button_id} does not exist.")
            except Exception as e:
                print(f"Error updating button {button_id}: {e}")
        serialInst.flush()
        return not enabled
    return enabled

# Function to validate input
def validate_input(key, values, min_val, max_val):
    try:
        value_str = values[key]
        if value_str == '':
            raise ValueError("Empty value")
        value = int(value_str)
        if value < min_val or value > max_val:
            raise ValueError(f"Value out of range: {value}")
        return value
    except ValueError as e:
        print(f"Invalid value for {key}. Please enter a value between {min_val} and {max_val}. Error: {e}")
        return None

# Event loop
while True:
    event, values = window.read(timeout=100)  # Shorter timeout for responsiveness
    
    if event == sg.WIN_CLOSED or event == 'Exit':
        serial_thread.stop()
        serial_thread.join()
        serialInst.close()
        break

    # Handle button events for all servos
    for servo in range(1, 5):
        servo_states[f'S{servo}B1'] = handle_servo_buttons(event, f'S{servo}B1', f"S{servo}B1 ENABLE", f"S{servo}B1 DISABLE", servo_states[f'S{servo}B1'])
        servo_states[f'S{servo}B2'] = handle_servo_buttons(event, f'S{servo}B2', f"S{servo}B2 START", f"S{servo}B2 STOP", servo_states[f'S{servo}B2'])
    
    # Print values only when a button is pressed
    if event in [f'S{servo}B1' for servo in range(1, 5)] + [f'S{servo}B2' for servo in range(1, 5)] + [f'S{servo}B3' for servo in range(1, 5)]:
        print(f"Values: {values}")

    # Handle parameter input for all servos
    for servo in range(1, 5):
        if event == f'S{servo}B3':
            V_data = validate_input(f'S{servo}V', values, 0, 10000)
            A_data = validate_input(f'S{servo}A', values, 0, 20000)
            P_data = validate_input(f'S{servo}P', values, 0, 6000)
            if V_data is not None and A_data is not None and P_data is not None:
                data = f"{V_data},{A_data},{P_data}"
                full_data = f"CMD:S{servo}_Parameters: {data}"
                time.sleep(0.1)  # Small delay to ensure data is processed
                serialInst.write(full_data.encode('utf-8'))
                print("Sending Data: ", full_data)
                serialInst.flush()
                
    # Check for messages from serial thread
    try:
        while True:  # Process all available messages
            message = message_queue.get_nowait()
            print(f"Received: {message}")
            # Update GUI based on received message
            window.refresh()
    except queue.Empty:
        pass  # No messages in queue