import PySimpleGUI as sg # type: ignore
import socket
import threading
import queue
import time
import sys

# Global state
state_engine_step = 0
DEBUG = False  # Global debug flag to control debug output
DEBUG00 = False  # Global debug flag to control debug output
DEBUG_LOW_PRIORITY = False  # Global debug flag to control debug output
DEBUG_MEDIUM_PRIORITY = False  # Global debug flag to control debug output
DEBUG_HIGH_PRIORITY = False  # Global debug flag to control debug output

# Constants
WINDOW_READ_TIMEOUT = 100  # Window read timeout in milliseconds
MEDIUM_PRIORITY_UPDATE_INTERVAL = .25  # Reduced Arduino polling (sec)
LOW_PRIORITY_UPDATE_INTERVAL = .5  # Faster display updates (sec)
BATCH_SIZE = 10
DEBOUNCE_INTERVAL = 0.5  # Debounce interval in seconds

# --- UDP CONFIGURATION ---
CLEARCORE_IP = '192.168.1.171'   # Set to your ClearCore's IP
CLEARCORE_PORT = 8888            # Set to your ClearCore's UDP port
LOCAL_PORT = 8889                # Local port for receiving responses

# --- UDP SOCKET SETUP ---
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
udp_sock.bind(('', LOCAL_PORT))
udp_sock.settimeout(0.1)  # Non-blocking

# Thread-safe queue for storing incoming UDP messages to be processed by the main thread
message_queue = queue.Queue()

# --- UDP Receiver Thread ---

class UDPReceiverThread(threading.Thread):
    def __init__(self, udp_sock, message_queue):
        super().__init__()
        self.udp_sock = udp_sock
        self.message_queue = message_queue
        self.running = True

    def run(self):
        while self.running:
            try:
                data, _ = self.udp_sock.recvfrom(1024)
                message = data.decode('utf-8').strip()
                if message:
                    self.message_queue.put(message)
            except socket.timeout:
                continue
            except ValueError as e:
                print(f"UDP socket closed (ValueError): {e}")
                self.running = False
            except OSError as e:
                print(f"UDP socket closed or error: {e}")
                self.running = False
            except Exception as e:
                print(f"UDP receive error: {e}")
                self.running = False

    def stop(self):
        self.running = False

udp_thread = UDPReceiverThread(udp_sock, message_queue)
udp_thread.start()

# --- Helper to send UDP command ---
def send_udp_command(cmd):
    udp_sock.sendto(cmd.encode('utf-8'), (CLEARCORE_IP, CLEARCORE_PORT))

last_request_time = time.time()

print("Script started", flush=True)
while True:
    print("Debug 50 - Loop", flush=True)
    # Background Tasks - Only process if no pending events
    current_time = time.time()
    
    # Medium Priority - Process Messages (reduced frequency)
    if current_time - last_request_time > MEDIUM_PRIORITY_UPDATE_INTERVAL:
        print("Debug 50 - Sending CMD:REQUEST_VALUES to Arduino")   
        time.sleep(2.0)
        send_udp_command("CMD:REQUEST_VALUES\n")
        # (UDP does not need flush)
        last_request_time = current_time

        try:
            # Example: process messages from the queue
            while not message_queue.empty():
                msg = message_queue.get_nowait()
                print(f"Received message: {msg}")
        except queue.Empty:
            pass

# Cleanup
