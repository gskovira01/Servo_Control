from operator import add
# import PySimpleGUI as sg # type: ignore
import FreeSimpleGUI as sg
import socket
import threading
import queue
import time
import sys

# Global state
state_engine_step = 0
DEBUG = False
DEBUG00 = False
DEBUG_LOW_PRIORITY = False
DEBUG_MEDIUM_PRIORITY = False
DEBUG_HIGH_PRIORITY = False

# Constants
WINDOW_READ_TIMEOUT = 100
MEDIUM_PRIORITY_UPDATE_INTERVAL = 0.1
LOW_PRIORITY_UPDATE_INTERVAL = 0.1
BATCH_SIZE = 30
DEBOUNCE_INTERVAL = 0.05

# --- UDP CONFIGURATION ---
CLEARCORE1_IP = '192.168.1.171'
CLEARCORE1_PORT = 8888
LOCAL_PORT1 = 8889

CLEARCORE2_IP = '192.168.1.172'
CLEARCORE2_PORT = 8890
LOCAL_PORT2 = 8889

# --- UDP SOCKET SETUP ---
# Only one UDP socket
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
udp_sock.bind(('', 8889))
udp_sock.settimeout(0.1)

message_queue = queue.Queue()

class UDPReceiverThread(threading.Thread):
    def __init__(self, udp_sock, message_queue):
        super().__init__()
        self.udp_sock = udp_sock
        self.message_queue = message_queue
        self.running = True

    def run(self):
        while self.running:
            try:
                data, addr = self.udp_sock.recvfrom(1024)
                message = data.decode('utf-8').strip()
                if message:
                    self.message_queue.put(message)
            except socket.timeout:
                continue
            except Exception as e:
                print(f"UDP receive error: {e}")
                self.running = False

    def stop(self):
        self.running = False

udp_thread = UDPReceiverThread(udp_sock, message_queue)
udp_thread.start()

def send_udp_command1(cmd):
    udp_sock.sendto(cmd.encode('utf-8'), (CLEARCORE1_IP, CLEARCORE1_PORT))

def send_udp_command2(cmd):
    udp_sock.sendto(cmd.encode('utf-8'), (CLEARCORE2_IP, CLEARCORE2_PORT))

# --- Per-board state dictionaries ---
arduino_values_1 = {
    'S1V': '0', 'S1A': '0', 'S1P': '0',
    'S2V': '0', 'S2A': '0', 'S2P': '0',
    'S3V': '0', 'S3A': '0', 'S3P': '0',
    'S4V': '0', 'S4A': '0', 'S4P': '0'
}
arduino_values_2 = arduino_values_1.copy()

setpoint_values_1 = {
    'Mode': 0, 'Repeat': 0, 'Start': 0,
    'S1V_SPT': 10000, 'S1A_SPT': 10000, 'S1P_SPT': 0,
    'S2V_SPT': 10000, 'S2A_SPT': 10000, 'S2P_SPT': 0,
    'S3V_SPT': 10000, 'S3A_SPT': 10000, 'S3P_SPT': 0,
    'S4V_SPT': 10000, 'S4A_SPT': 10000, 'S4P_SPT': 0
}
setpoint_values_2 = setpoint_values_1.copy()

GUI_button_states_1 = {
    'Mode': False, 'Repeat': False, 'Start': False,
    'S1B1': False, 'S1B2': False, 'S2B1': False, 'S2B2': False,
    'S3B1': False, 'S3B2': False, 'S4B1': False, 'S4B2': False
}
GUI_button_states_2 = GUI_button_states_1.copy()
CNT_button_states_1 = GUI_button_states_1.copy()
CNT_button_states_2 = GUI_button_states_2.copy()

values_received = False
states_received = False
setpoints_received = False

