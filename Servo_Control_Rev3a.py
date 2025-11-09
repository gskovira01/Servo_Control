import time
import threading
import queue
import serial
import PySimpleGUI as sg

# Initialize serial communication
serialInst = serial.Serial('COM10', 9600, timeout=1)

# Initialize message queue
message_queue = queue.Queue()

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
        value = int(values[key])
        if value < min_val or value > max_val:
            raise ValueError
        return value
    except ValueError:
        sg.popup_error(f"Invalid value for {key}. Please enter a value between {min_val} and {max_val}.")
        return None

# Function to handle commands
def handle_command(command):
    serialInst.write(f"{command}\n".encode('utf-8'))
    serialInst.flush()

# Function to read serial data
def read_serial():
    while True:
        if serialInst.in_waiting > 0:
            message = serialInst.readline().decode('utf-8').strip()
            message_queue.put(message)

# Start the serial reading thread
serial_thread = threading.Thread(target=read_serial, daemon=True)
serial_thread.start()

# Create the GUI layout
layout = [
    [sg.Button('S1B1'), sg.Button('S1B2'), sg.Button('S1B3')],
    [sg.Input(key='S1V'), sg.Input(key='S1A'), sg.Input(key='S1P')],
    [sg.Button('Exit')]
]

# Create the window
window = sg.Window('Servo Control', layout)

# Event loop
while True:
    event, values = window.read(timeout=100)  # Shorter timeout for responsiveness
    
    if event == sg.WIN_CLOSED or event == 'Exit':
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
    
    S1V_data = validate_input(event, 'S1V', values, 0, 10000)
    S1A_data = validate_input(event, 'S1A', values, 0, 20000)
    S1P_data = validate_input(event, 'S1P', values, 0, 6000)

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