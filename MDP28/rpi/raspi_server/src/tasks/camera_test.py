import PIL
from PIL import Image
import time
from picamera import PiCamera
from picamera.array import PiRGBArray
import math

# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera(resolution=(1024, 1024))  # '1920x1080'
rawCapture = PiRGBArray(camera)
# allow the camera to warmup
time.sleep(0.1)
# grab an image from the camera
camera.capture(rawCapture, format="rgb")
image = rawCapture.array
image = Image.fromarray(image)
image.save(f"current.png")

def get(x,y,z):
    # x,y,z in mm
    # real coordinates y is the height relative to the camera
    # z is the distance from camera to obstacle (verticle, facing)
    # x is distance from camera to obstacle (horizontal axis)
    f = 3.04 #mm
    theta = math.asin(z/sqrt(x*x+z*z)) # 
    u = f * 
    return 
    
    # return u,v from center of image

camera.close()