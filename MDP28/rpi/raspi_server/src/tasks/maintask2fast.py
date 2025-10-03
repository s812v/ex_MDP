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
# from src.Arduino_com import Arduino_communicator
from src.PseudoSTM_com import Arduino_communicator
from src.Algorithm_com import Algorithm_communicator
from src.Imageserver_com import Imageserver_communicator, Imageserver_communicator_server
from src.data_structure import IncomingMessage, OutgoingMessage, DequeProxy

from picamera import PiCamera
from picamera.array import PiRGBArray

from typing import List
from src.protocols import *

from PIL import Image, ImageDraw

import os

print(os.getcwd())
assert os.path.exists("/home/pi/Documents/MDP28/raspi_server/model/best_leftright.pt"), "Model weights missing! Please upload"
from ultralytics import YOLO
import cv2
import numpy as np
import math
import matplotlib.pyplot as plt

class DequeManager(BaseManager):
    pass

num_img = 0
model = YOLO("/home/pi/Documents/MDP28/raspi_server/model/best_leftright.pt")
classNames = ['L', 'R']
FONT = cv2.FONT_HERSHEY_SIMPLEX
COLOR = (255, 0, 0)
FONT_SCALE = 2e-3  # Adjust for larger font size in all images
THICKNESS_SCALE = 5e-3  # Adjust for larger thickness in all images
        
DequeManager.register('DequeProxy', DequeProxy,
                      exposed=['__len__', 'append', 'appendleft', 'popleft'])   

# DequeManager.register('Status', Status,
#                         exposed=['set_state', 'set_last_command', 'state', 'last_command'])

# if status is Finished then it can not go further or do anything

class MainTask2Fast:
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

        self.status = self.sub_manager.dict({'state': 'Idle'})
        self.to_arduino_message_deque = self.manager.DequeProxy() # * queue for communicating
        self.commands_queue = self.manager.DequeProxy(["S", "P", "P"]) # * queue for commands within robot, firing commands to arduino
        self.feedback_queue = self.manager.DequeProxy([]) # * queue for feedback from arduino to the robot
        self.read_arduino_process = Process(target=self._read_arduino)
        self.to_arduino_write_process = Process(target=self._write_arduino)
        self.brain_process = Process(target=self._brain)
        
    def start(self):        
        try:
            self.arduino.connect()
            print('Connected to Arduino and algorithm')
            # TODO: received start command from android
            st = input("Start?")
            
            self.read_arduino_process.start()
            self.to_arduino_write_process.start()
            self.brain_process.start()
            
            print('Started all processes: read-arduino, write arduino, brain')
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
    
    def end(self):
        self.arduino.disconnect_all()
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
        
        if source_header == IMAGESERVER_HEADER:
            if target_header == RASPBERRY_HEADER:
                    # TODO: routing the start command from android
                    pass
                    routed = True
        
        if not routed:
            print("Message not routed ", source_header, target_header, data_type, data)
        
    def _brain(self):
        camera = PiCamera(resolution=(IMAGE_WIDTH, IMAGE_HEIGHT))  # '1920x1080'
        camera.iso = 400
        # camera.exposure_compensation = 8
        time.sleep(2)
        camera.shutter_speed = camera.exposure_speed
        camera.exposure_mode = "off"
        g = camera.awb_gains
        camera.awb_mode = "off"
        camera.awb_gains = g
        _ = self._take_pic(camera)
        
        while True:
            try:
                # ! disabled this, cuz currently we don't have the feedback from the STM, we need a fixed period to unlock and locks
                if len(self.feedback_queue) > 0:
                    feedback = self.feedback_queue.popleft()
                    print("Feedback from arduino", feedback)
                    if feedback == "A": # success
                        self.status["state"] = 'Idle'
                
                if self.status["state"] == 'Idle':
                    if len(self.commands_queue) > 0:
                        print("There is a coming command in the queue and we are ready to execute it.")
                        command = self.commands_queue.popleft()
                        if command == 'P':
                            image = self._take_pic(camera)
                            result = self._detecting(image)
                            if result == "L":
                                command = "L"
                                self.to_arduino_message_deque.append(command)
                                self.status["state"] = "Mission"
                            elif result == "R":
                                command = "R"
                                self.to_arduino_message_deque.append(command)
                                self.status["state"] = "Mission"
                        
                        elif command == "S":
                            command = "S"
                            self.to_arduino_message_deque.append(command)
                            self.status["state"] = "Mission"
                        
                        else:
                            print("invalid command")
                            print(command)
            
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
                    print("Sending to arduino the message in_write_arduino", message)
                    self.arduino.write(message.encode())
                
            except Exception as error:
                print('Process write_arduino failed: ' + str(error))
                self.to_arduino_message_deque.appendleft(message)
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
    
    def _detecting(self, img):
        global num_img
        img = cv2.resize(img, (640, 640))
        cv2.imwrite(f"./saved_obs_{num_img}.png", img)
        
        results = model(img, stream=True)
        results = list(results)
        print("results raw from the mode", [r.boxes for r in results])
        
        detections = []
        
        confidence_thres = 0.6
        while confidence_thres > 0.05:
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0]
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    confidence = math.ceil((box.conf[0]*100))/100
                    cls = int(box.cls[0])
                    class_name = classNames[cls]
                    detection = {
                        "class_id": cls,
                        "class_name": class_name,
                        "confidence": confidence,
                        "bbox": [x1, y1, x2, y2],
                        "area": abs(x1-x2) * abs(y2-y1)
                    }
                    
                    if confidence > confidence_thres:
                        detections.append(detection)
            
            if len(detections) > 0:
                break
            confidence_thres -= 0.1
            detections = []
        
        if len(detections) > 0:
            detections.sort(key = lambda x: x["area"], reverse=True)
            theone = detections[0]
            x1, y1 = theone["bbox"][0], theone["bbox"][1]
            x1, y1 = int(x1), int(y1)
            x2, y2 = theone["bbox"][2], theone["bbox"][3]
            x2, y2 = int(x2), int(y2)
            org = [x1, y1]
            height, width, _ = img.shape
            font_scale = min(width, height) * FONT_SCALE
            thickness = math.ceil(min(width, height) * THICKNESS_SCALE)
            class_name = theone["class_name"]
            img = cv2.putText(img, class_name, org, FONT, font_scale, COLOR, thickness)
            img = cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
        
        cv2.imwrite(f"./detected_obs_{num_img}.png", img)
        num_img = num_img + 1
        return detections[0]["class_name"]

        
        