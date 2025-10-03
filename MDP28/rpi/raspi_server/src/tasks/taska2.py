import traceback
import sys
import time
import ast
import collections
from pickle import dumps, loads
from datetime import datetime
from multiprocessing import Process, Value
from multiprocessing.managers import BaseManager
from picamera import PiCamera
from picamera.array import PiRGBArray

from src.Android_com import Android_communicator
from src.Algorithm_com import Algorithm_communicator
from src.data_structure import IncomingMessage, OutgoingMessage, DequeProxy

from typing import List
from src.protocols import *

class DequeProxy(object):
    def __init__(self, *args):
        self.deque = collections.deque(*args)
    def __len__(self):
        return self.deque.__len__()
    def appendleft(self, x):
        self.deque.appendleft(x)
    def append(self, x):
        self.deque.append(x)
    def popleft(self):
        return self.deque.popleft()

class Status(object):
    def __init__(self, state):
        self._state = state
        self._last_state = None

    def set_state(self, state):
        self.set_last_state(self.state)
        self._state = state
    
    def set_last_state(self, state):
        self._last_state = state
    
    @property
    def state(self):
        return self._state
    
    @property
    def last_state(self):
        return self._last_state
    

class DequeManager(BaseManager):
    pass
        
DequeManager.register('DequeProxy', DequeProxy,
                      exposed=['__len__', 'append', 'appendleft', 'popleft'])   
DequeManager.register('Status', Status, 
                      exposed=['set_state', 'state', 'last_state'])

