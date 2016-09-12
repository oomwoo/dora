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
motor_speed_increment = 20
debug = True
fps = 30
w = 160
h = 120
quality = 23
bitrate = 0
file_name_prefix = "rec"
hor_flip = True
ver_flip = True
video_file_ext = ".h264"
log_file_ext = ".txt"

global autonomous, camera, autonomous_override
autonomous = False
autonomous_override = False
log_file = []
video_file_name = []
log_file_name = []
autonomous_thread = []
camera = []
USER_CMD_DRIVE_FORWARD = 0
USER_CMD_TURN_LEFT = 1
USER_CMD_TURN_RIGHT = 2
USER_CMD_DRIVE_BACKWARD = 3
USER_CMD_NONE = 4

# CNN setup
W = 32
H = W
my_dir = "/home/pi/dora/"
video_dir = my_dir + "train/video/"
# param_file_name = my_dir + "train/model/trained_dora_model_24x24_3x3x16.prm"
param_file_name = my_dir + "train/model/trained_dora_model_32x32.prm"
class_names = ["forward", "left", "right", "backward"]    # from ROBOT-C bot.c
nclasses = len(class_names)
size = H, W
file_name_prefix = video_dir + file_name_prefix
last_user_cmd = USER_CMD_NONE

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

def open_camera():
  global camera
  if camera != []:
    camera.close()

  debug_print("Opening camera")
  camera = picamera.PiCamera()
  camera.resolution = (w, h)
  if fps > 0:
    camera.framerate = fps
  camera.hflip = hor_flip
  camera.vflip = ver_flip
  #  camera.exposure_mode = 'fixedfps'
  time.sleep(0.2)  # Let camera exposure settle

def close_camera():
  global camera
  if camera != []:
    debug_print("Closing camera")
    camera.close()
    camera = []

def is_camera_recording():
  if camera == []:
    return False
  return camera.recording

def rm_files(file_path_name):
  command = "rm " + file_path_name #+ " 2> /dev/null"
  subprocess.call(command, shell=True)

def debug_start_timing():
  if debug:
    global start_time
    start_time = time.time()

def debug_stop_timing():
  if debug:
    debug_print("--- %s seconds per decision --- " % (time.time() - start_time))

def drive(cmd):
  if cmd == USER_CMD_DRIVE_FORWARD:
    left_motor.run(Adafruit_MotorHAT.BACKWARD)
    right_motor.run(Adafruit_MotorHAT.FORWARD)
  elif cmd == USER_CMD_TURN_LEFT:
    left_motor.run(Adafruit_MotorHAT.BACKWARD)
    right_motor.run(Adafruit_MotorHAT.RELEASE)
  elif cmd == USER_CMD_TURN_RIGHT:
    left_motor.run(Adafruit_MotorHAT.RELEASE)
    right_motor.run(Adafruit_MotorHAT.FORWARD)
  elif cmd == USER_CMD_DRIVE_BACKWARD:
    left_motor.run(Adafruit_MotorHAT.FORWARD)
    right_motor.run(Adafruit_MotorHAT.BACKWARD)
  else:
    stop_motors()

def drive_and_log(cmd):
  global autonomous_override
  autonomous_override = True
  drive(cmd)
  write_to_log(cmd)

