import threading
import time

def worker():
    print("Thread started")
    time.sleep(5)
    print("Thread finished")

# Create a thread
thread = threading.Thread(target=worker)

# Start the thread
thread.start()

# Check if the thread is running
while thread.is_alive():
    print("Thread is running")
    time.sleep(1)

print("Thread has finished")