import serial # type: ignore
import threading

class SerialThread(threading.Thread):
    def __init__(self, port, baudrate=9600, timeout=1):
        threading.Thread.__init__(self)
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
        self.running = True
        self.data_received = []

    def run(self):
        while self.running:
            if self.ser.in_waiting > 0:
                data = self.ser.readline().decode('utf-8').rstrip()
                self.data_received.append(data)

    def stop(self):
        self.running = False
        self.ser.close()

    def get_data(self):
        temp = self.data_received[:]
        self.data_received.clear()
        return temp

if __name__ == "__main__":
    port = "COM10"  # Replace with your Arduino's port
    baudrate = 9600

    serial_thread = SerialThread(port, baudrate)
    serial_thread.start()

    try:
        while True:
            data = input("Enter data to send to Arduino: ")
            serial_thread.ser.write((data + "\n").encode('utf-8'))

            received_data = serial_thread.get_data()
            if received_data:
                print("Data received from Arduino:", received_data)

    except KeyboardInterrupt:
        print("Exiting...")
        serial_thread.stop()
        serial_thread.join()