import PySimpleGUI as sg
import time
import serial
import serial.tools.list_ports
import sys, threading, queue


# Initialize serial connection
serialInst = serial.Serial()
serialInst.baudrate = 9600
serialInst.port = 'COM10'
serialInst.timeout = 1  # Set a timeout for read operations
serialInst.open()
serialInst.reset_input_buffer()  # Clear the input buffer initially

arduinoPort = "COM10"
arduino = serial.Serial(arduinoPort, 9600, timeout=1)   # Open the port at 9600 baud
arduinoQueue = queue.Queue()

def listenToArduino():
    message = b''
    while True:
        incoming = arduino.read()
        if incoming == b'\n':
            arduinoQueue.put(message.decode('utf-8').strip().upper())
            message = b''
        else:
            if incoming not in (b'', b'\r'):
                message += incoming

# ---- MAIN CODE -----
arduinoThread = threading.Thread(target=listenToArduino, args=())
arduinoThread.daemon = True
arduinoThread.start()

# Handshaking
arduino.write(b'READY\n')
print("Waiting for Arduino")
while True:
    if not arduinoQueue.empty():
        if arduinoQueue.get() == "ACK":
            print("Arduino Ready")
            break

# Now you can proceed with further communication
# Example: Sending a command to the Arduino
arduino.write(b'HELLO\n')