import pickle
import socket
import ast

class PC_clinet:
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

    def send_message(self, target, data_type, data):
        message = None
        if target == "RPI":
            if data_type == "ACK":
                message = target + '|' + data_type + '|'
                
        self.socket.sendall(message)

    def receive_data(self):
        # receive image data and recognition as well
        d=self.socket.recv(2048)
        if d is None:
            return None, None, None
        d = d.decode().split('|')
        header, data_type, data = d
        if header == 'RPI':
            if data_type == 'Image':
                return header, data_type, data
                
    def close(self):
        self.socket.close()

    def settimeout(self, time):
        self.socket.settimeout(time)
        
if __name__ == "__main__":
    RPI_HOST = "192.168.28.28"
    RPI_PORT = "1111"
    print(f"Attempting to connect to {RPI_HOST}:{RPI_PORT}")
    client = RPiClient(RPI_HOST, RPI_PORT)
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
    print("Waiting to receive obstacle data from RPi...")
    client.settimeout(10)  # Set timeout to 10 seconds
    while True:
        try:
            header, data_type, image = client.receive_data()
            if header is not None:
                break
        except Exception as e:
            print(e)
            pass
    print("Receiving image from RPi", image)
        