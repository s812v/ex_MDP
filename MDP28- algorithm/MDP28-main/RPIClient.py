import socket
import sys
import pickle

# Settings

PC_IP = "localhost"
PC_PORT = 4161
RPI_IP = "192.168.28.28"
RPI_PORT = 1111

class client(object):
    def __init__(self):
        # self.tcp_ip = "192.168.2.2" # Connecting to IP address of MDPGrp2
        self.tcp_ip = PC_IP
        self.port = PC_PORT
        self.conn = None
        self.client = None
        self.addr = None
        self.pc_is_connect = False

    def close_pc_socket(self):
        """
        Close socket connections
		"""
        if self.conn:
            self.conn.close()
            print("Closing server socket")
        if self.client:
            self.client.close()
            print("Closing client socket")
        self.pc_is_connect = False

    def pc_is_connected(self):
        """
		Check status of connection to PC
		"""
        return self.pc_is_connect

    def init_pc_comm(self):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect((self.tcp_ip, self.port))
        print("Connected! Connection address: ", self.addr)


    def write_to_PC(self, message):
        """
		Write message to PC
		"""
        try:
            data = pickle.dumps(message)
            self.conn.send(data)
        except TypeError:
            print("Error: Null value cannot be sent")


    def read_from_PC(self):
        """
		Read incoming message from PC
		"""
        try:
            pc_data = self.client.recv(2048)
            # print "Read [%s] from PC" %pc_data
            return pc_data
        except Exception as e:
            print("Error: %s " % str(e))
            print("Value not read from PC")


    def connect(self):
        self.socket.connect((self.host, self.port))


class server(object):
    def __init__(self):
        self.host = RPI_IP
        self.port = RPI_PORT
        self.socket = socket.socket()

        self.__data = []
        self.conn, self.address = None, None

    def start(self):
        print(f"Creating server at {self.host}:{self.port}")
        self.socket.bind((self.host, self.port))
        self.socket.listen()
        print("Listening for connection...")

        self.conn, self.address = self.socket.accept()
        print(f"Connection from {self.address}")

    def receive_data(self):
        assert self.conn is not None and self.address is not None
        d = self.conn.recv(2048)
        return pickle.loads(d)

    def close(self):
        print("Closing socket.")
        self.socket.close()


def estab_connections(obstacle_data):
    # global server
    global client

    data = []

    try:
        # print("Launching server")
        # server = server()
        # server.start()

        print("Launching client")
        client = client()
        client.init_pc_comm()
        client.write_to_PC(obstacle_data)

        # print("Waiting for commands from PC...")
        # data = server.receive_data()
        # print("Receiving commands:")

        if data is None:
            raise IOError("Data object is empty, quitting!")

        order = data[0]
        commands = data[1]

        return order, commands
    except Exception as e:
        client.close_pc_socket()
        server.close()
        raise e

if __name__ == "__main__":
    data_from_android = [[105, 75, 90, 0], [175, 25, 180, 1], [75, 125, 180, 2], [15, 185, 0, 3]]
    order, commands = estab_connections(data_from_android)
    print("order of obstacles: " + str(order))
    print("order of commands:" + str(commands))


