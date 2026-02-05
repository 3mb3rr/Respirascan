import socket
import csv
import threading
import json
import os
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import deque

# TCP server details
HOST = '192.168.0.101'  # Listen on the specified IP address
PORT = 12345           # Must match the port number used in the Arduino code

# Global lock for file writing (shared among all threads)
file_lock = threading.Lock()


# Shared buffers for live graphing
ax_buffer = deque(maxlen=100)
time_buffer = deque(maxlen=100)  # for x-axis

def get_csv_filename(device_id):
    """Return a filename for the given device ID."""
    return f"sensor_data_device_{device_id}.csv"

def write_row_for_device(row, lock):
    """Write a row to the CSV file corresponding to the device ID (first element in row)."""
    device_id = row[0]
    filename = get_csv_filename(device_id)
    with lock:
        file_exists = os.path.exists(filename)
        with open(filename, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            # If file doesn't exist, write header
            if not file_exists:
                writer.writerow(['device_id', 'timestamp', 'ax', 'ay', 'az', 'gx', 'gy', 'gz'])
            writer.writerow(row)

def handle_client(conn, addr):
    print(f"Connected by {addr}")
    conn.settimeout(10.0)  # Set a timeout for socket operations
    buffer = ''
    try:
        with conn:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                # Append received data to buffer
                buffer += data.decode('utf-8')
                # Process all complete lines (assuming each JSON message ends with a newline)
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    data_str = line.strip()
                    if not data_str:
                        continue
                    try:
                        # Parse the JSON data
                        json_data = json.loads(data_str)
                        # Extract required fields
                        device_id = json_data.get("device_id", "")
                        timestamp = json_data.get("timestamp", "")
                        acc = json_data.get("acc", {})
                        gyro = json_data.get("gyro", {})
                        ax = acc.get("x", "")
                        ay = acc.get("y", "")
                        az = acc.get("z", "")
                        gx = gyro.get("x", "")
                        gy = gyro.get("y", "")
                        gz = gyro.get("z", "")
                        # Build the CSV row
                        row = [device_id, timestamp, ax, ay, az, gx, gy, gz]
                        print(f"Received data from device {device_id}: {row}")
                        # Write the row into the corresponding CSV file
                        write_row_for_device(row, file_lock)
                    except json.JSONDecodeError:
                        print("Invalid JSON data received.")
    except socket.timeout:
        print("Connection timed out.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()
        print(f"Connection closed by {addr}")

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"Server listening on {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.daemon = True
            client_thread.start()
def live_plot():
    plt.style.use('ggplot')
    fig, ax = plt.subplots()
    line, = ax.plot([], [], lw=2)
    ax.set_xlabel('Time')
    ax.set_ylabel('ax (acceleration x)')
    ax.set_title('Live ax values')

    def update(frame):
        if len(time_buffer) > 0:
            line.set_data(time_buffer, ax_buffer)
            ax.relim()
            ax.autoscale_view()
        return line,

    ani = FuncAnimation(fig, update, interval=200)
    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    plot_thread = threading.Thread(target=live_plot)
    plot_thread.daemon = True
    plot_thread.start()

    start_server()
