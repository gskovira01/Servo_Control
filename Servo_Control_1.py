import PySimpleGUI as sg
import serial
import time

# Initialize serial connection
serialInst = serial.Serial()
serialInst.baudrate = 9600
serialInst.port = 'COM10'
serialInst.open()
serialInst.reset_input_buffer()  # Clear the input buffer initially

low_limit = 0
high_limit = 6000

layout = [
    [sg.Push(), sg.Column(''), sg.Text(' Velocity', size=(12, 1)), sg.Text('Acceleration', size=(12, 1)), sg.Text(' Position', size=(14, 1)), sg.Text(' ', size=(8, 1))],
    [sg.Push(), sg.Column(''), sg.Text(f"({low_limit}-{high_limit})", size=(12, 1)), sg.Text(f"({low_limit}-{high_limit})", size=(12, 1)), sg.Text(f"({low_limit}-{high_limit})", size=(14, 1)), sg.Text(' ', size=(8, 1))],
    
    [sg.Text('Servo 1', size=(8, 1)),
     sg.Button('ENABLE', button_color=('white', 'green'), key='S1B1'),
     sg.Button('RUN', button_color=('white', 'red'), key='S1B2'),
     sg.Input('', p=30, enable_events=True, key='S1V'),
     sg.Input('', p=10, enable_events=True, key='S1A'),
     sg.Input('', p=20, enable_events=True, key='S1P'),
     sg.Button('OK', button_color=('white', 'blue'), key='S1B3')],

    [sg.Text('Servo 2', size=(8, 1)),
     sg.Button('ENABLE', button_color=('white', 'green'), key='S2B1'),
     sg.Button('RUN', button_color=('white', 'red'), key='S2B2'),
     sg.Input('', p=30, enable_events=True, key='S2V'),
     sg.Input('', p=10, enable_events=True, key='S2A'),
     sg.Input('', p=20, enable_events=True, key='S2P'),
     sg.Button('OK', button_color=('white', 'blue'), key='S2B3')],

    [sg.Text('Servo 3', size=(8, 1)),
     sg.Button('ENABLE', button_color=('white', 'green'), key='S3B1'),
     sg.Button('RUN', button_color=('white', 'red'), key='S3B2'),
     sg.Input('', p=30, enable_events=True, key='S3V'),
     sg.Input('', p=10, enable_events=True, key='S3A'),
     sg.Input('', p=20, enable_events=True, key='S3P'),
     sg.Button('OK', button_color=('white', 'blue'), key='S3B3')],

    [sg.Text('Servo 4', size=(8, 1)),
     sg.Button('ENABLE', button_color=('white', 'green'), key='S4B1'),
     sg.Button('RUN', button_color=('white', 'red'), key='S4B2'),
     sg.Input('', p=30, enable_events=True, key='S4V'),
     sg.Input('', p=10, enable_events=True, key='S4A'),
     sg.Input('', p=20, enable_events=True, key='S4P'),
     sg.Button('OK', button_color=('white', 'blue'), key='S4B3')],
    ]

window = sg.Window("Robo Input", layout,
                   default_element_size=(10, 5),
                   size=(700, 500),
                   text_justification='center',
                   auto_size_text=True,
                   auto_size_buttons=False,
                   default_button_element_size=(8, 3),
                   finalize=True)

# Initialize button states for Servo 1
window['S1B1'].update(disabled=False)
window['S1B2'].update(disabled=True)

recording = have_data = False
S1V_data = S1A_data = S1P_data = ""

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

def handle_servo_buttons(event, start_key, stop_key, command_on, command_off):
    global recording, have_data
    if event == start_key:
        window[start_key].update(disabled=True)
        window[stop_key].update(disabled=False)
        serialInst.write(command_on.encode('utf-8'))
        serialInst.flush()
        recording = True
    elif event == stop_key and recording:
        window[start_key].update(disabled=False)
        window[stop_key].update(disabled=True)
        serialInst.write(command_off.encode('utf-8'))
        serialInst.flush()
        recording = False
        have_data = True

while True:
    event, values = window.read(timeout=2000)  # Non-blocking read with timeout
    # print(event, values)

    if event == sg.WIN_CLOSED:
        break

    # Servo 1 Buttons
    handle_servo_buttons(event, 'S1B1', 'S1B2', "S1 ENABLE", "S1 RUN")
    S1V_data = validate_input(event, 'S1V', values,0,6000)
    S1A_data = validate_input(event, 'S1A', values,0,6000)
    S1P_data = validate_input(event, 'S1P', values,0,6000)

    if event == 'S1B3':
        data = f"{S1V_data},{S1A_data},{S1P_data}"
        full_data = f"S1_Parameters: {data}"
        time.sleep(0.1)  # Small delay to ensure data is processed
        print(full_data)
        serialInst.write(full_data.encode('utf-8'))
        serialInst.flush()

    # Servo 2 Buttons
    handle_servo_buttons(event, 'S2B1', 'S2B2', "S2 ENABLE", "S2 RUN")

    # Servo 3 Buttons
    handle_servo_buttons(event, 'S3B1', 'S3B2', "S3 ENABLE", "S3 RUN")

    # Servo 4 Buttons
    handle_servo_buttons(event, 'S4B1', 'S4B2', "S4 ENABLE", "S4 RUN")

    # Continuously monitor the serial port for incoming responses
    if serialInst.in_waiting > 0:
        time.sleep(0.1)  # Small delay before reading the response
        line = serialInst.readline().decode('utf-8').rstrip()
        print(line)
        print("Ready")

window.close()