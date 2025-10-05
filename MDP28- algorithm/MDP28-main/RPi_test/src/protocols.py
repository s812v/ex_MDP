'''
Communication protocols.
They are pre-defined so it allows all subsystems to know the common ways of communication
'''
IMAGE_WIDTH = 1024
IMAGE_HEIGHT = 1024
IMAGE_FORMAT='rgb'
MESSAGE_SEPARATOR = '|'.encode()
NEWLINE = '\n'.encode()

ANDROID_HEADER = 'AND'
ARDUINO_HEADER = 'ARD'
ALGORITHM_HEADER = 'ALG'
RASPBERRY_HEADER = 'RSP'
ALL_HEADERS = [
    ANDROID_HEADER,
    ARDUINO_HEADER,
    ALGORITHM_HEADER,
    RASPBERRY_HEADER
]
# HEADER (heading to) | TYPE | DATA | END

class Status:
    IDLE = 'idle'.encode()

# ! Android connections
class AndroidToArduino:
    # data
    FL = 'Q' # Forward Left
    F = 'W' # Forward
    FR = 'E' # Forward Right
    BL = 'A' # Backward Left
    B = 'S' # Backward
    BR = 'D' # Backward Right
    
    
    
class AndroidToRaspberry:
    # Live location in the android context
    pass
    
    
class RaspberryToAndroid:
    # Live location in the raspberry pi context
    MOVING_STATUS = 'MOVING'

    STATES = [

    ]

class AndroidToAlgorithm:
    SEND_ARENA = 'SendArena'

# ! Algorithm connections
# class AlgorithmToArduino:
    
