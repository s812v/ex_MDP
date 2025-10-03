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

print(os.getcwd())
# assert os.path.exists("./cv/best.pt"), "Model weights missing! Please upload"

from ultralytics import YOLO
import cv2
import numpy as np
import math
import matplotlib.pyplot as plt

# model
model = YOLO("./last_trung.pt")

# # object classes
# classNames = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'S', 'T',
#               'U', 'V', 'W', 'X', 'Y', 'Z', 'bulls', 'down',
#               '8', '5', '4', 'left', '9', '1',
#               'right', '7', '6', 'stop', '3', '2', 'up']

FONT = cv2.FONT_HERSHEY_SIMPLEX
COLOR = (255, 0, 0)

FONT_SCALE = 2e-3  # Adjust for larger font size in all images
THICKNESS_SCALE = 5e-3  # Adjust for larger thickness in all images
num_img = 0

mapped = {0: '11_one', 1: '12_two', 2: '13_three', 3: '14_four', 4: '15_five', 5: '16_six', 6: '17_seven', 7: '18_eight', 8: '19_nine', 9: '20_alphabetA', 10: '21_alphabetB', 11: '22_alphabetC', 12: '23_alphabetD', 13: '24_alphabetE', 14: '25_alphabetF', 15: '26_alphabetG', 16: '27_alphabetH', 17: '28_alphabetS', 18: '29_alphabetT', 19: '30_alphabetU', 20: '31_alphabetV', 21: '32_alphabetW', 22: '33_alphabetX', 23: '34_alphabetY', 24: '35_alphabetZ', 25: '36_uparrow', 26: '37_downarrow', 27: '38_rightarrow', 28: '39_leftarrow', 29: '40_stop', 30: 'obstacles'}

def process_image(img):
    global num_img
    # img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
    # Perform object detection
    img = cv2.resize(img, (640, 640), interpolation=cv2.INTER_LINEAR)
    cv2.imwrite(f"./predictions/obs_{num_img}_before.png", img)
    results = model(img, stream=True)
    
    detections = []
    
    for r in results:
        print(r)
        boxes = r.boxes
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            confidence = math.ceil((box.conf[0]*100))/100
            cls = int(box.cls[0])
            class_name = mapped[cls]

            detection = {
                "class_id": cls,
                "class_name": class_name,
                "confidence": confidence,
                "bbox": [x1, y1, x2, y2]
            }
            if confidence > 0.6:
                detections.append(detection)

                # add detected object label
                org = [x1, y1]
                height, width, _ = img.shape
                font_scale = min(width, height) * FONT_SCALE
                thickness = math.ceil(min(width, height) * THICKNESS_SCALE)
                img = cv2.putText(img, class_name, org, FONT, font_scale, COLOR, thickness)

                # add bounding
                img = cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
    
    cv2.imwrite(f"./predictions/obs_{num_img}_detected.png", img)
    num_img = num_img + 1
    return detections

# 27 means right, 28 means left arrow

if __name__ == "__main__":
    image = cv2.imread("/Users/john/Documents/Code/MDP28/pc_clients/obs_0.png")
    # image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    print(process_image(image))
    