import pickle
import socket
import ast
import time

class PseudoArduinoClinet:
    """
    Used for connecting to...
    """
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket()
        self.socket.settimeout(5)

    def connect(self):
        self.socket.connect((self.host, self.port))

    def send_message(self, message):
        message = message.encode()
        self.socket.sendall(message)

    def receive_data(self):
        # receive image data and recognition as well
        d=self.socket.recv(2048)
        if d is None:
            return None
        d = d.decode()
        return d
                
    def close(self):
        self.socket.close()

    def settimeout(self, time):
        self.socket.settimeout(time)

def execute(command):
    if command == "H" or command == "I":
        return ""
    i = input(f"Is this commmand {command} executed successfully (y/n)")
    time.sleep(1)
    if i == "y":
        return "A"
    else:
        return "0"

if __name__ == "__main__":
    RPI_HOST = "192.168.28.28"
    RPI_PORT = 1113
    print(f"Attempting to connect to {RPI_HOST}:{RPI_PORT}")
    client = PseudoArduinoClinet(RPI_HOST, RPI_PORT)
    # Wait to connect to RPi.
    while True:
        try:
            client.connect()
            break
        except OSError:
            pass
        except KeyboardInterrupt:
            client.close()
            sys.exit(1)
    
    print(f"Connected to {RPI_HOST}:{RPI_HOST}")
    # Listen to image, predict the image, then bounding box,
    # then send back the ack
    print("Waiting to receive commands from RPi...")
    client.settimeout(10)  # Set timeout to 10 seconds
    while True:
        try:
            buffer = client.receive_data()
            if buffer is None:
                continue
            print("Received command, ", buffer)
            flag = execute(buffer)
            if flag != "":
                client.send_message(flag)
        except Exception as e:
            print(e)
            pass
        