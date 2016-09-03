sudo apt-get update
sudo apt-get install python-dev libopenblas-dev libopencv-dev python-opencv libyaml-dev libhdf5-dev
# sudo apt-get purge python-numpy
# sudo pip install numpy
# sudo apt-get install imagemagick
cd ..
git clone http://github.com/NervanaSystems/neon.git
cd neon $$ sudo make sysinstall
sudo pip install picamera
