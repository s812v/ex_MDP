import time
import requests
import cv2
import matplotlib.pyplot as plt
import io
from PIL import Image

def process_image(img):

    buf = io.BytesIO()
    im = Image.fromarray(img)
    im.save(buf, format='jpeg')
    image_data = buf.getvalue()
    response = requests.post("http://192.168.28.32:2223/reflect", files={"image":image_data})
    print(response.content)
    #print(response.json())

img = cv2.imread("right.jpg")
#img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
img = cv2.resize(img, (640,640))

print(img.shape)

st_time = time.time()
process_image(img)
et_time = time.time() - st_time

print(f"performance: {et_time} seconds")


