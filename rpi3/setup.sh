sudo apt-get update
sudo apt-get install python-dev libopenblas-dev libopencv-dev python-opencv libyaml-dev libhdf5-dev -y
cd
git clone http://github.com/NervanaSystems/neon.git
cd neon $$ sudo make sysinstall
sudo apt-get install i2c-tools python-smbus -y
cd
git clone https://github.com/adafruit/Adafruit-Motor-HAT-Python-Library.git
cd Adafruit-Motor-HAT-Python-Library
sudo python setup.py install
