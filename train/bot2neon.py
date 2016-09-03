#!/usr/bin/env python
# Convert recordings captured by a robot to Nervana Neon suite
# for training a neural network
# The robot runs on Raspberry Pi and ROBOTC for VEX EDR
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
Convert robot training data to Nervana Systems Neon format
    - convert video into series of JPG images
    - convert joystick/motor command to target class for training
        - create list of images and target class for neon
"""

import sys
import subprocess
import getopt
import glob
import re
import os
from neon.data import BatchWriter


def usage():
    print "python bot2neon.py"
    print "  Convert video and control recordings into training Neon dataset"
    print "  -w: skip frame extraction, only write batches (after visual inspection)"
    print "  -s n: keep one frame out of each n frames, default no skip"
    print "  -m: horizontal mirror"
    print "  -v: vertical mirror"
    print "  -?: print usage"


def extract_command_value(s, cmd):
    i = s.find(cmd)
    if i == -1:
        return -1
    return int(s[i+1:i+3], 16)


def extract_time(s):
    i = s.find(' ')
    return float(s[0:i])


def rm_files(file_path_name):
    command = "rm -r " + file_path_name #+ " 2> /dev/null"
    subprocess.call(command, shell=True)


def create_dir(dir_path_name):
    command = "mkdir " + dir_path_name #+ " 2> /dev/null"
    subprocess.call(command, shell=True)


hor_flip = False
ver_flip = False
validation_pct = 10
frame_skip = False
skip_frame_extraction = False
my_dir = os.path.expanduser("~") + "/dora/"
video_dir = my_dir + "rpi2/video/"
dataset_dir = my_dir + "train/dataset/"
out_data_dir = my_dir + "train/neon/"

opts, args = getopt.getopt(sys.argv[1:], "mv?ws:")

for opt, arg in opts:
    if opt == '-m':
        hor_flip = not(hor_flip)
    elif opt == '-v':
        ver_flip = not(ver_flip)
    elif opt == '-s':
        frame_skip = int(arg)
    elif opt == '-w':
        skip_frame_extraction = True
    elif opt == '-?':
        usage()
        sys.exit(2)


def extract_frames():
    # Wipe data set directory
    rm_files(dataset_dir)
    create_dir(dataset_dir)

    # Glob recordings
    file_names = glob.glob(video_dir + "*.h264")

    start_frame_number = 1
    class_list = []

    # Iterate over each recording file set
    for video_file_name in file_names:
        print "Extracting frames from " + video_file_name

        # Delete old files
        rm_files(video_dir + "*.jpg")

        # Extract frames from video(s)
        cmd = "avconv -i " + video_file_name + " -qscale 1 "
        if hor_flip or ver_flip or frame_skip:
            cmd += "-vf \""
            if frame_skip:
                cmd += "select=''not(mod(n\," + str(frame_skip) + "))''"
                if hor_flip or ver_flip:
                    cmd += ","
            if hor_flip:
                cmd += "hflip"
                if ver_flip:
                    cmd += ","
            if ver_flip:
                cmd += "vflip"
            cmd += "\""
        cmd += " -start_number " + str(start_frame_number) + " " + video_dir + "%08d.jpg"  # 2>&1"
        subprocess.check_output(cmd, shell=True)

        # Read list of extracted frames and their timestamps
        file_names = glob.glob(video_dir + "[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9].jpg")
        numbers = [int((re.findall('\d+', s))[0]) for s in file_names]

        # Read bot commands and their timestamps
        log_file_name = video_file_name.replace(".h264", ".txt")
        with open(log_file_name) as f:
            lines = f.read().splitlines()

        # note time of the 1st log entry
        log_start_time = extract_time(lines[0])

        # note time of last log entry
        log_end_time = extract_time(lines[-1])

        # One frame time
        frame_period = (log_end_time - log_start_time) / len(numbers)

        frame_times = [(n - start_frame_number) * frame_period for n in numbers]
        print video_file_name + " FPS " + "{:.2f}".format(1 / frame_period)

        frame_file_names = []

        print "Sorting frames ..."
        for l in lines:
            # line has user command?
            i = extract_command_value(l, 'u')
            if i < 0:
                continue
            # get time in seconds from the moment log started
            t = extract_time(l) - log_start_time
            # find image number best matching that time
            frame_times_diff = [abs(ft - t) for ft in frame_times]
            frame_idx = frame_times_diff.index(min(frame_times_diff))
            frame_no = numbers[frame_idx]

            # Create class sub-directory
            subdir_name = str(i)
            if i not in class_list:
                create_dir(dataset_dir + subdir_name)
                class_list.append(i)

            # Add image name + target class to Neon image list
            file_name = str(frame_no).zfill(8) + ".jpg"
            if file_name in frame_file_names:
                continue
            frame_file_names.append(file_name)

            # Move jpg file
            src = video_dir + file_name
            dst = dataset_dir + subdir_name + '/' + file_name
            os.rename(src, dst)

        start_frame_number = max(numbers) + 1

    # Delete unused frames
    rm_files(video_dir + "*.jpg")


# avconv -i video0.avi -vf "select=''not(mod(n\,5))'',showinfo,vflip,hflip"  %08d.jpg
if not skip_frame_extraction:
    extract_frames()

# Write macro-batches
rm_files(out_data_dir + "*")
bw = BatchWriter(out_dir=out_data_dir, image_dir=dataset_dir,
                 macro_size=3072, file_pattern="*.jpg", target_size=0,
                 validation_pct=validation_pct/100.0)
bw.run()

print "Please visually inspect sorted images for errors in " + dataset_dir
print "If you see erroneous images, delete them and rerun this script with -w"
