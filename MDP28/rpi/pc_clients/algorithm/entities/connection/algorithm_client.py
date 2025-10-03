import pickle
import socket


class AlgorithmClient:
    """
    Used for as a client actively connect to rasp
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
            if data_type == "Targets":
                data_str = '['
                for i, xy in enumerate(data):
                    data_str += '['
                    data_str += str(xy[0])
                    data_str += ','
                    data_str += str(xy[1])
                    data_str += ']'
                    if i != len(data) - 1:
                        data_str += ','
                data_str += ']'
                message = target + '|' + data_type + '|' + data_str
                print("Sending targets", message)
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
        d=self.socket.recv(2048)
        return d

    def close(self):
        self.socket.close()

