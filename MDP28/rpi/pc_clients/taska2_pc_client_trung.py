import pickle
import socket
import ast
import numpy as np
import sys
import select
import traceback
import time
from PIL import Image
import traceback

import os

# print(os.getcwd())
# assert os.path.exists("./cv/best.pt"), "Model weights missing! Please upload"

from ultralytics import YOLO
import cv2
import numpy as np
import math
import matplotlib.pyplot as plt

# model
model = YOLO("./last_trung.pt")
mapped = {0: '11_one', 1: '12_two', 2: '13_three', 3: '14_four', 4: '15_five', 5: '16_six', 6: '17_seven', 7: '18_eight', 8: '19_nine', 9: '20_alphabetA', 10: '21_alphabetB', 11: '22_alphabetC', 12: '23_alphabetD', 13: '24_alphabetE', 14: '25_alphabetF', 15: '26_alphabetG', 16: '27_alphabetH', 17: '28_alphabetS', 18: '29_alphabetT', 19: '30_alphabetU', 20: '31_alphabetV', 21: '32_alphabetW', 22: '33_alphabetX', 23: '34_alphabetY', 24: '35_alphabetZ', 25: '36_uparrow', 26: '37_downarrow', 27: '38_rightarrow', 28: '39_leftarrow', 29: '40_stop', 30: 'obstacles'}

FONT = cv2.FONT_HERSHEY_SIMPLEX
COLOR = (255, 0, 0)

FONT_SCALE = 2e-3  # Adjust for larger font size in all images
THICKNESS_SCALE = 5e-3  # Adjust for larger thickness in all images
num_img = 0

def process_image(img):
    #! 27 means right, 28 means left arrow
    global num_img
    # img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
    # Perform object detection
    img = cv2.resize(img, (640, 640))
    
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    cv2.imwrite(f"./saved/obs_{num_img}.png", img)
    
    results = model(img, stream=True)
    results = list(results)
    print("results raw from the mode", [r.boxes for r in results])
    
    detections = []
    cv2.imwrite(f"./predictions/obs_{num_img}.png", img)
    confidence_thres = 0.7
    
    while confidence_thres > 0.05:
        for r in results:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                confidence = math.ceil((box.conf[0]*100))/100
                cls = int(box.cls[0])
                class_name = mapped[cls]
                if cls == 30:
                    print("bulls")
                    continue
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
        # add bounding box
        img = cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
        cv2.imwrite(f"./predictions/obs_{num_img}.png", img)
    num_img = num_img + 1
    return detections

class PcClient:
    """
    Used for connecting to...
    """
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket()
        self.socket.settimeout(5)
        self.image_shape = np.asarray([1024, 1024, 3])

    def connect(self):
        self.socket.connect((self.host, self.port))

    def send_message(self, target, data_type, data):
        message = None
        
        if target == "RSP":
            if data_type == "Detections":
                if len(data) == 0:
                    message = target + '|' + data_type + '|' + '[1,-1]'
                    message = message.encode()
                else:
                    class_name = data[0]["class_id"]
                    class_name = str(class_name)
                    message = target + '|' + data_type + '|' + '[1,' + class_name + ']'
                    message = message.encode()
        else:
            print("Invalid header") 
        self.socket.sendall(message)

    def recvall(self, size):
        print("About to receiving ", size, " bytes")
        BUFFER_SIZE = 1024
        data = bytearray()
        while len(data) < size:
            packet = self.socket.recv(size - len(data))
            if not packet:
                return None
            data.extend(packet)
        return data

    def receive_data(self):
        # receive image data and recognition as well
        try:
            data_bytes = self.recvall(np.prod(self.image_shape))
            if data_bytes is None:
                return None
            if len(data_bytes) == 0:
                return ""
            rgb_array = np.frombuffer(data_bytes, dtype=np.uint8).reshape(self.image_shape)
            return rgb_array
        
        except Exception as error:
            # print(traceback.format_exc())
            print("Error", error)
            
    def close(self):
        self.socket.close()

    def settimeout(self, time):
        self.socket.settimeout(time)

        
if __name__ == "__main__":
    RPI_HOST = "192.168.28.28"
    RPI_PORT = 1112
    print(f"setting up connectiont to {RPI_HOST}:{RPI_PORT}")
    client = PcClient(RPI_HOST, RPI_PORT)
    while True:
        try:
            client.connect()
            break
        except OSError:
            pass
        except KeyboardInterrupt:
            client.close()
            sys.exit(1)
    
    print(f"Connected to {RPI_HOST}:{RPI_HOST}")
    client.settimeout(10)  # Set timeout to 10 seconds
    while True:
        print("Waiting to receive Image data from RPi...")
        while True:
            try:
                buffer = client.receive_data()
                if buffer is None:
                    continue
                else:
                    if len(buffer) == 0:
                        client.close()
                        client = PcClient(settings.RPI_HOST, settings.RPI_PORT)
                        print("Got disconnected")
                        print("Trying to reconnect")
                        while True:
                            time.sleep(1)
                            try:
                                client.connect()
                                break
                            except OSError as e:
                                client = PcClient(settings.RPI_HOST, settings.RPI_PORT)
                                pass
                            except KeyboardInterrupt:
                                client.close()
                                sys.exit(1)
                        print("Connected to RPi!\n")
                        continue
                    else:
                        print("Received image shape, ", buffer.shape)
                        detections = process_image(buffer)
                        print(detections)
                        #! 27 means right, 28 means left arrow
                        print("Sending back the detections...")
                        client.send_message("RSP", "Detections", detections)
            except OSError as e:
                print(e)
                pass
            except KeyboardInterrupt:
                client.close()
                sys.exit(1)
                print("Got data from RPi:")