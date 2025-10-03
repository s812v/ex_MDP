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
from src.Algorithm_com import Algorithm_communicator
from src.Imageserver_com import Imageserver_communicator, Imageserver_communicator_server
from src.data_structure import IncomingMessage, OutgoingMessage, DequeProxy

from picamera import PiCamera
from picamera.array import PiRGBArray

from typing import List
from src.protocols import *

class DequeManager(BaseManager):
    pass

        
DequeManager.register('DequeProxy', DequeProxy,
                      exposed=['__len__', 'append', 'appendleft', 'popleft'])   


class MainTaskTestMinimal:
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
        
        self.manager = DequeManager()
        self.sub_manager = Manager()
        self.manager.start()

        self.status = self.sub_manager.dict({'state': 'Idle', 'last_command': '', 'current_obs_idx': -1, 'obs_order': [], 'path_hist': []})
        self.obs_order = self.sub_manager.list([])
        
        self.to_arduino_message_deque = self.manager.DequeProxy() # * queue for communicating
      
        
        self.commands_queue = self.manager.DequeProxy() # * queue for commands within robot, firing commands to arduino
        self.feedback_queue = self.manager.DequeProxy([]) # * queue for feedback from arduino to the robot
        # ! we also need another commands queue for the algorithm to send commands to the robot, with higher priority

        # commands = ['SF040', 'RF090', 'SF070', 'LB090', 'P', 'SF020', 'LB090', 'SF005', 'LB090', 'SB025', 'LB090', 'P', 'SB020', 'LF090', 'SF010', 'RF090', 'P', 'SB005', 'LF090', 'SF020', 'P', 'SB030', 'LB090', 'SF025', 'LB090', 'LB090', 'P', 'LF090', 'SF040', 'RB090', 'SB020', 'RB090', 'P', 'RF090', 'SB020', 'LF090', 'SF005', 'LF090', 'P', 'finish']
        commands = ['RF019', 'P', 'RB019', 'RF090', 'P', 'SB015', 'LF090', 'RF090', 'P', 'SF025', 'LB090', 'P', 'LF090', 'LF090', 'RF019', 'P', 'RB019', 'SF020', 'RB090', 'SF020', 'RF020', 'P', 'RB020', 'SF010', 'RB090', 'SF005', 'LB090', 'LF016', 'P', 'LB016', 'finish']
        for command in commands:
            if command != "finish" and command != "P":
                self.commands_queue.append(command)
        
        self.read_arduino_process = Process(target=self._read_arduino)
        
        self.to_arduino_write_process = Process(target=self._write_arduino)
        # ! another process to handle the commands queue, controling the queue, and the status of the robot
        # ! the only one can access to to_arduino_message_deque with the commands from the commands_queue
        self.brain_process = Process(target=self._brain)
        
    def start(self):        
        try:
            self.arduino.connect()
            self.read_arduino_process.start()
            self.to_arduino_write_process.start()
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
        print('Multiprocess communication session ended')

    def _allow_reconnection(self):
        print('You can reconnect to RPi after disconnecting now')
        while True:
            try:
                if not self.read_arduino_process.is_alive():
                    self._reconnect_arduino()
                
                if not self.to_arduino_write_process.is_alive():
                    self._reconnect_arduino()
            except Exception as error:
                print("Error during reconnection: ",error)
                raise error

    def _reconnect_arduino(self):
        self.arduino.disconnect()
        self.read_arduino_process.terminate()
        self.brain_process.terminate()
        self.arduino.connect()

        self.read_arduino_process = Process(target=self._read_arduino)
        self.read_arduino_process.start()

        self.to_arduino_message_deque = Process(target=self._write_arduino)
        self.to_arduino_write_process.start()
        
        self.brain_process = Process(target=self._brain)
        self.brain_process.start()
        

        print('Reconnected to Arduino')

    def _routing(self, message: IncomingMessage):
        """ Routing IncomingMessage to the correct target queue with data structure OutgoingMessage

        Args:
            message (IncomingMessage): 
        """
        source_header = message.source_header
        target_header = message.target_header
        data_type = message.data_type
        data = message.data

    def _brain(self):
        st_time = None
        while True:
            try:
                # ! disabled this, cuz currently we don't have the feedback from the STM, we need a fixed period to unlock and locks
                if len(self.feedback_queue) > 0:
                    feedback = self.feedback_queue.popleft()
                    print("Feedback from arduino", feedback)
                    if feedback == "A": # success
                        self.status["state"] = 'Idle'
                    elif feedback == "0": # error
                    #     # ! Retry the last command
                        self.status["state"] = 'Idle'
                        self.commands_queue.appendleft(self.status["last_command"])
                
                if self.status["state"] == 'Idle':
                    if len(self.commands_queue) > 0:
                        print("There is a coming command in the queue and we are ready to execute it.")
                        command = self.commands_queue.popleft()
                        if command == 'P':
                            # pausing
                            self.status["current_obs_idx"] = self.status["current_obs_idx"] + 1
                            print("Taking image for ", self.status["current_obs_idx"], " obstacle")
                            image = self._take_pic()
                        else:
                            self.to_arduino_message_deque.append(command)
                            self.status["last_command"] = command
                            self.status["state"] = 'Mission'
            
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
                print("Arduino sending", raw_message)
                # TODO: need to enable this to get feedback
                self.feedback_queue.append(raw_message.decode())
                print(len(self.feedback_queue))
            except Exception as error:
                print(traceback.format_exc())
                print('Process read_arduino failed: ' + str(error))
                break    


    def _write_arduino(self):
        while True:
            try:
                # data from brain to arduino is different, brain acts like an interface with this
                if len(self.to_arduino_message_deque)>0:
                    message = self.to_arduino_message_deque.popleft()
                    self.arduino.write(message.encode())
                
            except Exception as error:
                print('Process write_arduino failed: ' + str(error))
                self.to_arduino_message_deque.appendleft(message)
                break