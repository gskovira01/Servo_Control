import PySimpleGUI as sg # type: ignore
import serial # type: ignore

# Serial port configuration
ser = serial.Serial('COM7', 9600)  # Replace 'COM3' with your Arduino's port

layout = [
    [sg.Text('Arduino Control')],
    [sg.Button('Turn LED ON'), sg.Button('Turn LED OFF')],
    [sg.Output(size=(40, 10))]
]

window = sg.Window('Arduino GUI', layout)

while True:
    event, values = window.read()

    if event == sg.WINDOW_CLOSED:
        break

    if event == 'Turn LED ON':
        ser.write(b'1')  # Send '1' to turn LED on
        window['Output'].print('LED ON')

    if event == 'Turn LED OFF':
        ser.write(b'0')  # Send '0' to turn LED off
        window['Output'].print('LED OFF')

ser.close()
window.close()