# DORA
Do-it-yourself Open-source Robotic Autonomous vehicle

DORA is a (relatively) simple DIY self-driving bot that you can build (and train) yourself by following instructions at www.oomwoo.com

Unlike the many other remote-controlled (RC) toys, DORA can drive around entirely by itself, fully autonomously.

- DORA uses Raspberry Pi model 2 with camera to image surroundings, "understand" what it "sees" and decide where to drive
- DORA uses a rudimentary Convolutional Neural Network to make decisions. The neural network runs on Raspberry Pi 2 using Nervana (Intel) Neon engine
- DORA is "taught" how to drive by the user (such as yourself). The user "shows" DORA how to drive properly by controlling DORA manually using a joystick - where to turn left, right, keep going forward or back up. As you drive DORA manually around your appartment, DORA keeps recording videos of what DORA's camera "sees" - and also keeps recording all commands from your joystick. These videos and joystick logs are how DORA will "know" how to self-drive autonomously. To finish the training, download these videos and joystick logs from Raspberry Pi to a Linux PC and run a Python script to drain DORA's decision engine.

This project is intended for high-school, college engineering students as well as DIY afficionados of Raspberry Pi, robotics, machine learning and science and engineering of all ages.

# Repository Structure
- dora/rpi2
  Python scripts to run on Raspberry Pi model 2
- dora/vex
  ROBOT-C C code to run on VEX Cortex
- dora/train
  Python scripts to run on a Ubuntu 14.04 Linux PC to train neural network-based decision engine. Uses Nervana (now Intel) Neon as NN training engine.

See all repositories under http://github.com/oomwoo/

# Robot body
DORA's body and motor drive are build using VEX Robotics components, www.veexrobotics.com.
VEX Robotics offers components to build robots, primarily for education purposes, largely aimed at high/middle/elementary school students. 
DORA's body (base) and drive consists of VEX Cortex (ARM-based) CPU and a couple of motors. The Cortex must be connected to a properly-configured Raspberry Pi model 2 over a serial UART cable.

# Revision history
- release 1.0, 2016 September 2016