def initialize_buttons(window, message_queue):
    global states_received, CNT_button_states, GUI_button_states
    MAX_RETRIES = 5
    TIMEOUT = 5
    for attempt in range(MAX_RETRIES):
        states_received = False
        request = "CMD:REQUEST_BUTTON_STATES\n"
        expected = "BUTTON_STATES:"
        time.sleep(.5)
        time.sleep(.5)
        timeout = time.time() + TIMEOUT
        while time.time() < timeout:
            try:
                message = message_queue.get(timeout=0.5)
                if message.startswith(expected):
                    if process_button_states_response(message, window):
                        CNT_button_states = GUI_button_states.copy()
                        return True
            except queue.Empty:
                continue
        time.sleep(2)
    return False



def initialize_setpoints(window, message_queue):
    global setpoints_received, setpoint_values
    MAX_RETRIES = 3
    TIMEOUT = 5
    for attempt in range(MAX_RETRIES):
        setpoints_received = False
        request = "CMD:REQUEST_SETPOINTS\n"
        expected = "SETPOINTS:"
        time.sleep(0.5)
        timeout = time.time() + TIMEOUT
        while time.time() < timeout:
            try:
                message = message_queue.get(timeout=0.5)
                if message.startswith(expected):
                    if process_setpoints_response(message, window):
                        setpoint_values.update({
                            'S1V_SPT': setpoint_values['S1V_SPT'], 'S1A_SPT': setpoint_values['S1A_SPT'], 'S1P_SPT': setpoint_values['S1P_SPT'],
                            'S2V_SPT': setpoint_values['S2V_SPT'], 'S2A_SPT': setpoint_values['S2A_SPT'], 'S2P_SPT': setpoint_values['S2P_SPT'],
                            'S3V_SPT': setpoint_values['S3V_SPT'], 'S3A_SPT': setpoint_values['S3A_SPT'], 'S3P_SPT': setpoint_values['S3P_SPT'],
                            'S4V_SPT': setpoint_values['S4V_SPT'], 'S4A_SPT': setpoint_values['S4A_SPT'], 'S4P_SPT': setpoint_values['S4P_SPT']
                        })
                        return True
            except queue.Empty:
                continue
        time.sleep(2)
    return False

def initialize_state_engine(window, message_queue):
    global state_engine_step
    MAX_RETRIES = 3
    TIMEOUT = 5
    for attempt in range(MAX_RETRIES):
        state_engine_step = None
        request = "CMD:REQUEST_STATE_ENGINE\n"
        expected = "STATE_ENGINE:"
        time.sleep(0.5)
        timeout = time.time() + TIMEOUT
        while time.time() < timeout:
            try:
                message = message_queue.get(timeout=0.5)
                if message.startswith(expected):
                    if process_state_engine_response(message, window):
                        return True
            except queue.Empty:
                continue
        time.sleep(2)
    return False

def initialize_from_arduino(window, send_udp_command, message_queue):
    send_udp_command("CMD:REQUEST_BUTTON_STATES\n")
    if not initialize_buttons(window, message_queue):
        return False
    send_udp_command("CMD:REQUEST_SETPOINTS\n")
    if not initialize_setpoints(window, message_queue):
        return False
    send_udp_command("CMD:REQUEST_STATE_ENGINE\n")
    if not initialize_state_engine(window, message_queue):
        return False
    return True

def process_values_response(message, window, arduino_values, prefix):
    # print(f"process_values_response called for {prefix}: {message}")
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
        #window[prefix+'S1A_display'].update(arduino_values['S1A'])
        window[prefix+'S1P_display'].update(arduino_values['S1P'])
        #window[prefix+'S2A_display'].update(arduino_values['S2A'])
        window[prefix+'S2P_display'].update(arduino_values['S2P'])
        #window[prefix+'S3A_display'].update(arduino_values['S3A'])
        window[prefix+'S3P_display'].update(arduino_values['S3P'])
        #window[prefix+'S4A_display'].update(arduino_values['S4A'])
        window[prefix+'S4P_display'].update(arduino_values['S4P'])
        window.refresh()
        return True
    return False

def process_button_states_response(message, window):
    global states_received, GUI_button_states, CNT_button_states
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
        CNT_button_states = GUI_button_states.copy()
        states_received = True
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
        window.refresh()
        return True
    return False

