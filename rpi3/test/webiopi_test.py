#!/usr/bin/python
# (c) oomwoo.com
# Distributed under GNU General Public License v3
# Use solely at your own risk
# Absolutely no warranties expressed or implied
import webiopi
from Adafruit_MotorHAT import Adafruit_MotorHAT, Adafruit_DCMotor


default_motor_speed = 150

# Access Adafruit motor board object
mh = Adafruit_MotorHAT(addr=0x60)
right_motor = mh.getMotor(1)
left_motor = mh.getMotor(3)

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

    
# Defaults

# Called by WebIOPi at script loading
def setup():
    set_speed(default_motor_speed)
    stop()

# Called by WebIOPi at server shutdown
def destroy():
    turnOffMotors()
