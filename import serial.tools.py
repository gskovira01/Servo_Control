import serial

#ports = serial.tools.list_ports.comports()
serialInst = serial.Serial()
portsList = []


serialInst.baudrate = 9600
serialInst.port = 'COM7'
serialInst.open()

while True:
    command = input("Arduino Command (ON/OFF/exit): ")
    serialInst.write(command.encode('utf-8'))

    if command == 'exit':
        exit()