class AutonomousThread (threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    self.daemon = True
    debug_print("Autonomous thread init")
    self.cnt = 0
    rm_files(my_dir + "train/debug/*")

  def run(self):
    global camera, autonomous_override
    open_camera()
    
    while True:
      if not autonomous:
        debug_print("Exiting autonomous thread")
        close_camera()
        turn_off_motors()
        break

      if autonomous_override:
        time.sleep(0)
        continue

      # Grab a still frame
      stream = picamera.array.PiRGBArray(camera)
      camera.capture(stream, 'rgb', use_video_port=False)

      debug_print("Grabbed a still frame")
      debug_start_timing()
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

      if autonomous_override:
        time.sleep(0)
        continue

      # Run neural network
      inference_set = ArrayIterator(x_new, None, nclass=nclasses, lshape=(3, H, W))
      out = model.get_outputs(inference_set)
      debug_stop_timing()
      decision = out.argmax()
      debug_print(class_names[decision])

      if not autonomous_override:
        drive(decision)

def get_file_max_idx(prefix, file_ext):
  rs = "[0-9][0-9][0-9][0-9][0-9]"
  file_names = glob.glob(prefix + rs + file_ext)
  if not file_names:
    return 0
  numbers = [int((re.findall('\d+', s))[0]) for s in file_names]
  return max(numbers) + 1

def start_recording():
  if autonomous:
    return False

  global log_file, video_file_name, log_file_name, camera

  debug_print("Starting recording");  
  if camera == []:
    open_camera()
  
  if not(camera.recording):
    n1 = get_file_max_idx(file_name_prefix, video_file_ext)
    n2 = get_file_max_idx(file_name_prefix, log_file_ext)
    n = max(n1, n2)
    s = str(n).zfill(5)
    global log_file_name_no_ext
    log_file_name_no_ext = file_name_prefix + s
    video_file_name = log_file_name_no_ext + video_file_ext
    log_file_name = log_file_name_no_ext + log_file_ext
    camera.start_recording(video_file_name, quality=quality)
    log_file = open(log_file_name, "w")
    do_write_to_log(USER_CMD_NONE);

    debug_print("Recording to " + log_file_name)
    return True
  else:
    return False

def stop_recording():
  if is_camera_recording():
    global log_file, camera
    debug_print("Stopping recording")
    camera.stop_recording()
    log_file.close()
    close_camera()
    global log_file_name_no_ext
    os.system("sudo chown pi:pi " + log_file_name_no_ext + ".*")

def enable_autonomous_driving(enable):
  global autonomous, autonomous_thread
  if (not autonomous) and enable:
    stop_recording()
    autonomous = True
    autonomous_thread = AutonomousThread()
    autonomous_thread.start()
  elif autonomous and not enable:
    autonomous = False
    autonomous_thread.join()
    debug_print("Autonomous thread has terminated")
    autonomous_thread = []

def write_to_log(cmd):
  global last_user_cmd
  if not autonomous and camera != [] and camera.recording:
    do_write_to_log(last_user_cmd)
    do_write_to_log(cmd)
  last_user_cmd = cmd

def do_write_to_log(cmd):
  global log_file
  s = repr(time.time()) + " u" + repr(cmd)  # Prepend timestamp
  debug_print(s)
  log_file.write(s + "\n")

def debug_print(s):
  if debug:
    print(s)

# Disable motors on script shutdown
def turn_off_motors():
  debug_print("Turning off all motors")
  mh.getMotor(1).run(Adafruit_MotorHAT.RELEASE)
  mh.getMotor(2).run(Adafruit_MotorHAT.RELEASE)
  mh.getMotor(3).run(Adafruit_MotorHAT.RELEASE)
  mh.getMotor(4).run(Adafruit_MotorHAT.RELEASE)

def set_speed(speed):
  global motor_speed
  if speed > 255:
    speed = 255
  elif speed < 10:
    speed = 10
  motor_speed = speed
  left_motor.setSpeed(speed)
  right_motor.setSpeed(speed)

def stop_motors():
  left_motor.run(Adafruit_MotorHAT.RELEASE)
  right_motor.run(Adafruit_MotorHAT.RELEASE)
  write_to_log(USER_CMD_NONE)

# Control over network
@webiopi.macro
def go_forward():
  drive_and_log(USER_CMD_DRIVE_FORWARD)

@webiopi.macro
def go_backward():
  drive_and_log(USER_CMD_DRIVE_BACKWARD)

@webiopi.macro
def turn_left():
  drive_and_log(USER_CMD_TURN_LEFT)

@webiopi.macro
def turn_right():
  drive_and_log(USER_CMD_TURN_RIGHT)

@webiopi.macro
def joystick_release():
  global autonomous_override
  autonomous_override = False
  stop_motors()

@webiopi.macro
def stop():
  global autonomous_override
  autonomous_override = True
  stop_motors()

@webiopi.macro
def shutdown_pi():
  debug_print("Shutting down\n")
  os.system("sudo poweroff")

@webiopi.macro
def toggle_self_driving():
  enable_autonomous_driving(not autonomous)
  return autonomous

@webiopi.macro
def increase_speed():
    set_speed(motor_speed + motor_speed_increment)

@webiopi.macro
def decrease_speed():
    set_speed(motor_speed - motor_speed_increment)

@webiopi.macro
def toggle_recording():
  if is_camera_recording():
    stop_recording()
  elif not autonomous:
    start_recording()
  return is_camera_recording()

@webiopi.macro
def discard_recording():
  if is_camera_recording():
    debug_print("Discarding current recording")
    stop_recording()
    # Delete last video and associated log
    os.remove(video_file_name)
    os.remove(log_file_name)
  return True

@webiopi.macro
def upload_recordings():
  # TODO
  debug_print("Uploading recordings");
  enable_autonomous_driving(False)
  close_camera()
  turn_off_motors()
  return False

# Called by WebIOPi at script loading
def setup():
  set_speed(default_motor_speed)
  stop_motors()

# Called by WebIOPi at server shutdown
def destroy():
  debug_print("Exiting...")
  enable_autonomous_driving(False)
  close_camera()
  turn_off_motors()
