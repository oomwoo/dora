sudo apt-get update
sudo apt-get purge python-numpy -y
sudo apt-get install python-dev libopenblas-dev libopencv-dev python-opencv libyaml-dev libhdf5-dev -y
cd
git clone http://github.com/NervanaSystems/neon.git
cd neon $$ sudo make sysinstall
sudo pip install picamera
