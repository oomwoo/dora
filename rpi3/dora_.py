#!/usr/bin/python
# (c) oomwoo.com
# Self-driving (autonomous) robot vehicle
# Runs on Raspberry Pi 3
# Distributed under GNU General Public License v3
# Use solely at your own risk
# Absolutely no warranty expressed or implied
import webiopi
from Adafruit_MotorHAT import Adafruit_MotorHAT, Adafruit_DCMotor
import time, sys, getopt, picamera, glob, re, subprocess, os
import threading
import picamera.array
import numpy as np
from PIL import Image
from neon.backends import gen_backend
from neon.layers import Affine, Conv, Pooling
from neon.models import Model
from neon.transforms import Rectlin, Softmax
from neon.initializers import Uniform
from neon.data.dataiterator import ArrayIterator


# Configuration defaults
default_motor_speed = 150
debug = False
fps = 90
w = 160
h = 120
quality = 23
bitrate = 0
file_name_prefix = "rec"
hor_flip = False
ver_flip = False
video_file_ext = ".h264"
log_file_ext = ".txt"
log_file = []
iso = 0
shutdown_on_exit = True
autonomous = False
video_file_name = []
log_file_name = []
autonomous_thread = []

# CNN setup
W = 32
H = W
my_dir = os.path.expanduser("~") + "/dora/"
video_dir = my_dir + "train/video/"
# param_file_name = my_dir + "train/model/trained_dora_model_24x24_3x3x16.prm"
param_file_name = my_dir + "train/model/trained_dora_model_32x32.prm"
class_names = ["forward", "left", "right", "backward"]    # from ROBOT-C bot.c
nclasses = len(class_names)
size = H, W

be = gen_backend(backend='cpu', batch_size=1)    # NN backend
init_uni = Uniform(low=-0.1, high=0.1)           # Unnecessary NN weight initialization
bn = True                                        # enable NN batch normalization
layers = [Conv((5, 5, 16), init=init_uni, activation=Rectlin(), batch_norm=bn),
          Pooling((2, 2)),
          Conv((3, 3, 32), init=init_uni, activation=Rectlin(), batch_norm=bn),
          Pooling((2, 2)),
          Affine(nout=50, init=init_uni, activation=Rectlin(), batch_norm=bn),
          Affine(nout=nclasses, init=init_uni, activation=Softmax())]
model = Model(layers=layers)
model.load_params(param_file_name, load_states=False)

# Motor setup
mh = Adafruit_MotorHAT(addr=0x60)
right_motor = mh.getMotor(1)
left_motor = mh.getMotor(3)

file_name_prefix = video_dir + file_name_prefix

camera = picamera.PiCamera()
camera.resolution = (w, h)
if fps > 0:
  camera.framerate = fps
if iso > 0:
  camera.iso = iso
camera.hflip = hor_flip
camera.vfilp = ver_flip
camera.led = False
camera.exposure_mode = 'fixedfps'

def rm_files(file_path_name):
  command = "rm " + file_path_name #+ " 2> /dev/null"
  subprocess.call(command, shell=True)

