import picamera, time

# picamera.readthedocs.io

try:
    camera = picamera.PiCamera()
except:
    print "Error instantiating camera"
    print "Did you connect the camera flex cable?"
    print "Trying to connect a USB camera? picamera does not support USB"
    print "Did you run `sudo raspi-config` to enable the camera?"
    exit()

camera.resolution = (320, 240)
camera.framerate = 90
#camera.hflip = True
#camera.vfilp = True
quality = 23
bitrate = 0
#camera.iso = 800
#camera.exposure_mode = 'fixedfps'
camera.exposure_mode = 'sports'

file_name = "video.h264"
seconds_to_record = 5
camera.start_recording(file_name, intra_period=5, quality=quality, bitrate=bitrate)
print "Started recording, camera LED should be ON"
print "Recording for " + str(seconds_to_record) + " seconds into " + file_name
print "Camera resolution = " + repr(camera.resolution)
print "Camera FPS = " + repr(camera.framerate)
print "Camera quality = " + str(quality)
print "Camera ISO = " + str(camera.iso)
print "Camera exposure mode = " + camera.exposure_mode
print "Camera meter mode = " + camera.meter_mode
if bitrate:
    print "Camera bitrate = " + repr(bitrate)
else:
    print "Camera bitrate unlimited"

time.sleep(seconds_to_record)

camera.stop_recording()
print "Stopped recording, camera LED should be OFF"
print "Run `omxplayer " + file_name + "` to view recorded video"
print "To extract frames"
print "  - install `sudo apt-get install libav-tools`"
print "  - run `avconv -i " + file_name + " -qscale 1 %08d.jpg`"

camera.close()
