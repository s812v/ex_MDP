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

from PIL import Image, ImageDraw

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

# if status is Finished then it can not go further or do anything

class CameraTest:
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
        self.imageserver = Imageserver_communicator()
        
        self.manager = DequeManager()
        self.sub_manager = Manager()
        self.manager.start()

        self.status = self.sub_manager.dict({'state': 'Idle', 'last_command': '', 'current_obs_idx': -1, 'obs_order': [], 'pause_positions': [],'path_hist': [], 'current_received': 0, "dummy_image": True})
        self.obs_order = self.sub_manager.list([])
        
        self.to_arduino_message_deque = self.manager.DequeProxy() # * queue for communicating
        self.to_imageserver_message_queue = self.manager.DequeProxy()
      
        self.image_queue = self.manager.DequeProxy([])
        self.commands_queue = self.manager.DequeProxy() # * queue for commands within robot, firing commands to arduino
        self.feedback_queue = self.manager.DequeProxy([]) # * queue for feedback from arduino to the robot
        # ! we also need another commands queue for the algorithm to send commands to the robot, with higher priority

        self.read_arduino_process = Process(target=self._read_arduino)
        self.read_imageserver_process = Process(target=self._read_imageserver)
        
        self.to_arduino_write_process = Process(target=self._write_arduino)
        self.to_imageserver_write_process = Process(target=self._write_imageserver)
        
        self.image_process = Process(target=self._image_process)
        self.brain_process = Process(target=self._brain)
        # self.hist_process = Process(target=self._hist)
        
    def start(self):        
        try:
            self.imageserver.connect()
            self.arduino.connect()
            print('Connected to Arduino and algorithm and server')
            
            self.read_arduino_process.start()
            self.read_imageserver_process.start()
            
            self.to_arduino_write_process.start()
            self.to_imageserver_write_process.start()
            
            self.brain_process.start()
            self.image_process.start()
            while True:
                takepic = input("Take a pic?")
                self.commands_queue.append("P")
            
            print('Started all processes: read-arduino, read-android, write, brain')
            print('Multiprocess communication session started')
            
        except Exception as error:
            print("Main process has died out")
            raise error
        self._allow_reconnection()

    def _allow_reconnection(self):
        print('You can reconnect to RPi after disconnecting now')
        while True:
            try:
                if not self.read_arduino_process.is_alive():
                    self._reconnect_arduino()
                if not self.read_imageserver_process.is_alive():
                    self._reconnect_imageserver()
                
                if not self.to_arduino_write_process.is_alive():
                    self._reconnect_arduino()
                if not self.to_imageserver_write_process.is_alive():
                    self._reconnect_imageserver()
            except Exception as error:
                print("Error during reconnection: ",error)
                raise error
    
    def _reconnect_arduino(self):
        self.arduino.disconnect()
        
        self.read_arduino_process.terminate()
        self.to_imageserver_write_process.terminate()
        self.brain_process.terminate()
        self.arduino.connect()
        self.read_arduino_process = Process(target=self._read_arduino)
        self.read_arduino_process.start()
        self.to_arduino_message_deque = Process(target=self._write_arduino)
        self.to_arduino_write_process.start()
        self.to_imageserver_write_process = Process(target=self._write_imageserver)
        self.to_imageserver_write_process.start()
        self.brain_process = Process(target=self._brain)
        self.brain_process.start()

        print('Reconnected to Arduino')
    
    def _reconnect_imageserver(self):
        self.imageserver.disconnect()
        
        self.read_imageserver_process.terminate()
        self.to_imageserver_write_process.terminate()
        self.brain_process.terminate()
        
        self.imageserver.connect()
        
        self.read_imageserver_process = Process(target=self._read_imageserver)
        self.read_imageserver_process.start()

        self.to_arduino_message_deque = Process(target=self._write_arduino)
        self.to_arduino_write_process.start()
        
        self.to_imageserver_write_process = Process(target=self._write_imageserver)
        self.to_imageserver_write_process.start()
        
        self.brain_process = Process(target=self._brain)
        self.brain_process.start()

        print('Reconnected to image server')
    
    def end(self):
        # children processes should be killed once this parent process is killed
        self.arduino.disconnect_all()
        self.imageserver.disconnect_all()
        print('Multiprocess communication session ended')

    def _routing(self, message: IncomingMessage):
        """ Routing IncomingMessage to the correct target queue with data structure OutgoingMessage

        Args:
            message (IncomingMessage): 
        """
        source_header = message.source_header
        target_header = message.target_header
        data_type = message.data_type
        data = message.data
        routed = False
        
        if source_header == RASPBERRY_HEADER:
            if target_header == IMAGESERVER_HEADER:
                if data_type == "Image":
                    # ! Sending image to image server
                    self.to_imageserver_message_queue.append(
                        OutgoingMessage(source_header=source_header,
                                        target_header=target_header,
                                        data_type=data_type,data=data))
                    routed = True
        
        if source_header == IMAGESERVER_HEADER:
            if target_header == RASPBERRY_HEADER:
                if data_type == "Detections":
                    # ! Passing image recognition server + current obs idx - > android
                    try:
                        data = data[1:-1] # remove square bracket
                        data = data.split(',')
                    except Exception as e:
                        print("Got error when try to interpret image detection result from image server to raspberry pi")
                    image_character = data[1]
                    print("recognized, ", image_character)
                    routed = True
        
        if not routed:
            print("Message not routed ", source_header, target_header, data_type, data)
        
    def _brain(self):
        # camera = None
        camera = PiCamera(resolution=(IMAGE_WIDTH, IMAGE_HEIGHT))  # '1920x1080'
        camera.iso = 400
        # camera.exposure_compensation = 8
        time.sleep(2)
        camera.shutter_speed = camera.exposure_speed
        camera.exposure_mode = "off"
        g = camera.awb_gains
        camera.awb_mode = "off"
        camera.awb_gains = g
        
        while True:
            try:
                # ! disabled this, cuz currently we don't have the feedback from the STM, we need a fixed period to unlock and locks
                if len(self.commands_queue) > 0:
                    print("There is a coming command in the queue and we are ready to execute it.")
                    command = self.commands_queue.popleft()
                    if command == 'P':
                        image = self._take_pic(camera)
                        self.image_queue.append(image)
            
            except Exception as error:
                print('Process brain failed: ' + str(error))
                break
    
    def _image_process(self):
        # send to algorithm IncomingMessage
        while True:
            try:
                if len(self.image_queue) > 0:
                    image = self.image_queue.popleft()
                    print("===== shape of image ====", image.shape, image.dtype)
                    image_str = image.tobytes()
                    data = IncomingMessage(
                        message=image_str,
                        from_outgoing=True,
                        source_header=RASPBERRY_HEADER,
                        target_header=IMAGESERVER_HEADER,
                        data_type="Image"
                    )
                    self._routing(data)
            
            except Exception as error:
                print("This is coming from 237")
                print(traceback.format_exc())
                print('Image processing failed: ' + str(error))
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

    def _read_imageserver(self):
        while True:
            try:
                raw_message = self.imageserver.read()
                if raw_message is None:
                    continue
                message = IncomingMessage(raw_message, IMAGESERVER_HEADER)
                self._routing(message)
                
            except Exception as error:
                print(traceback.format_exc())
                print('Process read_imageserver failed: ' + str(error))
                break
    
    def _write_arduino(self):
        while True:
            try:
                # data from brain to arduino is different, brain acts like an interface with this
                if len(self.to_arduino_message_deque)>0:
                    message = self.to_arduino_message_deque.popleft()
                    print("Sending to arduino the message in_write_arduino", message)
                    self.arduino.write(message.encode())
                
            except Exception as error:
                print('Process write_arduino failed: ' + str(error))
                self.to_arduino_message_deque.appendleft(message)
                break

    def _write_imageserver(self):
        while True:
            try:
                # data from brain to arduino is different, brain acts like an interface with this
                if len(self.to_imageserver_message_queue)>0:
                    message = self.to_imageserver_message_queue.popleft()
                    self.imageserver.write(message.encoded)
                
            except Exception as error:
                print('Process write image server failed: ' + str(error))
                self.to_imageserver_message_queue.appendleft(message)
                break
                
    def _take_pic(self, camera):
        try:
            start_time = datetime.now()
            rawCapture = PiRGBArray(camera)
            time.sleep(0.1)
            camera.capture(rawCapture, format=IMAGE_FORMAT)
            image = rawCapture.array
            print('Time taken to take picture: ' + str(datetime.now() - start_time) + 'seconds')

        except Exception as error:
            print('Taking picture failed: ' + str(error))

        return image