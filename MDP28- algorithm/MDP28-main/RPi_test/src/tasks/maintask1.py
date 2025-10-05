import traceback
import sys
import time
import ast
import collections
from datetime import datetime
from multiprocessing import Process, Value
from multiprocessing.managers import BaseManager

from src.Android_com import Android_communicator
from src.Arduino_com import Arduino_communicator
from src.Algorithm_com import Algorithm_communicator
from src.data_structure import IncomingMessage, OutgoingMessage, DequeProxy

from typing import List
from src.protocols import *

class CommandsQueue(object):
    def __init__(self, commands: List[OutgoingMessage]):
        self.deque = collections.deque(commands)
    def __len__(self):
        return self.deque.__len__()
    def appendleft(self, x):
        self.deque.appendleft(x)
    def append(self, x):
        self.deque.append(x)
    def popleft(self):
        return self.deque.popleft()
    def front(self):
        return self.deque[0]

class Status(object):
    def __init__(self, status):
        self._status = status
        self._last_command = None

    def set_state(self, status):
        self._status = status
    
    def set_last_command(self, last_command):
        self._last_command = last_command
    
    @property
    def state(self):
        return self._state
    
    @property
    def last_command(self):
        return self._last_command

class DequeManager(BaseManager):
    pass
        
DequeManager.register('DequeProxy', DequeProxy,
                      exposed=['__len__', 'append', 'appendleft', 'popleft'])   
DequeManager.register('Status', Status, 
                      exposed=['set_state', 'state', 'last_command', 'set_last_command'])
