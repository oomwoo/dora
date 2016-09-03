sudo apt-get update
sudo apt-get install libopenblas-dev
sudo apt-get purge python-numpy
sudo apt-get install python-dev
sudo pip install numpy
sudo apt-get install libopencv-dev python-opencv
sudo pip install picamera
sudo apt-get install libyaml-dev libhdf5-dev
sudo apt-get install imagemagick
cd ..
git clone http://github.com/NervanaSystems/neon.git
cd neon $$ sudo make sysinstall
