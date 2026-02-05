import socket
import wave
import threading

# Server IP and port
SERVER_IP = '192.168.4.2'  # Listen on all interfaces
SERVER_PORT = 12346

# WAV file settings
CHANNELS = 1  # Mono audio
SAMPLE_WIDTH = 2  # 16 bits -> 2 bytes
FRAME_RATE = 44100
OUTPUT_FILENAME = 'output_mono2.wav'

def handle_client_connection(client_socket, addr):
    print(f"Accepted connection from {addr}")

    # Start an interactive session with the user
    command_thread = threading.Thread(
        target=command_sender,
        args=(client_socket,)
    )
    command_thread.start()

    with wave.open(OUTPUT_FILENAME, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(SAMPLE_WIDTH)
        wf.setframerate(FRAME_RATE)

        try:
            while True:
                data = client_socket.recv(2048)
                if not data:
                    break
                wf.writeframes(data)
        except Exception as e:
            print(f"Exception: {e}")
        finally:
            client_socket.close()
            print(f"Connection from {addr} closed.")

def command_sender(client_socket):
    try:
        while True:
            cmd = input("Enter command (START/STOP/EXIT): ").strip().upper()
            if cmd == "START":
                client_socket.sendall(b"START\n")
                print("Sent START command.")
            elif cmd == "STOP":
                client_socket.sendall(b"STOP\n")
                print("Sent STOP command.")
            elif cmd == "EXIT":
                client_socket.sendall(b"STOP\n")
                print("Sent STOP command and closing connection.")
                client_socket.close()
                break
            else:
                print("Invalid command. Please enter START, STOP, or EXIT.")
    except Exception as e:
        print(f"Command sender exception: {e}")

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
