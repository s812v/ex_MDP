import pickle
import socket


class AlgorithmCommunicator:
    """
    Used for as a client actively connect and passively connect to raspi
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
        if target == "RSP":
            if data_type == "ACK":
                message = target + '|' + data_type + '|'
                message = message.encode()
        
        if target == "RSP":
            if data_type == "Detections":
                if len(data) == 0:
                    message = target + '|' + data_type + '|' + '[1,-1]'
                    message = message.encode()
                else:
                    # class_name = classNames.index(data[0]["class_name"])
                    class_name = data[0]["class_name"]
                    class_name = str(class_name)
                    message = target + '|' + data_type + '|' + '[1,' + class_name + ']'
                    message = message.encode()
                    
        if target == "ARD":
            if data_type == "Commands":
                data = '[' + ', '.join(data) + ']'
                message = target + '|' + data_type + '|' + data
                message = message.encode()
        
        if target == "RSP":
            if data_type == "ObsOrder":
                data = [str(i) for i in data]
                data = '[' + ', '.join(data) + ']'
                message = target + '|' + data_type + '|' + data
                message = message.encode()
                
        self.socket.sendall(message)

    def receive_data(self):
        d=self.socket.recv(2048)
        return d

    def close(self):
        self.socket.close()