def process_setpoints_response(message, window):
    global setpoints_received, setpoint_values
    parts = message.split(":")[1].split(",")
    if len(parts) >= 12:
        try:
            S1V_SPT, S1A_SPT, S1P_SPT = map(int, parts[0:3])
            S2V_SPT, S2A_SPT, S2P_SPT = map(int, parts[3:6])
            S3V_SPT, S3A_SPT, S3P_SPT = map(int, parts[6:9])
            S4V_SPT, S4A_SPT, S4P_SPT = map(int, parts[9:12])
            setpoints_received = True
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
            window.refresh()
            return True
        except ValueError:
            print("Error processing setpoints response")
    return False

def process_state_engine_response(message, window):
    global state_engine_step
    parts = message.split(":")[1].split(",")
    if len(parts) >= 1:
        state_engine_step = int(parts[0])
        window['state_engine_step'].update(state_engine_step)
        window.refresh()
        return True
    return False

def process_response(message, expected, window):
    if expected == "BUTTON_STATES:":
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
            send_udp_command("CMD:Mode MANUAL\n")
            window[event].update(text='Auto', button_color=('white', 'green'))
            GUI_button_states[event] = False
        else:
            # print(f"Debugs 27 - Sending enable command for Mode: AUTO")   
            send_udp_command("CMD:Mode AUTO\n")
            window[event].update(text='Manual', button_color=('black', 'yellow'))
            GUI_button_states[event] = True

    elif event == 'Repeat':  # Repeat is either enabled or disabled
        if enabled:
            # print(f"Debugs 28 - Sending disable command for Repeat: DISABLE")   
            send_udp_command("CMD:Repeat DISABLE\n")
            window[event].update(text='Repeat', button_color=('white', 'green'))
            GUI_button_states[event] = False
        else:
            # print(f"Debugs 29 - Sending enable command for Repeat: ENABLE")   
            send_udp_command("CMD:Repeat ENABLE\n")
            window[event].update(text='Single', button_color=('black', 'yellow'))
            GUI_button_states[event] = True

    elif event == 'Start':  # Start is either enabled or disabled
        if enabled:
            # print(f"Debugs 30 - Sending disable command for Start: DISABLE")   
            send_udp_command("CMD:Start DISABLE\n")
            window[event].update(text='Disable Start', button_color=('white', 'green'))
            GUI_button_states[event] = False
        else:
            # print(f"Debugs 31 - Sending enable command for Start: ENABLE")   
            send_udp_command("CMD:Start ENABLE\n")
            window[event].update(text='Enable Start', button_color=('black', 'yellow'))
            GUI_button_states[event] = True
    
    elif event.endswith('B1'):  # B1 is either ENABLE or DISABLE
        if enabled:
            # print(f"Debugs 32 - Sending disable command for {event}: DISABLE")   
            send_udp_command(f"CMD:{event} DISABLE\n")
            window[event].update(text='ENabled', button_color=('white', 'green'))
            GUI_button_states[event] = False
        else:
            # print(f"Debugs 33 - Sending enable command for {event}: ENABLE")   
            send_udp_command(f"CMD:{event} ENABLE\n")
            window[event].update(text='DISabled', button_color=('black', 'yellow'))
            GUI_button_states[event] = True
    
    elif event.endswith('B2'):  # B2 is either Run or Stop
        if enabled:
            # print(f"Debugs 34 - Sending disable command for {event}: STOP")   
            send_udp_command(f"CMD:{event} STOP\n")
            window[event].update(text='Spare', button_color=('black', 'gray'))
            GUI_button_states[event] = False
        else:
            # print(f"Debugs 35 - Sending enable command for {event}: Start")   
            send_udp_command(f"CMD:{event} Start\n")
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
            send_udp_command(cmd)
            # (UDP does not need flush)
            # Update setpoint_values and corresponding sg.Text elements
            setpoint_values[f'S{servo}V_SPT'] = V_data
            setpoint_values[f'S{servo}A_SPT'] = A_data
            setpoint_values[f'S{servo}P_SPT'] = P_data
            window.refresh()
            # print(f"Debugs 37 - Updated setpoints for S{servo}: V_SPT={V_data}, A_SPT={A_data}, P_SPT={P_data}")   
    
    # (UDP does not need flush)
    return not enabled

