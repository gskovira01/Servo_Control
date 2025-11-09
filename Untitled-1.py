class SerialThread(threading.Thread):
    def __init__(self, serial_port, message_queue):
        super().__init__()
        self.serial_port = serial_port
        self.message_queue = message_queue
        self.running = True
        self._timeout = 1.0  # 1 second timeout
        
    def run(self):
        while self.running:
            try:
                if self.serial_port.in_waiting:
                    line = self.serial_port.readline(timeout=self._timeout).decode('utf-8').rstrip()
                    if line:
                        self.message_queue.put(line)
                else:
                    time.sleep(0.01)  # Prevent CPU hogging
            except Exception as