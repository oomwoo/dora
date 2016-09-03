#!/usr/bin/python

import picamera
import picamera.array


fps = 90
w = 320
h = 240

camera = picamera.PiCamera()
camera.resolution = (w, h)
camera.framerate = fps
camera.exposure_mode = 'fixedfps'

# get camera picture
stream = picamera.array.PiRGBArray(camera)
camera.capture(stream, 'rgb', use_video_port=True)
print(stream.array.shape)

# run neural network



camera.close()