def validate_input(key, values, min_val, max_val):
    try:
        value = int(values[key])
        if min_val <= value <= max_val:
            return value
    except ValueError:
        print(f"Invalid value for {key}")
    return None

def show_numeric_keypad(title, current_value, min_val=0, max_val=18000):
    """Custom numeric keypad popup for touchscreen input"""
    layout = [
        [sg.Text(title, font=('Helvetica', 14, 'bold'))],
        [sg.Text('Current Value:', font=('Helvetica', 12)), 
         sg.InputText(str(current_value), key='display', size=(15, 1), font=('Helvetica', 14), justification='center', readonly=False)],
        [sg.Button('7', size=(4, 2), font=('Helvetica', 16)), 
         sg.Button('8', size=(4, 2), font=('Helvetica', 16)), 
         sg.Button('9', size=(4, 2), font=('Helvetica', 16))],
        [sg.Button('4', size=(4, 2), font=('Helvetica', 16)), 
         sg.Button('5', size=(4, 2), font=('Helvetica', 16)), 
         sg.Button('6', size=(4, 2), font=('Helvetica', 16))],
        [sg.Button('1', size=(4, 2), font=('Helvetica', 16)), 
         sg.Button('2', size=(4, 2), font=('Helvetica', 16)), 
         sg.Button('3', size=(4, 2), font=('Helvetica', 16))],
        [sg.Button('Clear', size=(4, 2), font=('Helvetica', 14)), 
         sg.Button('0', size=(4, 2), font=('Helvetica', 16)), 
         sg.Button('⌫', size=(4, 2), font=('Helvetica', 16))],
        [sg.Button('Cancel', size=(8, 2), font=('Helvetica', 14)), 
         sg.Button('OK', size=(8, 2), font=('Helvetica', 14))]
    ]
    
    popup_window = sg.Window(title, layout, modal=True, finalize=True, location=(300, 200))
    
    while True:
        event, values = popup_window.read()
        
        if event in (sg.WIN_CLOSED, 'Cancel'):
            popup_window.close()
            return None
            
        elif event == 'OK':
            try:
                result = int(values['display'])
                if min_val <= result <= max_val:
                    popup_window.close()
                    return result
                else:
                    sg.popup_error(f'Value must be between {min_val} and {max_val}', keep_on_top=True)
            except ValueError:
                sg.popup_error('Please enter a valid number', keep_on_top=True)
                
        elif event == 'Clear':
            popup_window['display'].update('')
            
        elif event == '⌫':  # Backspace
            current = values['display']
            popup_window['display'].update(current[:-1])
            
        elif event in '0123456789':
            current = values['display']
            popup_window['display'].update(current + event)