class DetectImage:
    """
    This class handles multi-processing communications between Raspi, and Android and PC.
    """
    def __init__(self):
        """
        Instantiates a MultiProcess Communications session and set up the necessary variables.

        Upon instantiation, RPi begins connecting to
        - Arduino
        - Algorithm
        - Android
        in this exact order.

        Also instantiates the queues required for multiprocessing.
        """
        self.algorithm = Algorithm_communicator()  # handles connection to Algorithm
        self.android = Android_communicator()  # handles connection to Android
        
        self.manager = DequeManager()
        self.manager.start()

        # messages from Arduino, Algorithm and Android are placed in this queue before being read
        self.image_queue = self.manager.DequeProxy([])
        self.status = self.manager.Status("Idle")
        self.message_queue= self.manager.DequeProxy([])
        self.dropped_connection = Value('i',0) # 0 - android, 1 - algorithm

        self.read_algorithm_process = Process(target=self._read_algorithm)
        self.read_android_process = Process(target=self._read_android)
        self.write_process = Process(target=self._write_target)
        
        self.image_process = Process(target=self._image_process)
        # self.status_process = Process(target=self._status_process)
        
        
    def start(self):        
        try:
            self.algorithm.connect()
            self.android.connect()

            print('Connected to Arduino, Algorithm and Android')
            
            self.read_algorithm_process.start()
            self.read_android_process.start()
            self.write_process.start()
            self.image_process.start()
            # self.status_process.start()
            
            print('Started all processes: read-algorithm, read-android, write, image')
            print('Multiprocess communication session started')
            
        except Exception as error:
            print("Main process has died out")
            print("This is coming from 112")
            print(traceback.format_exc())
            raise error
        
        self._allow_reconnection()

    def _allow_reconnection(self):
        print('You can reconnect to RPi after disconnecting now')

        while True:
            try:
                if not self.read_algorithm_process.is_alive():
                    self._reconnect_algorithm()
                    
                if not self.read_android_process.is_alive():
                    self._reconnect_android()
                    
                if not self.write_process.is_alive():
                    if self.dropped_connection.value == 1:
                        self._reconnect_algorithm()
                    elif self.dropped_connection.value == 0:
                        self._reconnect_android()
                        
            except Exception as error:
                print("Error during reconnection: ",error)
                raise error

    def _reconnect_algorithm(self):
        self.algorithm.disconnect()
        
        self.read_algorithm_process.terminate()
        self.write_process.terminate()

        self.algorithm.connect()

        self.read_algorithm_process = Process(target=self._read_algorithm)
        self.read_algorithm_process.start()

        self.write_process = Process(target=self._write_target)
        self.write_process.start()

        print('Reconnected to Algorithm')

    def _reconnect_android(self):
        self.android.disconnect()
        
        self.read_android_process.terminate()
        self.write_process.terminate()
        
        self.android.connect()
        
        self.read_android_process = Process(target=self._read_android)
        self.read_android_process.start()

        self.write_process = Process(target=self._write_target)
        self.write_process.start()
        

        print('Reconnected to Android')

    def end(self):
        # children processes should be killed once this parent process is killed
        self.algorithm.disconnect_all()
        self.android.disconnect_all()
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
        if source_header == ANDROID_HEADER:
            if target_header == RASPBERRY_HEADER:
                # ! append image_queue process
                if data_type == "TakePicture":
                    # self.status.set_state("Recognizing")
                    image = self._take_pic()
                    self.image_queue.append(image)
        
        if source_header == RASPBERRY_HEADER:
            if target_header == ALGORITHM_HEADER:
                if data_type == "Image":
                    self.message_queue.append(
                        OutgoingMessage(source_header=source_header,
                                        target_header=target_header,
                                        data_type=data_type,data=data))
        
        if source_header == RASPBERRY_HEADER:
            if target_header == ANDROID_HEADER:
                # ! append image_queue process
                if data_type == "Prompt":
                    self.message_queue.append(
                        OutgoingMessage(source_header=source_header,
                                        target_header=target_header,
                                        data_type=data_type,data=data))
        
        if source_header == ALGORITHM_HEADER:
            if target_header == ANDROID_HEADER:
                # ! Send back to Android
                if data_type == "Detections":
                    self.message_queue.append(
                        OutgoingMessage(source_header=source_header,
                                        target_header=target_header,
                                        data_type=data_type,data=data)
                    )
                    # self.status.set_state("Completed")
    
    
    def _image_process(self):
        # send to algorithm IncomingMessage
        while True:
            try:
                if len(self.image_queue) > 0:
                    image = self.image_queue.popleft()
                    print("===== shape of image ====", image.shape, image.dtype)
                    image_str = image.tobytes()
                    # message = IncomingMessage(
                    #     message=" ",
                    #     from_outgoing=True,
                    #     source_header=RASPBERRY_HEADER,
                    #     target_header=ALGORITHM_HEADER,
                    #     data_type="HeadingImage"
                    # )
                    data = IncomingMessage(
                        message=image_str,
                        from_outgoing=True,
                        source_header=RASPBERRY_HEADER,
                        target_header=ALGORITHM_HEADER,
                        data_type="Image"
                    )
                    self._routing(data)
            
            except Exception as error:
                print("This is coming from 237")
                print(traceback.format_exc())
                print('Image processing failed: ' + str(error))
                break
        
    
    # def _status_process(self):
    #     last_state = self.status.state
    #     while True:
    #         try:
    #             if self.status.state != last_state:
    #                 last_state = self.status.state
    #                 # ! Prompt back to Android
    #                 prompt = IncomingMessage(source_header=RASPBERRY_HEADER,
    #                                         target_header=ANDROID_HEADER,
    #                                         data_type="Prompt",
    #                                         data=self.status.state)
    #                 self._routing(prompt)
    #             else:
    #                 continue
    #         except Exception as error:
    #             print(traceback.format_exc())
    #             print('Process status failed: ' + str(error))
    #             break
                
    
    # ! Read algorithm
    def _read_algorithm(self):
        while True:
            try:
                raw_message = self.algorithm.read()
                if raw_message is None:
                    continue
                message = IncomingMessage(raw_message, ALGORITHM_HEADER)
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

    def _take_pic(self):
        try:
            start_time = datetime.now()
            # initialize the camera and grab a reference to the raw camera capture
            camera = PiCamera(resolution=(IMAGE_WIDTH, IMAGE_HEIGHT))  # '1920x1080'
            rawCapture = PiRGBArray(camera)
            # allow the camera to warmup
            time.sleep(0.1)
            # grab an image from the camera
            camera.capture(rawCapture, format=IMAGE_FORMAT)
            image = rawCapture.array
            camera.close()
            print('Time taken to take picture: ' + str(datetime.now() - start_time) + 'seconds')

        except Exception as error:
            print('Taking picture failed: ' + str(error))

        return image

    def _write_target(self):
        while True:
            target_header = None
            try:
                if len(self.message_queue) > 0:
                    message = self.message_queue.popleft()
                    target_header = message.target_header 
                    if message.target_header == ALGORITHM_HEADER:
                        self.algorithm.write(message.encoded)
                    elif message.target_header == ANDROID_HEADER:
                        self.android.write(message.encoded)
                    else:
                        print("Invalid header", message.header)
            
            except Exception as error:
                print(traceback.format_exc())
                print('Process write_target failed: ' + str(error))
                if target_header == ANDROID_HEADER:
                    self.dropped_connection.value = 0

                elif target_header == ALGORITHM_HEADER:
                    self.dropped_connection.value = 1
                self.message_queue.appendleft(message)
                break
    
#    def _take_pic(self):
    #    pass
        # try:
        #     start_time = datetime.now()
        #     # initialize the camera and grab a reference to the raw camera capture
        #     camera = PiCamera(resolution=(IMAGE_WIDTH, IMAGE_HEIGHT))  # '1920x1080'
        #     rawCapture = PiRGBArray(camera)
        #     # allow the camera to warmup
        #     time.sleep(0.1)
        #     # grab an image from the camera
        #     camera.capture(rawCapture, format=IMAGE_FORMAT)
        #     image = rawCapture.array
        #     camera.close()
        #     print('Time taken to take picture: ' + str(datetime.now() - start_time) + 'seconds')
        #     # to gather training images
        #     # os.system("raspistill -o images/test"+
        #     # str(start_time.strftime("%d%m%H%M%S"))+".png -w 1920 -h 1080 -q 100")

        # except Exception as error:
        #     print('Taking picture failed: ' + str(error))

        # return image