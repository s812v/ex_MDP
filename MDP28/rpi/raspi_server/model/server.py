import os

assert os.path.exists("best.pt"), "Model weights missing! Please upload"

import threading

from flask import Flask, request, jsonify
from pyngrok import ngrok

from ultralytics import YOLO
import cv2
import numpy as np
import math

import matplotlib.pyplot as plt

app = Flask(__name__)
port = "5000"

ngrok.set_auth_token("2c1j7chXBbEg6tM4gRq6dD9OLYB_6jB8fpkKRgSGepYagjEd3")

# Open a ngrok tunnel to the HTTP server
public_url = ngrok.connect(port).public_url
print(" * ngrok tunnel \"{}\" -> \"http://127.0.0.1:{}\"".format(public_url, port))

# Update any base URLs to use the public ngrok URL
app.config["BASE_URL"] = public_url

# model
model = YOLO("best.pt")

# object classes
classNames = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'S', 'T',
              'U', 'V', 'W', 'X', 'Y', 'Z', 'bulls', 'down',
              'eight', 'five', 'four', 'left', 'nine', 'one',
              'right', 'seven', 'six', 'stop', 'three', 'two', 'up']
FONT = cv2.FONT_HERSHEY_SIMPLEX
COLOR = (255, 0, 0)

FONT_SCALE = 2e-3  # Adjust for larger font size in all images
THICKNESS_SCALE = 5e-3  # Adjust for larger thickness in all images

# Define Flask routes
@app.route("/")
def index():
    return "Hello from Colab!"

@app.route('/detect', methods=['POST'])
def detect():
    if 'image' not in request.files:
        return jsonify({"error": "Missing image file"}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Convert the image file to a CV2 image
    filestr = file.read()
    npimg = np.frombuffer(filestr, np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

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

    # show image
    # plt.imshow(img)
    # plt.axis('off')
    # plt.show()


    return jsonify(detections)

# Start the Flask server in a new thread
# threading.Thread(target=app.run, kwargs={"use_reloader": False}).start()
app.run()