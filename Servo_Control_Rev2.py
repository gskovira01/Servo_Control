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

# Initialize serial connection
serialInst = serial.Serial()
serialInst.baudrate = 9600
serialInst.port = 'COM10'
serialInst.timeout = 1
serialInst.open()

# Add a small delay to allow Arduino to reset
time.sleep(2)

serialInst.reset_input_buffer()

# Create message queue and serial thread
message_queue = queue.Queue()
serial_thread = SerialThread(serialInst, message_queue)
serial_thread.start()

# Define the layout of the GUI
low_limit = 0
high_limit = 10000

layout = [
    [sg.Button('S1B1'), sg.Button('S1B2'), sg.Button('S1B3')],
    [sg.Input(key='S1V', default_text='0'), sg.Input(key='S1A', default_text='0'), sg.Input(key='S1P', default_text='0')],
    [sg.Button('Exit')]
]

# Create the window
window = sg.Window('Servo Control', layout)

# Function to handle servo buttons
def handle_servo_buttons(event, button_id, enable_command, disable_command):
    if event == button_id:
        if values[button_id]:
            serialInst.write(f"{enable_command}\n".encode('utf-8'))
        else:
            serialInst.write(f"{disable_command}\n".encode('utf-8'))
        serialInst.flush()

# Function to validate input
def validate_input(event, key, values, min_val, max_val):
    try:
        value_str = values[key]
        if value_str == '':
            raise ValueError("Empty value")
        value = int(value_str)
        if value < min_val or value > max_val:
            raise ValueError(f"Value out of range: {value}")
        return value
    except ValueError as e:
        sg.popup_error(f"Invalid value for {key}. Please enter a value between {min_val} and {max_val}. Error: {e}")
        return None

# Event loop
while True:
    event, values = window.read(timeout=100)  # Shorter timeout for responsiveness
    
    if event == sg.WIN_CLOSED or event == 'Exit':
        serial_thread.stop()
        serial_thread.join()
        serialInst.close()
        break

    # Handle button events
    if event == 'S1B1':
        serialInst.write("S1B1\n".encode('utf-8'))
        serialInst.flush()
        print("Sent command: S1B1")

    # Servo 1 Buttons
    handle_servo_buttons(event, 'S1B1', "S1B1 ENABLE", "S1B1 DISABLE")
    handle_servo_buttons(event, 'S1B2', "S1B2 START", "S1B2 STOP")
    
    # Add debug statements to check input values
    print(f"Values: {values}")
    
    S1V_data = validate_input(event, 'S1V', values, low_limit, high_limit)
    S1A_data = validate_input(event, 'S1A', values, low_limit, high_limit)
    S1P_data = validate_input(event, 'S1P', values, low_limit, high_limit)

    if event == 'S1B3':
        if S1V_data is not None and S1A_data is not None and S1P_data is not None:
            data = f"{S1V_data},{S1A_data},{S1P_data}"
            full_data = f"CMD:S1_Parameters: {data}"
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
        pass