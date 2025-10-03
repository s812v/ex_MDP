from flask import Flask, request, jsonify
from ultralytics import YOLO
import cv2
import numpy as np
import math
import time


app = Flask(__name__)

model = YOLO("best.pt")
className = ['left', 'right']
detections = []

def process_image(img):
    global model, className

    results = model(img, stream=True)
    for r in results:
        boxes = r.boxes
        for box in boxes:
            confidence = math.ceil((box.conf[0]*100))/100
            if confidence < 0.6:
                # Exit iteration and move onto the next box
                continue

            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            #confidence = math.ceil((box.conf[0]*100))/100
            cls = int(box.cls[0])
            class_name = className[cls]
            detection = {
                "class_id": cls,
                "class_name": class_name,
                "confidence": confidence,
                "bbox": [x1, y1, x2, y2]
            }
            print(detection)
            detections.append(detection)
    return detections

@app.route('/detect', methods=['POST'])
def detect_objects():
    if 'image' not in request.files:
        return jsonify({"error": "No image provided"}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No selected image"}), 400

    try:
        npimg = np.fromstring(file.read(), np.uint8)
        img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, (640, 640))
        detections = process_image(img)
        return jsonify(detections), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Running cold start rectifier by loading dummy image into model...")
    # blank_image = np.zeros((640,640,3), np.uint8)
    # process_image(blank_image)
    app.run(debug=False, host="0.0.0.0", port=2223)
