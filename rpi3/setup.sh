sudo apt-get update
sudo apt-get purge numpy
# sudo pip uninstall numpy
sudo apt-get install python-dev libopenblas-dev libopencv-dev python-opencv libyaml-dev libhdf5-dev -y
cd
git clone http://github.com/NervanaSystems/neon.git
cd neon $$ sudo make sysinstall
sudo apt-get install imagemagick -y
sudo apt-get install i2c-tools python-smbus -y
sudo pip install picamera
cd
git clone https://github.com/adafruit/Adafruit-Motor-HAT-Python-Library.git
cd Adafruit-Motor-HAT-Python-Library
sudo python setup.py install
cd
wget http://sourceforge.net/projects/webiopi/files/WebIOPi-0.7.1.tar.gz
tar xvzf WebIOPi-0.7.1.tar.gz
rm WebIOPi-0.7.1.tar.gz
cd WebIOPi-0.7.1
wget https://raw.githubusercontent.com/doublebind/raspi/master/webiopi-pi2bplus.patch
patch -p1 -i webiopi-pi2bplus.patch
# patch -p1 -i webiopi-python3.patch
#   diff -u old.c new.c >my.patch
#   change top line in WebIOPi-0.7.1/setup.sh from "python python3" to "python"
#   press n, enter when asked "access over Internet?"
sudo ./setup.sh
# patch -p1 -i webiopi-python3.patch
#   sudo /etc/init.d/webiopi start
#   sudo webiopi -d -c /etc/webiopi/config
# log in to IP:8000, user webiopi, password raspberry
# you should see WebIOPi Main Menu in your browser
# to access bot over internet, register at https://developer.weaved.com/portal/
cd /etc/systemd/system/
sudo wget https://raw.githubusercontent.com/doublebind/raspi/master/webiopi.service
sudo systemctl start webiopi
sudo systemctl enable webiopi