def build_board_panel(board_num, arduino_values, setpoint_values, GUI_button_states):
    prefix = f'B{board_num}_'
    panel = [
        # [sg.Text(f'Board {board_num} State Engine Step:', size=(22, 1), justification='right', font=('Helvetica', 12, 'bold')), sg.Text('0', size=(3, 1), key=prefix+'state_engine_step', font=('Helvetica', 12, 'bold'))],
        # [
    # sg.Text('', size=(8, 1)),  # <-- This moves the buttons to the right by 6 characters
    # sg.Button('Auto' if GUI_button_states['Mode'] else 'Manual', key=prefix+'Mode',
              # button_color=('white', 'green') if GUI_button_states['Mode'] else ('black', 'yellow')),
    # sg.Button('Repeat' if GUI_button_states['Repeat'] else 'Single', key=prefix+'Repeat',
              # button_color=('white', 'green') if GUI_button_states['Repeat'] else ('black', 'yellow')),
    # sg.Button('Started' if GUI_button_states['Start'] else 'Start', key=prefix+'Start',
              # button_color=('white', 'green') if GUI_button_states['Start'] else ('black', 'yellow')),
        # ],
        [sg.Text(' ', size=(35, 1)), sg.Text('Velocity', size=(6, 1)), sg.Text('Acceleration', size=(9, 1)), sg.Text('Position', size=(7, 1))],
    ]
    for i in range(1, 5):
        panel += [
            [sg.Text(f'Servo {i}', size=(8, 1)),
             sg.Button('Enabled' if GUI_button_states[f'S{i}B1'] else 'Disabled', key=prefix+f'S{i}B1', button_color=('white', 'green') if GUI_button_states[f'S{i}B1'] else ('black', 'yellow')),
             sg.Button('Run' if GUI_button_states[f'S{i}B2'] else 'Stop', key=prefix+f'S{i}B2', button_color=('white', 'green') if GUI_button_states[f'S{i}B2'] else ('black', 'yellow')),
             sg.Button(f'{setpoint_values[f"S{i}V_SPT"]}', key=prefix+f'S{i}V_SPT_btn', size=(8, 1), button_color=('black', 'lightblue')),
             sg.Button(f'{setpoint_values[f"S{i}A_SPT"]}', key=prefix+f'S{i}A_SPT_btn', size=(8, 1), button_color=('black', 'lightblue')),
             sg.Button(f'{setpoint_values[f"S{i}P_SPT"]}', key=prefix+f'S{i}P_SPT_btn', size=(8, 1), button_color=('black', 'lightblue')),
             sg.Button('OK', key=prefix+f'S{i}B3', size=(8, 2))],
            [sg.Text(' ', size=(8, 1)),
             sg.Button('Clear Value', key=prefix+f'S{i}B4', button_color=('black', 'orange')),
             sg.Text('Current Value', size=(12, 1), justification='right'),
             sg.Text('', size=(7, 1)),  # Placeholder for velocity column
             sg.Text('', size=(7, 1)),  # Placeholder for acceleration column
             sg.Text(arduino_values[f'S{i}P'], size=(6, 1), key=prefix+f'S{i}P_display', justification='right')]
        ]
    return panel

layout = [
    [sg.TabGroup(
        [[
            sg.Tab('Board 1', build_board_panel(1, arduino_values_1, setpoint_values_1, GUI_button_states_1), key='TAB1'),
            sg.Tab('Board 2', build_board_panel(2, arduino_values_2, setpoint_values_2, GUI_button_states_2), key='TAB2')
        ]],
        key='TABGROUP',
        tab_background_color='darkgray',           # color of all tabs
        selected_title_color='darkblue',               # text color of selected tab
        selected_background_color='white'        # background color of selected tab
    )]
]

window = sg.Window("Servo Control",
            layout, default_element_size=(8, 5),
            size=(800, 460),
            location=(0, 0),
            auto_size_text=False,
            auto_size_buttons=False,
            finalize=True)

init_error_queue = queue.Queue()

last_request_time = time.time()
last_gui_update = time.time()
last_event_time = {}

