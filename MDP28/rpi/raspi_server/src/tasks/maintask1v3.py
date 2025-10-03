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

class MainTaskFeedback:
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

        self.algorithm = Algorithm_communicator()  # handles connection to Algorithm
        self.arduino = Arduino_communicator()  # handles connection to Arduino
        self.android = Android_communicator()  # handles connection to Android
        self.imageserver = Imageserver_communicator()
        # self.imageserver = Imageserver_communicator_server()
        
        self.manager = DequeManager()
        self.sub_manager = Manager()
        self.manager.start()

        # self.status = Value('s', 'Idle') # * status of the robot (0: Idle, 1: Mission)
        # self.last_command = Value('s', '') # * last command sent to the arduino
        self.status = self.sub_manager.dict({'state': 'Idle', 'last_command': '', 'current_obs_idx': -1, 'obs_order': [], 'pause_positions': [],'path_hist': [], 'current_received': 0})
        self.obs_order = self.sub_manager.list([])
        
        self.to_android_message_deque = self.manager.DequeProxy() # * queue for communicating
        self.to_arduino_message_deque = self.manager.DequeProxy() # * queue for communicating
        self.to_algorithm_message_queue = self.manager.DequeProxy()
        self.to_imageserver_message_queue = self.manager.DequeProxy()
      
        
        self.image_queue = self.manager.DequeProxy([])
        self.image_id_queue = self.manager.DequeProxy([])
        self.commands_queue = self.manager.DequeProxy() # * queue for commands within robot, firing commands to arduino
        self.feedback_queue = self.manager.DequeProxy([]) # * queue for feedback from arduino to the robot
        # ! we also need another commands queue for the algorithm to send commands to the robot, with higher priority


        self.read_arduino_process = Process(target=self._read_arduino)
        self.read_android_process = Process(target=self._read_android)
        self.read_algorithm_process = Process(target=self._read_algorithm)
        self.read_imageserver_process = Process(target=self._read_imageserver)
        
        self.to_arduino_write_process = Process(target=self._write_arduino)
        self.to_android_write_process = Process(target=self._write_android)
        self.to_imageserver_write_process = Process(target=self._write_imageserver)
        self.to_algorithm_write_process = Process(target=self._write_algorithm)
        # ! another process to handle the commands queue, controling the queue, and the status of the robot
        # ! the only one can access to to_arduino_message_deque with the commands from the commands_queue
        self.image_process = Process(target=self._image_process)
        self.brain_process = Process(target=self._brain)
        # self.hist_process = Process(target=self._hist)
        
    def start(self):        
        try:
            self.imageserver.connect()
            self.arduino.connect()
            self.algorithm.connect()
            self.android.connect()
            print('Connected to Arduino and algorithm and server')

            
            self.read_arduino_process.start()
            self.read_algorithm_process.start()
            self.read_imageserver_process.start()
            self.read_android_process.start()
            
            self.to_arduino_write_process.start()
            self.to_algorithm_write_process.start()
            self.to_imageserver_write_process.start()
            self.to_android_write_process.start()
            
            self.brain_process.start()
            self.image_process.start()
            # self.hist_process.start()
            
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
        self.algorithm.disconnect_all()
        self.imageserver.disconnect_all()
        print('Multiprocess communication session ended')

    def _allow_reconnection(self):
        print('You can reconnect to RPi after disconnecting now')
        while True:
            try:
                if not self.read_arduino_process.is_alive():
                    self._reconnect_arduino()
                if not self.read_android_process.is_alive():
                    self._reconnect_android()
                if not self.read_algorithm_process.is_alive():
                    self._reconnect_algorithm()
                if not self.read_imageserver_process.is_alive():
                    self._reconnect_imageserver()
                
                if not self.to_arduino_write_process.is_alive():
                    self._reconnect_arduino()
                if not self.to_android_write_process.is_alive():
                    self._reconnect_android()
                if not self.to_algorithm_write_process.is_alive():
                    self._reconnect_algorithm()
                if not self.to_imageserver_write_process.is_alive():
                    self._reconnect_imageserver()
            except Exception as error:
                print("Error during reconnection: ",error)
                raise error

    def _reconnect_arduino(self):
        self.arduino.disconnect()
        
        self.read_arduino_process.terminate()
        self.to_android_write_process.terminate()
        self.to_android_write_process.terminate()
        self.to_algorithm_write_process.terminate()
        self.to_imageserver_write_process.terminate()
        self.brain_process.terminate()

        self.arduino.connect()

        self.read_arduino_process = Process(target=self._read_arduino)
        self.read_arduino_process.start()

        self.to_arduino_message_deque = Process(target=self._write_arduino)
        self.to_arduino_write_process.start()
        
        self.to_android_write_process = Process(target=self._write_android)
        self.to_android_write_process.start()
        
        self.to_algorithm_write_process = Process(target=self._write_algorithm)
        self.to_algorithm_write_process.start()
        
        self.to_imageserver_write_process = Process(target=self._write_imageserver)
        self.to_imageserver_write_process.start()
        
        self.brain_process = Process(target=self._brain)
        self.brain_process.start()
        

        print('Reconnected to Arduino')

    def _reconnect_android(self):
        self.android.disconnect()
        
        self.read_android_process.terminate()
        self.to_android_write_process.terminate()
        self.to_android_write_process.terminate()
        self.to_algorithm_write_process.terminate()
        self.to_imageserver_write_process.terminate()
        self.brain_process.terminate()
        
        self.android.connect()
        
        self.read_android_process = Process(target=self._read_android)
        self.read_android_process.start()

        self.to_arduino_message_deque = Process(target=self._write_arduino)
        self.to_arduino_write_process.start()
        
        self.to_android_write_process = Process(target=self._write_android)
        self.to_android_write_process.start()
        
        self.to_algorithm_write_process = Process(target=self._write_algorithm)
        self.to_algorithm_write_process.start()
        
        self.to_imageserver_write_process = Process(target=self._write_imageserver)
        self.to_imageserver_write_process.start()
        
        self.brain_process = Process(target=self._brain)
        self.brain_process.start()

        print('Reconnected to Android')
    
    def _reconnect_algorithm(self):
        self.algorithm.disconnect()
        
        self.read_algorithm.terminate()
        self.to_android_write_process.terminate()
        self.to_android_write_process.terminate()
        self.to_algorithm_write_process.terminate()
        self.to_imageserver_write_process.terminate()
        self.brain_process.terminate()
        
        self.algorithm.connect()
        
        self.read_algorithm_process = Process(target=self._read_algorithm)
        self.read_algorithm_process.start()

        self.to_arduino_message_deque = Process(target=self._write_arduino)
        self.to_arduino_write_process.start()
        
        self.to_android_write_process = Process(target=self._write_android)
        self.to_android_write_process.start()
        
        self.to_algorithm_write_process = Process(target=self._write_algorithm)
        self.to_algorithm_write_process.start()
        
        self.to_imageserver_write_process = Process(target=self._write_imageserver)
        self.to_imageserver_write_process.start()
        self.to_algorithm_write_process.start()
        
        self.brain_process = Process(target=self._brain)
        self.brain_process.start()

        print('Reconnected to Algorithm')
        
    def _reconnect_imageserver(self):
        self.imageserver.disconnect()
        
        self.read_imageserver_process.terminate()
        self.to_android_write_process.terminate()
        self.to_android_write_process.terminate()
        self.to_algorithm_write_process.terminate()
        self.to_imageserver_write_process.terminate()
        self.brain_process.terminate()
        
        self.imageserver.connect()
        
        self.read_imageserver_process = Process(target=self._read_imageserver)
        self.read_imageserver_process.start()

        self.to_arduino_message_deque = Process(target=self._write_arduino)
        self.to_arduino_write_process.start()
        
        self.to_android_write_process = Process(target=self._write_android)
        self.to_android_write_process.start()
        
        self.to_algorithm_write_process = Process(target=self._write_algorithm)
        self.to_algorithm_write_process.start()
        
        self.to_imageserver_write_process = Process(target=self._write_imageserver)
        self.to_imageserver_write_process.start()
        
        self.brain_process = Process(target=self._brain)
        self.brain_process.start()

        print('Reconnected to Algorithm')
    
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
        if source_header == ANDROID_HEADER:
            if target_header == ARDUINO_HEADER:  # Send the basic commands to the Arduino
                # print(f"{data_type}, Sending Android to Arduino: ")
                if data == AndroidToArduino.FL: 
                    # Forward Left
                    data = 'LF090'
                elif data == AndroidToArduino.F:
                    # Forward
                    data = 'SF060'
                elif data == AndroidToArduino.FR:
                    data = 'RF090'
                elif data == AndroidToArduino.BL:
                    # Backward left
                    data = 'LB090'
                elif data == AndroidToArduino.B:
                    # Backward
                    data = 'SB060'
                elif data == AndroidToArduino.BR:
                    data = 'RB090'
                print(f"Sending Android to Arduino a command: {data}")
                self.commands_queue.append(data)
                routed = True
        
        if source_header == ANDROID_HEADER:
            if target_header == ALGORITHM_HEADER:
                # arena sending from android to algorithm
                if data_type == "Arena":
                    # ! sending arena from android to algorithm
                    print("Routing Arena to algorithm")
                    message = OutgoingMessage(source_header=source_header,
                                              target_header=target_header,
                                              data_type=data_type,
                                              data=data)
                    self.to_algorithm_message_queue.append(message)
                    routed = True
        
        if source_header == ALGORITHM_HEADER:
            if target_header == ARDUINO_HEADER:
                if data_type == "Commands":
                    # ! sending commands from algorithm to arduino
                    data = data[1:-1]
                    commands = data.split(', ')
                    print("sent commands")
                    # commands = ast.literal_eval(data)
                    for command in commands:
                        if command == "finish":
                            break
                        else:
                            self.commands_queue.append(command)
                    routed = True

        if source_header == ALGORITHM_HEADER:
            if target_header == RASPBERRY_HEADER:
                if data_type == "ObsOrder":
                    # ! sending the observation order to raspberry pi from algorithm
                    data = data[1:-1]
                    order = data.split(', ')
                    # self.obs_order = order
                    self.status["obs_order"] = order
                    print("Observation order from algorithm", order, self.status["obs_order"])
                    routed = True
        
        if source_header == ALGORITHM_HEADER:
            if target_header == RASPBERRY_HEADER:
                if data_type == "Targets":
                    # ! sending the observation order to raspberry pi from algorithm
                    data = ast.literal_eval(data)
                    print("Trying to assign the pause_positions ", data)
                    self.status["pause_positions"] = data
                    print("pause_positions order from algorithm", data, self.status["pause_positions"])
                    routed = True
        
        if source_header == ALGORITHM_HEADER:
            if target_header == RASPBERRY_HEADER:
                if data_type == "PathHist":
                    # ! sending the PathHist order to raspberry pi from algorithm
                    # data = data[1:-1]
                    print("Aissgning path hist before ast", data)
                    data = ast.literal_eval(data)
                    print("Aissgning path hist", data)
                    if self.status["path_hist"] is None:
                        self.status["path_hist"] = data   
                    elif len(self.status["path_hist"])>0:
                        self.status["path_hist"] = self.status["path_hist"].extend(data)
                    else:
                        self.status["path_hist"] = data
                    routed = True
        
        if source_header == RASPBERRY_HEADER:
            if target_header == ANDROID_HEADER:
                if data_type == "PathHist":
                    # ! sending the PathHist order to raspberry pi from algorithm
                    print("routing path hist")
                    message = OutgoingMessage(source_header=source_header,
                                              target_header=target_header,
                                              data_type=data_type,
                                              data=data)
                    self.to_android_message_deque.append(message)
                    routed = True
                    
        
        if source_header == ANDROID_HEADER:
            if target_header == RASPBERRY_HEADER:
                if data_type == "TakePicture":
                    # ! Got recognize button from android
                    self.status["state"] = "TakingImage"
                    self.status["obs_order"] = [1]
                    camera = PiCamera(resolution=(IMAGE_WIDTH, IMAGE_HEIGHT))  # '1920x1080'
                    camera.iso = 400
                    # camera.exposure_compensation = 8
                    time.sleep(2)
                    
                    camera.shutter_speed = camera.exposure_speed
                    camera.exposure_mode = "off"
                    image = self._take_pic(camera)
                    camera.close()
                    self.image_queue.append(image)
                    routed = True
        
        if source_header == RASPBERRY_HEADER:
            if target_header == IMAGESERVER_HEADER:
                if data_type == "Image":
                    # ! Sending image to image server
                    self.to_imageserver_message_queue.append(
                        OutgoingMessage(source_header=source_header,
                                        target_header=target_header,
                                        data_type=data_type,data=data))
                    routed = True
        
        if source_header == RASPBERRY_HEADER:
            if target_header == ANDROID_HEADER:
                if data_type == "Detections":
                    # ! Passing result to android
                    self.to_android_message_deque.append(
                        OutgoingMessage(source_header=source_header,
                                        target_header=target_header,
                                        data_type=data_type,data=data))
                    routed = True
        
        if source_header == IMAGESERVER_HEADER:
            if target_header == RASPBERRY_HEADER:
                if data_type == "Detections":
                    # ! Passing image recognition server + current obs idx - > android
                    try:
                        # data = ast.literal_eval(data)
                        data = data[1:-1] # remove square bracket
                        data = data.split(',')
                    except Exception as e:
                        print("Got error when try to interpret image detection result from image server to raspberry pi")
                    # obs_idx = data[0] ! # ignore this
                    image_character = data[1] # str
                    
                    print("Routing result back to android", self.status["obs_order"], self.status["current_obs_idx"])
                    # obs_idx = self.status["obs_order"][self.status["current_obs_idx"]]
                    obs_idx = self.status["obs_order"][self.status["current_received"]]
                    # self.status["state"] = "Idle"
                    data[0] = obs_idx
                    for idx in range(len(data)):
                        data[idx] = str(data[idx])
                    data = '[' + ','.join(data) + ']'
                    self.status["current_received"] = self.status["current_received"] + 1
                    # passing this to
                    self._routing(IncomingMessage(source_header=RASPBERRY_HEADER,
                                                  from_outgoing=True,
                                                target_header=ANDROID_HEADER,
                                                data_type=data_type,message=data))
                    routed = True
        if not routed:
            print("Message not routed ", source_header, target_header, data_type, data)
        
    def _hist(self):
        st_time = None
        id = 0
        while True:
            if self.status["path_hist"] is None:
                continue
            if len(self.status["path_hist"]) > 0:
                if st_time is None:
                    st_time = time.time()
                # the path hist already arrived
                end_time = time.time()
                if end_time - st_time > 3:
                    st_time = time.time()
                    if id < len(self.status["path_hist"]):
                        cord = self.status["path_hist"][id]
                        cord = [str(i) for i in cord]
                        data_str = '['
                        data_str += ",".join(cord)
                        data_str += ']'
                        message = IncomingMessage(source_header=RASPBERRY_HEADER,
                                                from_outgoing=True,
                                                target_header=ANDROID_HEADER,
                                                data_type="PathHist",
                                                message=data_str)
                        self._routing(message)
                        id += 1
    
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
                            # obs_idx = self.status["current_obs_idx"]
                            # horizontal = self.status["pause_positions"][obs_idx][0]
                            # vertical = self.status["pause_positions"][obs_idx][1]
                            # print("Taking image for ", obs_idx, " obstacle")
                            image = self._take_pic(camera, horizontal=None, vertical=None, obs_idx=None)
                            self.image_queue.append(image)
                            self.image_id_queue.append(self.status["current_obs_idx"])
                        #     self.status["state"] = "TakingImage"
                        else:
                            self.to_arduino_message_deque.append(command)
                            self.status["last_command"] = command
                            self.status["state"] = 'Mission'
            
            except Exception as error:
                print('Process brain failed: ' + str(error))
                break
    
    def _image_process(self):
        # send to algorithm IncomingMessage
        while True:
            try:
                if len(self.image_queue) > 0:
                    image = self.image_queue.popleft()
                    image_id = self.image_id_queue.popleft()
                    distance = self.status["pause_positions"][image_id][1]
                    distance = distance // 10
                    print("===== shape of image ====", image.shape, image.dtype)
                    image_str = image.tobytes()
                    print("time to take, ", image_id, " distance ", distance)
                    image_str += bytes([distance])
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

    # ! Read android
    def _read_algorithm(self):
        while True:
            try:
                raw_message = self.algorithm.read()
                if raw_message is None:
                    continue
                message = IncomingMessage(raw_message, ALGORITHM_HEADER)
                if message.data_type == "Commands":
                    # ! Need to treat this differently, put the commands into a queue, not 
                    # ! routing the message imidiately to Arduino
                    # self.commands_queue
                    # append OutgoingMessage
                    # message.data -> string, evaluate it to list of string
                    # commands_data = ast.literal_eval(message.data)
                    # for command_str in message.data:
                    outgoing_message = OutgoingMessage(
                        target_header=ARDUINO_HEADER,
                        source_header=ALGORITHM_HEADER,
                        data_type='Commands',
                        data=message.data
                    )
                    self._routing(message)
                    # self.to_algorithm_message_queue.append(outgoing_message)
                else:
                    print("routing from algorithm, ", message.data_type)
                    self._routing(message)
                
            except Exception as error:
                print(traceback.format_exc())
                print('Process read_algorithm failed: ' + str(error))
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
                    self.arduino.write(message.encode())
                
            except Exception as error:
                print('Process write_arduino failed: ' + str(error))
                self.to_arduino_message_deque.appendleft(message)
                break

    def _write_algorithm(self):
        while True:
            try:
                # data from brain to arduino is different, brain acts like an interface with this
                if len(self.to_algorithm_message_queue)>0:
                    message = self.to_algorithm_message_queue.popleft()
                    print(message.encoded, "from message algrothm queue")
                    self.algorithm.write(message.encoded)
                
            except Exception as error:
                print('Process write_algorithm failed: ' + str(error))
                self.to_algorithm_message_queue.appendleft(message)
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

    def get_uv(self, horizontal,height,vertical):
        sensor_width=2592
        sensor_height=1944
        focal = 3.6 #mm
        pixel_size=1.4

        ratio_w = 1024/sensor_width
        ratio_h = 1024/sensor_height
        x = horizontal
        y = height
        z = vertical
        f = focal #mm
        theta = math.acos(abs(z)/math.sqrt(x*x+z*z)) # 
        deg = math.degrees(theta)
        print(deg)
        
        # alpha = f/2.76 # vertical focal ratio, height
        # beta = f/3.68 # horizontal focal ratio, width
        e = 0.001
        try:
            u = f * (x/z - y*math.tan(theta)/z)
        except:
            u = f * x / z# projected horizontal on image plane
        print(f"u {u}mm", f"f*x/z {f*x/z}mm", f"mathtan, {y*math.tan(theta)/z}mm")
        u /= (pixel_size*e) #  projected width pixel
        
        v = f * (y/(z*math.cos(theta))) # height pixel, using height
        v /= pixel_size*e # f/z == projected_height/real_height
        
        print("displacment ", u, v)
        # u *= -1
        # v *= -1
        
        # u = 512+u
        v = 512-v*ratio_h # got flip up
        u = 512+u*ratio_w
        # u = 2464 - u
        
        # v = 512+v
        return (u, v)
    
    def _take_pic(self, camera, horizontal=None, vertical=None, obs_idx=None):
        try:
            start_time = datetime.now()
            # initialize the camera and grab a reference to the raw camera capture
            # camera = PiCamera(resolution=(IMAGE_WIDTH, IMAGE_HEIGHT))  # '1920x1080'
            # camera.iso = 400
            # camera.shutter_speed = camera.exposure_speed
            # camera.exposure_mode = "off"
            # g = camera.awb_gains
            # camera.awb_mode = "off"
            # camera.awb_gains = g
            rawCapture = PiRGBArray(camera)
            # allow the camera to warmup
            time.sleep(0.1)
            # grab an image from the camera
            camera.capture(rawCapture, format=IMAGE_FORMAT)
            image = rawCapture.array
            
            # pil_image = Image.fromarray(image)
            # u,v=self.get_uv(horizontal=horizontal, height=30, vertical=vertical)
            # #plot the a point on the image
            # draw = ImageDraw.Draw(pil_image)
            # def get_rec(u,v):
            #     return (u-20, v-20, u+20, v+20)
            # draw.ellipse(get_rec(u, v), fill = 'blue', outline ='blue')
            # pil_image.save(f"./obs_{obs_idx}.png")
            
            # camera.close()
            print('Time taken to take picture: ' + str(datetime.now() - start_time) + 'seconds')

        except Exception as error:
            print('Taking picture failed: ' + str(error))

        return image