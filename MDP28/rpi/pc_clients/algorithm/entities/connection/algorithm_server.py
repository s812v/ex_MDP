import socket
import pickle


class AlgorithmServer:
    """
    Used as the server in the Algorithm
    """
    def __init__(self, local_host, local_port):
        self.local_host = local_host
        self.local_port = local_port
        self.local_socket = socket.socket()

        self.__data = []
        self.conn, self.address = None, None

    def start(self):
        print(f"Creating server at {self.host}:{self.port}")
        self.local_socket.bind((self.local_host, self.local_port))
        self.local_socket.listen()
        print("Listening for connection...")

        self.remote_socket, self.remote_address = self.local_socket.accept()
        print(f"Connection from {self.remote_address}")

    def send_message(self, target, data_type, data):
        message = None
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
        
        if target == "RSP":
            if data_type == "PathHist":
                # data_str = "["
                # for l in data:
                #     data += "["
                #     for tup in l:
                #         tup = list(tup)
                #         for idx in range(len(tup)):
                #             tup[idx] = str(tup[idx])
                #         data += '('
                #         data += ','.join(tup)
                #         data += '),'
                #     data += "],"
                # data_str += "]"
                
                new_data = []
                for l in data:
                    for tup in l:
                        new_data.append(tup)
                
                new_data = [new_data[i] for i in range(0, len(new_data), 3)]
                data_str = "["
                for i in new_data:
                    # tuple
                    data_str += '['
                    data_str += ",".join([str((j//10+1)) if idx < 2 else "'"+j+"'" for idx, j in enumerate(i)])
                    data_str += '],'
                # new_data = [str(j) for i in new_data for j in i]
                data_str = list(data_str)
                data_str[-1] = ']'
                data_str = "".join(data_str)
                
                # data_str = ", ".join(new_data)
                
                message = target + '|' + data_type + '|' + data_str
                print("sent, ", message)
                message = message.encode()
                
        self.socket.sendall(message)

    def receive_data(self):
        d=self.local_socket.recv(2048)
        return d

    def close(self):
        self.local_socket.close()
        
    def restart(self):
        pass
