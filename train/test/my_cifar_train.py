#!/usr/bin/env python
# Trains a CIFAR10 model based on Nervana Neon sample code
# Then, tries to recognize an image, sanity-checks recognition
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


num_epochs = 20
classes =["airplane", "automobile", "bird", "cat", "deer",
          "dog", "frog", "horse", "ship", "truck"]
nclasses = len(classes)

from neon.backends import gen_backend
be = gen_backend(backend='cpu', batch_size=128)

from neon.data import load_cifar10
(X_train, y_train), (X_test, y_test), nclass = load_cifar10()

from neon.data import ArrayIterator
train_set = ArrayIterator(X_train, y_train, nclass=nclass, lshape=(3, 32, 32))
test_set = ArrayIterator(X_test, y_test, nclass=nclass, lshape=(3, 32, 32))

from neon.layers import Conv, Affine, Pooling
from neon.initializers import Uniform
from neon.transforms.activation import Rectlin, Softmax
init_uni = Uniform(low=-0.1, high=0.1)
layers = [Conv(fshape=(5,5,16), init=init_uni, activation=Rectlin()),
          Pooling(fshape=2, strides=2),
          Conv(fshape=(5,5,32), init=init_uni, activation=Rectlin()),
          Pooling(fshape=2, strides=2),
          Affine(nout=500, init=init_uni, activation=Rectlin()),
          Affine(nout=nclasses, init=init_uni, activation=Softmax())]

from neon.models import Model
model = Model(layers)

from neon.layers import GeneralizedCost
from neon.transforms import CrossEntropyMulti
cost = GeneralizedCost(costfunc=CrossEntropyMulti())

from neon.optimizers import GradientDescentMomentum, RMSProp
optimizer = GradientDescentMomentum(learning_rate=0.005,
                                    momentum_coef=0.9)

# Set up callbacks. By default sets up a progress bar
from neon.callbacks.callbacks import Callbacks
callbacks = Callbacks(model, train_set)

model.fit(dataset=train_set, cost=cost, optimizer=optimizer,  num_epochs=num_epochs, callbacks=callbacks)

model.save_params("cifar10_model.prm")

# Evaluate performance
from neon.transforms import Misclassification
error_pct = 100 * model.eval(test_set, metric=Misclassification())
print 'Misclassification error = %.1f%%' % error_pct


# Sanity check 1
# an image of a frog from wikipedia
# img_source = "https://upload.wikimedia.org/wikipedia/commons/thumb/5/55/Atelopus_zeteki1.jpg/440px-Atelopus_zeteki1.jpg"
# import urllib
# urllib.urlretrieve(img_source, filename="image.jpg")

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
x_new = np.zeros((128, 3072), dtype=np.float32)
x_new[0] = image.reshape(1, 3072) / 255
show_sample(x_new[0])

inference_set = ArrayIterator(x_new, None, nclass=nclass, lshape=(3, 32, 32))
out = model.get_outputs(inference_set)
print classes[out[0].argmax()] + ", ground truth FROG"


# Sanity check 2
out = model.get_outputs(test_set)
# print out
print "Validation set result:"
print(out.argmax(1))
print "Ground truth:"
print y_test.reshape(10000)
