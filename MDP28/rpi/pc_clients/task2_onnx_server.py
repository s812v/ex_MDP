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
import cv2
import torch
import numpy as np
import math
import matplotlib.pyplot as plt


IMG_MAP = { 0: ('11','Number 1'), 1: ('12','Number 2'), 2: ('13','Number 3'), 3: ('14','Number 4'), 5: ('16','Number 6'), 6: ('17','Number 7'), 7: ('18','Number 8'),
           8: ('19','Number 9'), 4: ('15','Number 5'), 9: ('20','Alphabet A'), 10: ('21','Alphabet B'), 11: ('22','Alphabet C'), 12: ('23','Alphabet D'), 13: ('24','Alphabet E'),
           14: ('25','Alphabet F'), 15: ('26','Alphabet G'), 16: ('27','Alphabet H'), 17: ('28','Alphabet S'), 18: ('29','Alphabet T'), 19: ('30','Alphabet U'), 20: ('31','Alphabet V'),
           21: ('32','Alphabet W'), 22: ('33','Alphabet X'), 23: ('34','Alphabet Y'), 24: ('35','Alphabet Z'), 25: ('36','Up Arrow'), 26: ('37','Down Arrow'), 27: ('38','Right Arrow'),
           28: ('39','Left Arrow'), 29: ('40','Stop'), 30: ('41','Bullseye')}

model = torch.hub.load('ultralytics/yolov5','custom',path='./best20.onnx')
count = 0

def plot_boxes(image, labels, cord_thres):
    '''Takes a image and its labels and plots the boundig boxes on the image and labels it
    :param image: Image detected and to be plotted
    :param labels: Labels of the image
    :param cord_thres: Coordinates of the image
    :return: image with bounding boxes and labels
    '''
    n = len(labels)
    x_shape, y_shape = image.shape[1], image.shape[0]
    true_labels = []
    highest_probability = -1
    for i in range(n):
        row = cord_thres[i]
        if row[4] >= 0.5:
            x1, y1, x2, y2 = int(row[0]*x_shape), int(row[1]*y_shape), int(row[2]*x_shape), int(row[3]*y_shape)
            bgr_box = (0,255,0)
            bgr_text = (0,0,0)
            cv2.rectangle(image, (x1,y1), (x2,y2), bgr_box, 5)
            label_text = f"{labels[i][1]}"
            label = f"Image id={labels[i][0]}"
            true_labels.append((labels[i][0],labels[i][1],row[4]))

            ## For the text background
            ## Finds space requied by text so we can put a background
            (w, h), _ = cv2.getTextSize(
                str(label), cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
            
            (w_label, h_label), _ = cv2.getTextSize(
                str(label_text), cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
            ## Draws the background
            cv2.rectangle(image, (x2+10, y2+10), (x2+10+w, y2-h-h_label-5),bgr_text, 2)
            cv2.rectangle(image, (x2+10, y2+10), (x2+10+w, y2-h-h_label-5), (255,255,255), -1)
            cv2.putText(image, label_text, (x2+10, y2-h), cv2.FONT_HERSHEY_SIMPLEX, 0.6, bgr_text, 1)
            cv2.putText(image, label, (x2+10,y2+5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, bgr_text, 1)
    return image,true_labels

def imageDetect(img):
    global count
    cv2.imwrite(f"./predictions/rpi_sent_{count}.png", img)
    resized = cv2.resize(img, (640, 640), interpolation=cv2.INTER_AREA)
    resized = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
    cv2.imwrite(f"./predictions/rpi_senf_{count}_rgb.png", resized)
    
    results = model(resized)
    print(results)
    labels, cord_thres = results.xyxyn[0][:, -1].numpy(), results.xyxyn[0][:, :-1].numpy()
    if len(labels) == 0:
        print("[6] For debugging. No object detected!")
    labels_mapped = [IMG_MAP[int(i)] for i in labels]
    image_with_bounding_box,correct_label = plot_boxes(resized, labels_mapped, cord_thres)
    cv2.imwrite(f'./predictions/recognized_{count}.jpg', image_with_bounding_box)
    print(labels_mapped)
    
    print("image saved")
    if labels_mapped[0][1] == "Left Arrow":
        return [{
            "class_id": 0,
        }]
    elif labels_mapped[0][1] == "Right Arrow":
        return [{
            "class_id": 1
        }]
    

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
                    # class_name = classNames.index(data[0]["class_name"])
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
            data_bytes = self.recvall(np.prod(self.image_shape)) # image + vertical distance, from 0 -> 2000
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

    LOCAL_HOST = "192.168.28.29"
    LOCAL_PORT = 2223
    print(f"setting up connectiont to {LOCAL_HOST}:{LOCAL_PORT}")
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
    # Listen to image, predict the image, then bounding box,
    # then send back the ack
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
                        detections = imageDetect(buffer)
                        print(detections)
                        print("Sending back the detections...")
                        # client.send_message("RSP", "Detections", detections)
                        client.send_message("RSP", "Detections", detections)
            except OSError as e:
                print(e)
                pass
            except KeyboardInterrupt:
                client.close()
                sys.exit(1)
                print("Got data from RPi:")