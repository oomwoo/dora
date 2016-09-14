#!/usr/bin/python

import picamera
import picamera.array
from PIL import Image


fps = 30
w = 320
h = 240
use_video_port = True

camera = picamera.PiCamera()
import time
camera.resolution = (w, h)
camera.framerate = fps
# camera.exposure_mode = 'fixedfps'

# Let exposure work
time.sleep(1)

# get camera picture
stream = picamera.array.PiRGBArray(camera)
camera.capture(stream, 'rgb', use_video_port=use_video_port)
print("use_video_port="+repr(use_video_port))
print("camera.framerate="+repr(camera.framerate))
camera.close()

image = Image.fromarray(stream.array)
image.save("camera_capture_test.png", "PNG")
image.show()