class MultiProcessComms:
    """
    This class handles multi-processing communications between Arduino, Algorithm and Android.
    """
    def __init__(self, image_processing_server_url: str=None):
        """
        Instantiates a MultiProcess Communications session and set up the necessary variables.

        Upon instantiation, RPi begins connecting to
        - Arduino
        - Algorithm
        - Android
        in this exact order.

        Also instantiates the queues required for multiprocessing.
        """
        print('Initializing Multiprocessing Communication')

        self.arduino = Arduino_communicator()  # handles connection to Arduino
        self.algorithm = Algorithm_communicator()  # handles connection to Algorithm
        self.android = Android_communicator()  # handles connection to Android
        
        self.manager = DequeManager()
        self.manager.start()

        # messages from Arduino, Algorithm and Android are placed in this queue before being read
        self.message_deque = self.manager.DequeProxy()
        self.commands_queue = self.manager.CommandsQueue([])
        self.status = self.manager.Status("Start")
        
        self.to_android_message_deque = self.manager.DequeProxy()

        # ! TODO: enable arduino
        self.read_arduino_process = Process(target=self._read_arduino)
        self.read_algorithm_process = Process(target=self._read_algorithm)
        self.read_android_process = Process(target=self._read_android)
        
        self.write_process = Process(target=self._write_target)
        self.write_android_process = Process(target=self._write_android)
        
        self.firing_commands_process = Process(target=self._firing_commands_process)
        
        

        self.dropped_connection = Value('i',0) # 0 - arduino, 1 - algorithm
        
    def start(self):        
        try:
            # ! TODO: enable arduino
            self.arduino.connect()
            self.algorithm.connect()
            self.android.connect()

            print('Connected to Arduino, Algorithm and Android')
            
            # ! TODO: enable arduino
            self.read_arduino_process.start()
            self.read_algorithm_process.start()
            self.read_android_process.start()
            self.write_process.start()
            self.write_android_process.start()
            self.firing_commands_process.start()
            
            print('Started all processes: read-arduino, read-algorithm, read-android, write, image')

            print('Multiprocess communication session started')
            
        except Exception as error:
            print("Main process has died out")
            raise error

        self._allow_reconnection()

    def end(self):
        # children processes should be killed once this parent process is killed
        self.arduino.disconnect_all()
        self.algorithm.disconnect_all()
        self.android.disconnect_all()
        print('Multiprocess communication session ended')

    def _allow_reconnection(self):
        print('You can reconnect to RPi after disconnecting now')

        while True:
            try:
                # ! Enable arduino
                if not self.read_arduino_process.is_alive():
                    self._reconnect_arduino()
                    
                if not self.read_algorithm_process.is_alive():
                    self._reconnect_algorithm()
                    
                if not self.read_android_process.is_alive():
                    self._reconnect_android()
                    
                if not self.write_process.is_alive():
                    # ! Enable arduno
                    if self.dropped_connection.value == 0:
                        self._reconnect_arduino()
                    elif self.dropped_connection.value == 1:
                        self._reconnect_algorithm()
                    if self.dropped_connection.value == 1:
                        self._reconnect_algorithm()
                        
                if not self.write_android_process.is_alive():
                    self._reconnect_android()
                    
            except Exception as error:
                print("Error during reconnection: ",error)
                raise error

    def _reconnect_arduino(self):
        self.arduino.disconnect()
        
        self.read_arduino_process.terminate()
        self.write_process.terminate()
        self.write_android_process.terminate()

        self.arduino.connect()

        self.read_arduino_process = Process(target=self._read_arduino)
        self.read_arduino_process.start()

        self.write_process = Process(target=self._write_target)
        self.write_process.start()
        
        self.write_android_process = Process(target=self._write_android)
        self.write_android_process.start()

        print('Reconnected to Arduino')

    def _reconnect_algorithm(self):
        self.algorithm.disconnect()
        
        self.read_algorithm_process.terminate()
        self.write_process.terminate()
        self.write_android_process.terminate()

        self.algorithm.connect()

        self.read_algorithm_process = Process(target=self._read_algorithm)
        self.read_algorithm_process.start()

        self.write_process = Process(target=self._write_target)
        self.write_process.start()
        
        self.write_android_process = Process(target=self._write_android)
        self.write_android_process.start()

        print('Reconnected to Algorithm')

    def _reconnect_android(self):
        self.android.disconnect()
        
        self.read_android_process.terminate()
        self.write_process.terminate()
        self.write_android_process.terminate()
        
        self.android.connect()
        
        self.read_android_process = Process(target=self._read_android)
        self.read_android_process.start()

        self.write_process = Process(target=self._write_target)
        self.write_process.start()
        
        self.write_android_process = Process(target=self._write_android)
        self.write_android_process.start()

        print('Reconnected to Android')
    
    def _firing_commands_process(self):
        while True:
            if self.status.state == 'Mission':
                command_message = self.commands_queue[0]
                self.commands_queue.popleft()
                self._routing(command_message)
                self.status.set_state('Executing')
    
    def _routing(self, message: IncomingMessage):
        """ Routing IncomingMessage to the correct target queue with data structure OutgoingMessage

        Args:
            message (IncomingMessage): 
        """
        source_header = message.source_header
        target_header = message.target_header
        data_type = message.data_type
        data = message.data
        
        if source_header == ANDROID_HEADER:
            if target_header == ARDUINO_HEADER:  # Send the basic commands to the Arduino
                # print(f"{data_type}, Sending Android to Arduino: ")
                if data == AndroidToArduino.FL: 
                    # Forward Left
                    data = 'LF000'
                elif data == AndroidToArduino.F:
                    # Forward
                    data = 'SF015'
                elif data == AndroidToArduino.FR:
                    data = 'RF000'
                elif data == AndroidToArduino.BL:
                    # Backward left
                    data = 'LB090'
                elif data == AndroidToArduino.B:
                    # Backward
                    data = 'SB015'
                elif data == AndroidToArduino.BR:
                    data = 'RB090' 
                self.message_deque.append(OutgoingMessage(source_header, target_header, data_type, data))
            if target_header == ALGORITHM_HEADER: # Send the arena data to the algorithm
                # need to interpret the arena and send to the algorithm
                # print(f"{data_type}, Sending Android to Algorithm: ")
                self.message_deque.append(OutgoingMessage(source_header, target_header, data_type, data))
        if source_header == ALGORITHM_HEADER:
            if target_header == ARDUINO_HEADER: # Send the commands to the Arduino
                self.message_deque.append(OutgoingMessage(source_header, target_header, data_type, data))
        
        if source_header == ARDUINO_HEADER:
            if target_header == RASPBERRY_HEADER:
                # notifying the ardunino excuted successfully or not
                if data_type == "Successful":
                    self.status.set_state('Mission')
                elif data_type == "Error":
                    # ! Retry
                    self.status.set_state('Mission')
                    self.commands_queue.appendleft(self.status.last_command)
                else:
                    print("Got error when communicating with STM32, with raspberrypi, line 277")  
        # manage data 
    
    # ! Read arduino
    def _read_arduino(self):
        while True:
            try:
                raw_message = self.arduino.read()
                if raw_message is None:
                    continue
                message = IncomingMessage(raw_message, ARDUINO_HEADER)
                self._routing(message)
            except Exception as error:
                print(traceback.format_exc())
                print('Process read_arduino failed: ' + str(error))
                break    

    # ! Read algorithm
    def _read_algorithm(self):
        while True:
            try:
                raw_message = self.algorithm.read()
                if raw_message is None:
                    continue
                message = IncomingMessage(raw_message, ALGORITHM_HEADER)
                if message.target_header == ARDUINO_HEADER:
                    if message.data_type == "Commands":
                        # ! Need to treat this differently, put the commands into a queue, not 
                        # ! routing the message imidiately to Arduino
                        # self.commands_queue
                        # append OutgoingMessage
                        # message.data -> string, evaluate it to list of string
                        commands_data = ast.literal_eval(message.data)
                        for command_str in commands_data:
                            outgoing_message = OutgoingMessage(
                                target_header=ARDUINO_HEADER,
                                source_header=ALGORITHM_HEADER,
                                data_type='Command',
                                data=command_str
                            )
                            self.commands_queue.append(outgoing_message)
                        self.status.set_state("Mission")
                else:
                    self._routing(message)
            except Exception as error:
                print(traceback.format_exc())
                print('Process read_algorithm failed: ' + str(error))
                break

    # ! Read android
    def _read_android(self):
        while True:
            try:
                raw_message = self.android.read()
                if raw_message is None:
                    continue
                message = IncomingMessage(raw_message, ANDROID_HEADER)
                self._routing(message)
                
            except Exception as error:
                print(traceback.format_exc())
                print('Process read_android failed: ' + str(error))
                break
    
    def _write_target(self):
        while True:
            target_header = None
            try:
                if len(self.message_deque)>0:
                    message = self.message_deque.popleft()
                    target_header = message.target_header 
                    # message will ignore the target_header, only encode and send the source
                    if message.target_header == ARDUINO_HEADER:
                            # ! sending to arduino, but in raws, only the data
                            self.arduino.write(message.data.encode())
                        
                    elif message.target_header == ALGORITHM_HEADER:
                            self.algorithm.write(message.encoded)
                    else:
                        print("Invalid header", message.header)
                
            except Exception as error:
                print('Process write_target failed: ' + str(error))

                if target_header == ARDUINO_HEADER:
                    self.dropped_connection.value = 0

                elif target_header == ALGORITHM_HEADER:
                    self.dropped_connection.value = 1
                    
                self.message_deque.appendleft(message)
                break
                
    def _write_android(self):
        while True:
            try:
                if len(self.to_android_message_deque)>0:
                    message = self.to_android_message_deque.popleft()
                    self.android.write(message.encoded)
                
            except Exception as error:
                print('Process write_android failed: ' + str(error))
                self.to_android_message_deque.appendleft(message)
                break
				
