import PySimpleGUI as sg # type: ignore
import serial # type: ignore
import threading
import queue
import time
import sys


DEBUG = False  # Global debug flag to control debug output
DEBUG_00 = False  # Global debug flag to control debug output

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
                        if DEBUG_00:
                            print(f"Debug 0 - Serial message received: {line}")
                else:
                    time.sleep(0.01)  # Prevent CPU hogging
            except Exception as e:
                if DEBUG_00:
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
serialInst = initialize_serial_connection('COM10')
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
# Define the motor setpoints array
motor1_setpoints = [
    [500, 50, 0],    # Idle
    [501, 50, 1850], # Address
    [502, 50, 1000], # Initial Take Away
    [503, 50, 1000], # Take Away
    [504, 50, 300],  # Full Rotation
    [505, 50, 0],    # Top of Swing
    [506, 50, 3000], # Initial Downswing
    [507, 50, 1750], # Release
    [508, 50, 1800], # Impact
    [508, 50, 1000], # Follow Through
    [500, 50, 1250]  # Finish
]

# Define the layout for the GUI
layout = [
    [sg.Text(f"Step {i}", size=(10, 1)), 
     sg.InputText(motor1_setpoints[i][0], key=f"velocity_{i}", size=(10, 1)), 
     sg.InputText(motor1_setpoints[i][1], key=f"acceleration_{i}", size=(10, 1)), 
     sg.InputText(motor1_setpoints[i][2], key=f"position_{i}", size=(10, 1))]
    for i in range(len(motor1_setpoints))
] + [
    [sg.Button("Update"), sg.Button("Exit")]
]

# Create the window
window = sg.Window("Motor Setpoints", layout)

# Event loop to process events and get values from inputs
while True:
    event, values = window.read()
    if event == sg.WINDOW_CLOSED or event == "Exit":
        break
    elif event == "Update":
        # Update the motor setpoints array with new values from the GUI
        for i in range(len(motor1_setpoints)):
            motor1_setpoints[i][0] = int(values[f"velocity_{i}"])
            motor1_setpoints[i][1] = int(values[f"acceleration_{i}"])
            motor1_setpoints[i][2] = int(values[f"position_{i}"])
        sg.popup("Setpoints updated successfully!")

# Close the window
window.close()