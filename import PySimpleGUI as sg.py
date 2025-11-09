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
        self.waiting_ack = None
        self.ack_timeout = 1.0  # 1 second timeout

    def send_command(self, command):
        print(f"Sending command: CMD:{command}")  # Debug print
        cmd = f"CMD:{command}\n"
        self.serial_port.write(cmd.encode('utf-8'))
        self.serial_port.flush()
        self.waiting_ack = command
        self.ack_start_time = time.time()

    def run(self):
        while self.running:
            if self.serial_port.in_waiting > 0:
                try:
                    line = self.serial_port.readline().decode('utf-8').rstrip()
                    if line.startswith('ACK:'):
                        received_ack = line[4:]
                        if received_ack == self.waiting_ack:
                            self.message_queue.put(f"Acknowledged: {received_ack}")
                            self.waiting_ack = None
                    else:
                        self.message_queue.put(line)
                except Exception as e:
                    self.message_queue.put(f"ERR:{str(e)}")
            
            # Check for timeout
            if self.waiting_ack and (time.time() - self.ack_start_time > self.ack_timeout):
                self.message_queue.put(f"ERR:Timeout waiting for {self.waiting_ack}")
                self.waiting_ack = None
            
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

def create_layout(low_limit, high_limit):
    layout = [
        [sg.Push(), sg.Column(''), sg.Text(' Velocity', size=(12, 1)), sg.Text('Acceleration', size=(12, 1)), sg.Text(' Position', size=(14, 1)), sg.Text(' ', size=(8, 1))],
        [sg.Push(), sg.Column(''), sg.Text(f"({low_limit}-{high_limit})", size=(12, 1)), sg.Text(f"({low_limit}-{high_limit})", size=(12, 1)), sg.Text(f"({low_limit}-{high_limit})", size=(14, 1)), sg.Text(' ', size=(8, 1))],
        
        *[create_servo_row(i) for i in range(1, 5)]
    ]
    return layout

def create_servo_row(servo_number):
    return [
        sg.Text(f'Servo {servo_number}', size=(8, 1)),
        sg.Button('ENABLE', button_color=('white', 'green'), key=f'S{servo_number}B1'),
        sg.Button('RUN', button_color=('white', 'red'), key=f'S{servo_number}B2'),
        sg.Input('', p=30, enable_events=True, key=f'S{servo_number}V'),
        sg.Input('', p=10, enable_events=True, key=f'S{servo_number}A'),
        sg.Input('', p=20, enable_events=True, key=f'S{servo_number}P'),
        sg.Button('OK', button_color=('white', 'blue'), key=f'S{servo_number}B3')
    ]

def validate_input(event, key, values, low, high):
    if event == key and len(values[key]) and values[key][-1] not in ('0123456789'):
        window[key].update(values[key][:-1])
    else:
        try:
            value = int(values[key])
            if value < low:
                window[key].update(low)
            elif value > high:
                window[key].update(high)
        except ValueError:
            pass  # Ignore if the value is not a valid integer
    return values[key]

def handle_servo_buttons(event, start_key, command_on, command_off):
    global toggle
    if event == start_key and not toggle:
        serial_thread.send_command(command_on)
        toggle = True
    elif event == start_key and toggle:
        serial_thread.send_command(command_off)
        toggle = False

# Initialize serial connection
serialInst = initialize_serial_connection('COM10')

# Create message queue and serial thread
message_queue = queue.Queue()
serial_thread = SerialThread(serialInst, message_queue)
serial_thread.start()

# Define the layout of the GUI
low_limit = 0
high_limit = 8000

layout = create_layout(low_limit, high_limit)

window = sg.Window("Robo Input", layout,
                   default_element_size=(10, 5),
                   size=(700, 500),
                   text_justification='center',
                   auto_size_text=False,
                   auto_size_buttons=False,
                   default_button_element_size=(8, 3),
                   finalize=True)

# Initialize button states for Servo 1
window['S1B1'].update(disabled=False)
window['S1B2'].update(disabled=False)

toggle = False

servo_data = {
    'S1': {'V': '', 'A': '', 'P': ''},
    'S2': {'V': '', 'A': '', 'P': ''},
    'S3': {'V': '', 'A': '', 'P': ''},
    'S4': {'V': '', 'A': '', 'P': ''}
}

while True:
    event, values = window.read(timeout=100)  # Shorter timeout for responsiveness
    
    if event == sg.WIN_CLOSED:
        serial_thread.stop()
        serial_thread.join()
        serialInst.close()
        break

    # Handle button events
    if event in [f'S{i}B1' for i in range(1, 5)]:
        key = event[:2]
        serialInst.write(f"{event}\n".encode('utf-8'))
        serialInst.flush()

    for i in range(1, 5):
        servo_key = f'S{i}'
        
        handle_servo_buttons(event, f'{servo_key}B1', f"{servo_key}B1 ENABLE", f"{servo_key}B1 DISABLE")
        handle_servo_buttons(event, f'{servo_key}B2', f"{servo_key}B2 START", f"{servo_key}B2 STOP")
        
        servo_data[servo_key]['V'] = validate_input(event, f'{servo_key}V', values, 0, 10000)
        servo_data[servo_key]['A'] = validate_input(event, f'{servo_key}A', values, 0, 20000)
        servo_data[servo_key]['P'] = validate_input(event, f'{servo_key}P', values, 0, 6000)
        
        if event == f'{servo_key}B3':
            data = f"{servo_data[servo_key]['V']},{servo_data[servo_key]['A']},{servo_data[servo_key]['P']}"
            full_data = f"CMD:{servo_key}_Parameters: {data}"
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