LOCALE = 'UTF-8'

#Android BT connection settings

RFCOMM_CHANNEL = 1
RPI_MAC_ADDR = 'a4:cf:99:73:d1:0c'
UUID = '00001801-0000-1000-8000-00805f9b34fb'
ANDROID_SOCKET_BUFFER_SIZE = 512

# Passive listening to algorithm and image server
WIFI_IP = '192.168.28.28'
WIFI_PORT = 1111
IMAGE_PORT = 1112
ALGORITHM_SOCKET_BUFFER_SIZE = 512

# Actively connecting to algorithm and image server
ALGORITHM_IP = '192.168.28.33'
ALGORITHM_PORT = 2222
IMAGESERVER_IP = '192.168.28.33'
IMAGESERVER_PORT = 2223

# Arduino USB connection settings
# SERIAL_PORT = '/dev/ttyACM0'
# Symbolic link to always point to the correct port that arduino is connected to
SERIAL_PORT = '/dev/ttyUSB0'
BAUD_RATE = 115200
