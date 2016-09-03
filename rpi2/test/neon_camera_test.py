#!/usr/bin/env python
# Train robot to drive autonomously using Nervana Neon
# See more at https://github.com/oomwoo/
#
# Copyright (C) 2016 oomwoo.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3.0
# as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License <http://www.gnu.org/licenses/> for details.
"""
Train robot to drive autonomously. Use a small convolutional neural network.
"""

import os
import time
import picamera
import picamera.array
import numpy as np
from PIL import Image
from neon.backends import gen_backend
from neon.layers import Affine, Conv, Pooling
from neon.models import Model
from neon.transforms import Rectlin, Softmax
from neon.initializers import Uniform
from neon.data.dataiterator import ArrayIterator


def show_sample(x):
    # Input to CNN - this is what neural network "sees"
    image = x.reshape(3, W, H)
    image = image[[2, 1, 0], :, :]
    image = np.transpose(image, (1, 2, 0))
    image = Image.fromarray(np.uint8(image + 127))
    # image.show()

w = 160
h = 120
W = 32  # CNN input image size
H = W
fps = 90
my_dir = os.path.expanduser("~") + "/dora/"
# param_file_name = my_dir + "train/model/trained_dora_model_24x24_3x3x16.prm"
param_file_name = my_dir + "train/model/trained_dora_model_32x32.prm"
class_names = ["forward", "left", "right", "backward"]  # from ROBOT-C bot.c
nclasses = len(class_names)

# Set up camera
camera = picamera.PiCamera()
camera.resolution = (w, h)
camera.framerate = fps
camera.exposure_mode = 'fixedfps'
# camera.brightness = 70
# camera.contrast = 10

# Capture image
stream = picamera.array.PiRGBArray(camera)
camera.capture(stream, 'rgb', use_video_port=True)
camera.close()
print "Captured image " + repr(stream.array.shape)
image = Image.fromarray(stream.array)
image.show()

# Set up neural network
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

start_time = time.time()

# Convert image to sample
size = H, W
image = image.resize(size, Image.ANTIALIAS)
r, g, b = image.split()
image = Image.merge("RGB", (b, g, r))
image = np.asarray(image, dtype=np.float32)
image = np.transpose(image, (2, 0, 1))
x_new = image.reshape(1, 3*W*H) - 127
show_sample(x_new)

# Run neural network
inference_set = ArrayIterator(x_new, None, nclass=nclasses, lshape=(3, H, W))
out = model.get_outputs(inference_set)
print "Recognized as " + class_names[out.argmax()]

print "--- %s seconds --- " % (time.time() - start_time)