while True:
    event, values = window.read(timeout=WINDOW_READ_TIMEOUT)
    try:
        error_msg = init_error_queue.get_nowait()
        sg.popup_error(error_msg)
    except queue.Empty:
        pass

    if event == sg.WIN_CLOSED or event == "Exit":
        print("Debug 40 - Window closed or Exit event triggered")
        break

    board_num = None
    event_key = event
    if isinstance(event, str) and event.startswith("B1_"):
        board_num = 1
        event_key = event[3:]
    elif isinstance(event, str) and event.startswith("B2_"):
        board_num = 2
        event_key = event[3:]

    if board_num == 1:
        GUI_button_states = GUI_button_states_1
        CNT_button_states = CNT_button_states_1
        setpoint_values = setpoint_values_1
        send_udp_command = send_udp_command1
        message_queue = message_queue
    elif board_num == 2:
        GUI_button_states = GUI_button_states_2
        CNT_button_states = CNT_button_states_2
        setpoint_values = setpoint_values_2
        send_udp_command = send_udp_command2
        message_queue = message_queue

    # --- Button Events with BOARD prefix for all commands ---
    if event and isinstance(event, str) and board_num:
        current_time = time.time()
        if event != '__TIMEOUT__':
            print(f"Debug 41 - Event: {event}")

        if event not in last_event_time or (current_time - last_event_time[event] > DEBOUNCE_INTERVAL):
            last_event_time[event] = current_time
            match event_key:
                case 'Mode':
                    GUI_button_states[event_key] = not GUI_button_states[event_key]
                    CNT_button_states[event_key] = handle_servo_buttons(event, "Mode AUTO", "Mode MANUAL", CNT_button_states[event_key], window)
                    window[event].update(
                        text='Auto' if GUI_button_states[event_key] else 'Manual',
                        button_color=('white', 'green') if GUI_button_states[event_key] else ('black', 'yellow')
                    )
                    window.refresh()
                    mode_cmd = "Mode AUTO" if GUI_button_states[event_key] else "Mode MANUAL"
                    cmd = f"BOARD:{board_num};CMD:{mode_cmd}\n"
                    print(f"Debug 42 - Sending command: {cmd.strip()}")
                    send_udp_command(cmd)
                case 'Repeat':
                    GUI_button_states[event_key] = not GUI_button_states[event_key]
                    CNT_button_states[event_key] = handle_servo_buttons(event, "Repeat", "Single", CNT_button_states[event_key], window)
                    window[event].update(
                        text='Repeat' if GUI_button_states[event_key] else 'Single',
                        button_color=('white', 'green') if GUI_button_states[event_key] else ('black', 'yellow')
                    )
                    window.refresh()
                    repeat_cmd = "Repeat ENABLE" if GUI_button_states[event_key] else "Repeat DISABLE"
                    cmd = f"BOARD:{board_num};CMD:{repeat_cmd}\n"
                    print(f"Debug 43 - Sending command: {cmd.strip()}")
                    send_udp_command(cmd)
                case 'Start':
                    GUI_button_states[event_key] = not GUI_button_states[event_key]
                    CNT_button_states[event_key] = handle_servo_buttons(event, "Start ENABLED", "Start DISABLED", CNT_button_states[event_key], window)
                    window[event].update(
                        text='Step Enabled' if GUI_button_states[event_key] else 'Step Disabled',
                        button_color=('white', 'green') if GUI_button_states[event_key] else ('black', 'yellow')
                    )
                    window.refresh()
                    start_cmd = "Start ENABLE" if GUI_button_states[event_key] else "Start DISABLE"
                    cmd = f"BOARD:{board_num};CMD:{start_cmd}\n"
                    print(f"Debug 44 - Sending command: {cmd.strip()}")
                    send_udp_command(cmd)
                case 'S1B1' | 'S2B1' | 'S3B1' | 'S4B1':
                    servo = int(event_key[1])
                    GUI_button_states[event_key] = not GUI_button_states[event_key]
                    CNT_button_states[event_key] = handle_servo_buttons(event, "ENABLE", "DISABLE", CNT_button_states[event_key], window)
                    window[event].update(
                        text='Enabled' if GUI_button_states[event_key] else 'Disabled',
                        button_color=('white', 'green') if GUI_button_states[event_key] else ('black', 'yellow')
                    )
                    window.refresh()
                    b1_cmd = f"S{servo}B1 ENABLE" if GUI_button_states[event_key] else f"S{servo}B1 DISABLE"
                    cmd = f"BOARD:{board_num};CMD:{b1_cmd}\n"
                    print(f"Debug 45 - Sending command: {cmd.strip()}")
                    send_udp_command(cmd)
                case 'S1B2' | 'S2B2' | 'S3B2' | 'S4B2':
                    servo = int(event_key[1])
                    GUI_button_states[event_key] = not GUI_button_states[event_key]
                    CNT_button_states[event_key] = handle_servo_buttons(event, "RUN", "STOP", CNT_button_states[event_key], window)
                    window[event].update(
                        text='STOP' if GUI_button_states[event_key] else 'RUN',
                        button_color=('black', 'gray') if GUI_button_states[event_key] else ('white', 'gray')
                    )
                    window.refresh()
                    b2_cmd = f"S{servo}B2 Start" if GUI_button_states[event_key] else f"S{servo}B2 STOP"
                    cmd = f"BOARD:{board_num};CMD:{b2_cmd}\n"
                    print(f"Debug 46 - Sending command: {cmd.strip()}")
                    send_udp_command(cmd)
                case _ if event_key.endswith('V_SPT_btn'):
                    servo = int(event_key[1])
                    current_value = setpoint_values[f'S{servo}V_SPT']
                    new_value = show_numeric_keypad(
                        f'Velocity Setpoint for Servo {servo}',
                        current_value,
                        0, 18000
                    )
                    if new_value is not None:
                        setpoint_values[f'S{servo}V_SPT'] = new_value
                        window[event].update(str(new_value))
                case _ if event_key.endswith('A_SPT_btn'):
                    servo = int(event_key[1])
                    current_value = setpoint_values[f'S{servo}A_SPT']
                    new_value = show_numeric_keypad(
                        f'Acceleration Setpoint for Servo {servo}',
                        current_value,
                        0, 18000
                    )
                    if new_value is not None:
                        setpoint_values[f'S{servo}A_SPT'] = new_value
                        window[event].update(str(new_value))
                case _ if event_key.endswith('P_SPT_btn'):
                    servo = int(event_key[1])
                    current_value = setpoint_values[f'S{servo}P_SPT']
                    new_value = show_numeric_keypad(
                        f'Position Setpoint for Servo {servo}',
                        current_value,
                        0, 18000
                    )
                    if new_value is not None:
                        setpoint_values[f'S{servo}P_SPT'] = new_value
                        window[event].update(str(new_value))
                case _ if event_key.endswith('B3'):
                    servo = int(event_key[1])
                    V_data = setpoint_values[f'S{servo}V_SPT']
                    A_data = setpoint_values[f'S{servo}A_SPT']
                    P_data = setpoint_values[f'S{servo}P_SPT']
                    cmd = f"BOARD:{board_num};CMD:S{servo}_Parameters:{V_data},{A_data},{P_data}\n"
                    print(f"Debug 47 - Sending command: {cmd.strip()}")
                    send_udp_command(cmd)
                    print(f"Debug 48 - Updated setpoints for S{servo}: V_SPT={V_data}, A_SPT={A_data}, P_SPT={P_data}")
                case _ if event_key.endswith('B4'):
                    servo = int(event_key[1])
                    cmd = f"BOARD:{board_num};CMD:S{servo}_ClearPosition\n"
                    print(f"Debug 49 - Sending clear position command: {cmd.strip()}")
                    send_udp_command(cmd)

    current_time = time.time()
    if current_time - last_request_time > MEDIUM_PRIORITY_UPDATE_INTERVAL:
        send_udp_command1("BOARD:1;CMD:REQUEST_VALUES\n")
        send_udp_command2("BOARD:2;CMD:REQUEST_VALUES\n")
        last_request_time = current_time

    gui_update_time = time.time()
    if gui_update_time - last_gui_update > LOW_PRIORITY_UPDATE_INTERVAL:
        try:
            for _ in range(BATCH_SIZE):
                message = message_queue.get_nowait()
                if DEBUG_LOW_PRIORITY:
                   print(f"Debug 51 - Processing message: {message}")
                if message.startswith("STATE_ENGINE:"):
                    process_response(message, "STATE_ENGINE:", window)
                elif message.startswith("BOARD:1;VALUES:"):
                    process_values_response(message[len("BOARD:1;"):], window, arduino_values_1, 'B1_')
                elif message.startswith("BOARD:2;VALUES:"):
                    process_values_response(message[len("BOARD:2;"):], window, arduino_values_2, 'B2_')
                elif message.startswith("SETPOINTS:"):
                    process_response(message, "SETPOINTS:", window)
                elif message.startswith("BUTTON_STATES:"):
                    process_response(message, "BUTTON_STATES:", window)
        except queue.Empty:
            pass

        last_gui_update = current_time

udp_thread.stop()
udp_thread.join()
udp_sock.close()
window.close()