class AutonomousThread (threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    self.daemon = True
    debug_print("Autonomous thread init")
    self.cnt = 0
	rm_files(my_dir + "train/debug/*")

  def run(self):
    while True:
      if not autonomous:
        debug_print("Exiting autonomous thread")
        break

      # Grab a still frame
      stream = picamera.array.PiRGBArray(camera)
      camera.capture(stream, 'rgb', use_video_port=True)

      debug_print("Grabbed a still frame")
      start_time = time.time()
      image = Image.fromarray(stream.array)
      image = image.resize(size, Image.ANTIALIAS)
      if (debug):
        image.save(my_dir + "train/debug/capture" + str(self.cnt) + ".png", "PNG")
        self.cnt = self.cnt + 1
      r, g, b = image.split()
      image = Image.merge("RGB", (b, g, r))
      image = np.asarray(image, dtype=np.float32)
      image = np.transpose(image, (2, 0, 1))
      x_new = image.reshape(1, 3*W*H) - 127

      # Run neural network
      inference_set = ArrayIterator(x_new, None, nclass=nclasses, lshape=(3, H, W))
      out = model.get_outputs(inference_set)
      debug_print("--- %s seconds per decision --- " % (time.time() - start_time))
      decision = out.argmax()
      debug_print(class_names[decision])
      send_cmd(decision)

def get_file_max_idx(prefix, file_ext):
  rs = "[0-9][0-9][0-9][0-9][0-9]"
  file_names = glob.glob(prefix + rs + file_ext)
  if not file_names:
    return 0
  numbers = [int((re.findall('\d+', s))[0]) for s in file_names]
  return max(numbers) + 1

def start_recording():
  global log_file, video_file_name, log_file_name
  if not(camera.recording):
    n1 = get_file_max_idx(file_name_prefix, video_file_ext)
    n2 = get_file_max_idx(file_name_prefix, log_file_ext)
    n = max(n1, n2)
    s = str(n).zfill(5)
    video_file_name = file_name_prefix + s + video_file_ext
    log_file_name = file_name_prefix + s + log_file_ext
    camera.start_recording(video_file_name, quality=quality)
    log_file = open(log_file_name, "w")
    camera.led = True

    debug_print("Recording to " + log_file_name)
    return True
  else:
    return False

def stop_recording():
  global log_file
  if camera.recording:
    debug_print("Stopping recording")
    camera.stop_recording()
    log_file.close()
    camera.led = False

def enable_autonomous_driving(enable):
  global autonomous, autonomous_thread
  if (not autonomous) and enable:
    # going autonomous?
    # Stop recording
    stop_recording()
    # camera.start_preview()
    # configure capturing frames into buffer (not on disk)
    autonomous = True
    autonomous_thread = AutonomousThread()
    autonomous_thread.start()
  elif autonomous and not enable:
    # going manual
    # camera.stop_preview()
    autonomous = False
    autonomous_thread.join()
    debug_print("Autonomous thread has terminated")
    autonomous_thread = []

def write_to_log(txt):
  if camera.recording:
    # Prepend timestamp
    s = repr(time.time()) + " " + txt
    # Save all commands into log file
    debug_print(s)
    log_file.write(s)

def debug_print(s):
  if debug:
    print(s)

# Disable motors on script shutdown
def turnOffMotors():
  mh.getMotor(1).run(Adafruit_MotorHAT.RELEASE)
  mh.getMotor(2).run(Adafruit_MotorHAT.RELEASE)
  mh.getMotor(3).run(Adafruit_MotorHAT.RELEASE)
  mh.getMotor(4).run(Adafruit_MotorHAT.RELEASE)

def set_speed(speed):
  if speed > 255:
    speed = 255
  elif speed < 10:
    speed = 10
  motor_speed = speed
  left_motor.setSpeed(speed)
  right_motor.setSpeed(speed)

# Control over network
@webiopi.macro
def go_forward():
    left_motor.run(Adafruit_MotorHAT.BACKWARD)
    right_motor.run(Adafruit_MotorHAT.FORWARD)

@webiopi.macro
def go_backward():
  left_motor.run(Adafruit_MotorHAT.FORWARD)
  right_motor.run(Adafruit_MotorHAT.BACKWARD)

@webiopi.macro
def turn_left():
  left_motor.run(Adafruit_MotorHAT.BACKWARD)
  right_motor.run(Adafruit_MotorHAT.RELEASE)

@webiopi.macro
def turn_right():
  left_motor.run(Adafruit_MotorHAT.RELEASE)
  right_motor.run(Adafruit_MotorHAT.FORWARD)

@webiopi.macro
def stop():
  left_motor.run(Adafruit_MotorHAT.RELEASE)
  right_motor.run(Adafruit_MotorHAT.RELEASE)

@webiopi.macro
def shutdown_pi():
  os.system("sudo shutdown now -h")

# Called by WebIOPi at script loading
def setup():
  set_speed(default_motor_speed)
  stop()

# Called by WebIOPi at server shutdown
def destroy():
  turnOffMotors()
  stop_recording()
  enable_autonomous_driving(False)
