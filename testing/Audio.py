import socket
import wave
import threading
import pyaudio

# Server IP and Port
SERVER_IP = '192.168.0.152'
SERVER_PORT = 12345

# Audio settings
CHANNELS = 1  # Stereo (if using 2 mics)
SAMPLE_WIDTH = 2  # 16-bit
FRAME_RATE = 44100
OUTPUT_FILENAME = 'output.wav'

# Initialize PyAudio for playback
p = pyaudio.PyAudio()
stream = p.open(format=p.get_format_from_width(SAMPLE_WIDTH),
                channels=CHANNELS,
                rate=FRAME_RATE,
                output=True)

def handle_client_connection(client_socket, addr):
    print(f"Accepted connection from {addr}")
    with wave.open(OUTPUT_FILENAME, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(SAMPLE_WIDTH)
        wf.setframerate(FRAME_RATE)
        
        try:
            while True:
                data = client_socket.recv(2048)
                if not data:
                    break
                wf.writeframes(data)  # Save to file
                stream.write(data)  # Real-time playback
        except Exception as e:
            print(f"Exception: {e}")
        finally:
            client_socket.close()
            print(f"Connection from {addr} closed.")

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((SERVER_IP, SERVER_PORT))
    server.listen(1)
    print(f"Server listening on {SERVER_IP}:{SERVER_PORT}")

    while True:
        client_sock, addr = server.accept()
        client_handler = threading.Thread(
            target=handle_client_connection,
            args=(client_sock, addr)
        )
        client_handler.start()

if __name__ == "__main__":
    main()
