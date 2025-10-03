# Simple movements only, from android to arduino, 
# moving and update back to android, queuing up all the commands

# Any communication to arduino, in terms of movement, will be sent into a command queue in 
# to_arduino_process (to_arudino_message_deque), and the arduino will be reading from this queue
    # but only if the status is allowed to move, 
    # and the status will be updated by the arduino itself

# Also a control state in the raspi, to keep track who's controlling the robot

import traceback
import sys
import time
import ast
import collections
from datetime import datetime
from multiprocessing import Process, Value, Manager
from multiprocessing.managers import BaseManager

from src.Android_com import Android_communicator
from src.Arduino_com import Arduino_communicator
# from src.PseudoSTM_com import Arduino_communicator
# from src.Algorithm_com import Algorithm_communicator
from src.data_structure import IncomingMessage, OutgoingMessage, DequeProxy

from typing import List
from src.protocols import *

class DequeManager(BaseManager):
    pass

# class Status(object):
#     def __init__(self, status):
#         self._status = status
#         self._last_command = None

#     def set_state(self, status):
#         self._status = status
    
#     def set_last_command(self, last_command):
#         self._last_command = last_command
    
#     @property
#     def state(self):
#         return self._state
    
#     @property
#     def last_command(self):
#         return self._last_command
        
DequeManager.register('DequeProxy', DequeProxy,
                      exposed=['__len__', 'append', 'appendleft', 'popleft'])   

# DequeManager.register('Status', Status,
#                         exposed=['set_state', 'set_last_command', 'state', 'last_command'])

class AndroidMovement:
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
        self.android = Android_communicator()  # handles connection to Android
        
        self.manager = DequeManager()
        self.sub_manager = Manager()
        self.manager.start()

        # self.status = Value('s', 'Idle') # * status of the robot (0: Idle, 1: Mission)
        # self.last_command = Value('s', '') # * last command sent to the arduino
        self.status = self.sub_manager.dict({'state': 'Idle', 'last_command': ''})
        
        self.to_android_message_deque = self.manager.DequeProxy() # * queue for communicating
        self.to_arduino_message_deque = self.manager.DequeProxy() # * queue for communicating
        
        self.commands_queue = self.manager.DequeProxy() # * queue for commands within robot, firing commands to arduino
        self.feedback_queue = self.manager.DequeProxy() # * queue for feedback from arduino to the robot
        # ! we also need another commands queue for the algorithm to send commands to the robot, with higher priority


        self.read_arduino_process = Process(target=self._read_arduino)
        self.read_android_process = Process(target=self._read_android)
        
        self.to_arduino_write_process = Process(target=self._write_arduino)
        self.to_android_write_process = Process(target=self._write_android)
        # ! another process to handle the commands queue, controling the queue, and the status of the robot
        # ! the only one can access to to_arduino_message_deque with the commands from the commands_queue
        self.brain_process = Process(target=self._brain)
        
    def start(self):        
        try:
            self.arduino.connect()
            self.android.connect()

            print('Connected to Arduino and Android')
            
            self.read_arduino_process.start()
            self.read_android_process.start()
            self.to_arduino_write_process.start()
            self.to_android_write_process.start()
            self.brain_process.start()
            
            print('Started all processes: read-arduino, read-android, write, brain')
            print('Multiprocess communication session started')
            
        except Exception as error:
            print("Main process has died out")
            raise error

        self._allow_reconnection()

    def end(self):
        # children processes should be killed once this parent process is killed
        self.arduino.disconnect_all()
        self.android.disconnect_all()
        print('Multiprocess communication session ended')

    def _allow_reconnection(self):
        print('You can reconnect to RPi after disconnecting now')
        while True:
            try:
                if not self.read_arduino_process.is_alive():
                    self._reconnect_arduino()
                if not self.read_android_process.is_alive():
                    self._reconnect_android()
                if not self.to_arduino_write_process.is_alive():
                    self._reconnect_arduino()
                if not self.to_android_write_process.is_alive():
                    self._reconnect_android()
            except Exception as error:
                print("Error during reconnection: ",error)
                raise error

    def _reconnect_arduino(self):
        self.arduino.disconnect()
        
        self.read_arduino_process.terminate()
        self.to_android_write_process.terminate()
        self.to_android_write_process.terminate()
        self.brain_process.terminate()

        self.arduino.connect()

        self.read_arduino_process = Process(target=self._read_arduino)
        self.read_arduino_process.start()

        self.to_arduino_message_deque = Process(target=self._write_arduino)
        self.to_arduino_write_process.start()
        
        self.to_android_write_process = Process(target=self._write_android)
        self.to_android_write_process.start()
        
        self.brain_process = Process(target=self._brain)
        self.brain_process.start()

        print('Reconnected to Arduino')

    def _reconnect_android(self):
        self.android.disconnect()
        
        self.read_android_process.terminate()
        self.to_arduino_write_process.terminate()
        self.to_android_write_process.terminate()
        
        self.android.connect()
        
        self.read_android_process = Process(target=self._read_android)
        self.read_android_process.start()

        self.to_arduino_message_deque = Process(target=self._write_arduino)
        self.to_arduino_write_process.start()
        
        self.to_android_write_process = Process(target=self._write_android)
        self.to_android_write_process.start()

        print('Reconnected to Android')
    
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
                    data = 'LF090'
                elif data == AndroidToArduino.F:
                    # Forward
                    data = 'SF015'
                elif data == AndroidToArduino.FR:
                    data = 'RF090'
                elif data == AndroidToArduino.BL:
                    # Backward left
                    data = 'LB090'
                elif data == AndroidToArduino.B:
                    # Backward
                    data = 'SB015'
                elif data == AndroidToArduino.BR:
                    data = 'RB090'
                print(f"Sending Android to Arduino a command: {data}")
                self.commands_queue.append(data)
        
    def _brain(self):
        while True:
            try:
                if len(self.feedback_queue) > 0:
                    feedback = self.feedback_queue.popleft()
                    print("Feedback from arduino", feedback)
                    # if feedback == "A": # success
                    #     self.status["state"] = 'Idle'
                    # elif feedback == "0": # error
                    #     # ! Retry the last command
                    #     self.status["state"] = 'Idle'
                    #     self.commands_queue.appendleft(self.status["last_command"])
                
                if self.status["state"] == 'Idle':
                    if len(self.commands_queue) > 0:
                        print("There is a coming command in the queue and we are ready to execute it.")
                        command = self.commands_queue.popleft()
                        self.to_arduino_message_deque.append(command)
                        self.status["last_command"] = command
                        # self.status["state"] = 'Mission'
            
            except Exception as error:
                print('Process brain failed: ' + str(error))
                break
    
    # ! Read arduino
    def _read_arduino(self):
        while True:
            try:
                raw_message = self.arduino.read()
                if raw_message is None:
                    continue
                self.feedback_queue.append(raw_message.decode())
            except Exception as error:
                print(traceback.format_exc())
                print('Process read_arduino failed: ' + str(error))
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
    
    def _write_arduino(self):
        while True:
            try:
                # data from brain to arduino is different, brain acts like an interface with this
                if len(self.to_arduino_message_deque)>0:
                    message = self.to_arduino_message_deque.popleft()
                    self.arduino.write(message.encode())
                
            except Exception as error:
                print('Process write_target failed: ' + str(error))
                self.to_arduino_message_deque.appendleft(message)
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
				
