#!/usr/bin/env python
# Load pre-trained CIFAR10 model
# Try recognizing an image, sanity-check recognition
#
# (c) oomwoo.com 2016
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3.0
# as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License <http://www.gnu.org/licenses/> for details.


from neon.backends import gen_backend
be = gen_backend(backend='cpu', batch_size=1)

from neon.data import ArrayIterator
from neon.layers import Conv, Affine, Pooling
from neon.initializers import Uniform
from neon.transforms.activation import Rectlin, Softmax
init_uni = Uniform(low=-0.1, high=0.1)
layers = [Conv(fshape=(5,5,16), init=init_uni, activation=Rectlin()),
          Pooling(fshape=2, strides=2),
          Conv(fshape=(5,5,32), init=init_uni, activation=Rectlin()),
          Pooling(fshape=2, strides=2),
          Affine(nout=500, init=init_uni, activation=Rectlin()),
          Affine(nout=10, init=init_uni, activation=Softmax())]

print("Before running this script, run my_cifar_train.py to train a CIFAR10 model")
print("Loading pre-trained CIFAR10 model")
from neon.models import Model
model = Model(layers)
model.load_params("cifar10_model.prm", load_states=False)

classes =["airplane", "automobile", "bird", "cat", "deer",
          "dog", "frog", "horse", "ship", "truck"]
nclass = len(classes)


# Sanity check 1
# an image of a frog from wikipedia
# image_source = "https://upload.wikimedia.org/wikipedia/commons/thumb/5/55/Atelopus_zeteki1.jpg/440px-Atelopus_zeteki1.jpg"
# import urllib
# urllib.urlretrieve(image_source, filename="image.jpg")

# crop and resize to 32x32
from PIL import Image
import numpy as np

# To view images, install Imagemagic
def show_sample(x):
    image = x.reshape(3, 32, 32)
    image = np.transpose(image, (1, 2, 0))
    image = Image.fromarray(np.uint8(image * 255))
    image.show()

image = Image.open('frog.jpg')
image = image.crop((0,0,min(image.size),min(image.size)))
image.thumbnail((32, 32))
# image.show()
image = np.asarray(image, dtype=np.float32)     # (width, height, channel)
image = np.transpose(image, (2, 0, 1))  # ArrayIterator expects (channel, height, width)
x_new = image.reshape(1, 3072) / 255
show_sample(x_new)
inference_set = ArrayIterator(x_new, None, nclass=nclass, lshape=(3, 32, 32))
out = model.get_outputs(inference_set)
print classes[out.argmax()] + (", ground truth FROG")


# Sanity check 2
from neon.data import load_cifar10
(X_train, y_train), (X_test, y_test), nclass = load_cifar10()
i = 1
x_new = X_test[i]
x_new = x_new.reshape(1, 3072)
show_sample(x_new)
inference_set = ArrayIterator(x_new, None, nclass=nclass, lshape=(3, 32, 32))
out = model.get_outputs(inference_set)
print classes[out.argmax()] + ", ground truth " + classes[y_test[i][0]]
