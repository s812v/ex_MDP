import pickle
import socket
import ast
import numpy as np
import sys
import traceback
from PIL import Image

import os

print(os.getcwd())
assert os.path.exists("../cv/best.pt"), "Model weights missing! Please upload"

from ultralytics import YOLO
import cv2
import numpy as np
import math
import matplotlib.pyplot as plt

# model
model = YOLO("../cv/best.pt")

# object classes
classNames = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'S', 'T',
              'U', 'V', 'W', 'X', 'Y', 'Z', 'bulls', 'down',
              'eight', 'five', 'four', 'left', 'nine', 'one',
              'right', 'seven', 'six', 'stop', 'three', 'two', 'up']

FONT = cv2.FONT_HERSHEY_SIMPLEX
COLOR = (255, 0, 0)

FONT_SCALE = 2e-3  # Adjust for larger font size in all images
THICKNESS_SCALE = 5e-3  # Adjust for larger thickness in all images

def process_image(img):
    
    # img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
    # Perform object detection
    results = model(img, stream=True)
    detections = []

    # recolour
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    for r in results:
        boxes = r.boxes
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            confidence = math.ceil((box.conf[0]*100))/100
            cls = int(box.cls[0])
            class_name = classNames[cls]

            detection = {
                "class_name": class_name,
                "confidence": confidence,
                "bbox": [x1, y1, x2, y2]
            }
            detections.append(detection)

            # add detected object label
            org = [x1, y1]
            height, width, _ = img.shape
            font_scale = min(width, height) * FONT_SCALE
            thickness = math.ceil(min(width, height) * THICKNESS_SCALE)
            img = cv2.putText(img, class_name, org, FONT, font_scale, COLOR, thickness)

            # add bounding box
            img = cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
    
    cv2.imwrite("prediction.png", img)
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
            if data_type == "ACK":
                message = target + '|' + data_type + '|'
                
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
    RPI_PORT = 1111
    print(f"Attempting to connect to {RPI_HOST}:{RPI_PORT}")
    client = PcClient(RPI_HOST, RPI_PORT)
    # Wait to connect to RPi.
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
    # Listen to image, predict the image, then bounding box,
    # then send back the ack
    print("Waiting to receive Image data from RPi...")
    client.settimeout(10)  # Set timeout to 10 seconds
    while True:
        while True:
            try:
                buffer = client.receive_data()
                if buffer is not None:
                    print("Received image shape, ", buffer.shape)
                    detections = process_image(buffer)
                else:
                    continue
            except Exception as e:
                print(e)
                pass
        # im = Image.fromarray(image)
        # im.save("your_file.jpeg")