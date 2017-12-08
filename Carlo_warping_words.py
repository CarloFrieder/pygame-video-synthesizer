#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec  7 21:16:23 2017

@author: pkreyenb
"""

import pyaudio
import numpy as np
import matplotlib.pyplot as plt
import aubio as ab

import pygame
pygame.font.init() # you have to call this at the start, 
                   # if you want to use this module.
import random

from threading import Thread

import queue
import time

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-input", required=False, type=int, help="Audio Input Device")
parser.add_argument("-f", action="store_true", help="Run in Fullscreen Mode")
args = parser.parse_args()

if not args.input:
    print("No input device specified. Printing list of input devices now: ")
    p = pyaudio.PyAudio()
    for i in range(p.get_device_count()):
        print("Device number (%i): %s" % (i, p.get_device_info_by_index(i).get('name')))
    print("Run this program with -input 1, or the number of the input you'd like to use.")
    exit()

pygame.init()

if args.f:
    screenWidth, screenHeight = 1280, 720
    screen = pygame.display.set_mode((screenWidth, screenHeight), pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF)

else:
    screenWidth, screenHeight = 1280, 720
    screen = pygame.display.set_mode((screenWidth, screenHeight))

white = (255, 255, 255)
black = (0, 0, 0)
        
class TextSurface(object):
    def __init__(self, x, y, color, size, text):
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.text = text
        self.myfont = pygame.font.SysFont('Padauk', self.size)
        self.textsurface = self.myfont.render(self.text, False, self.color)
        self.lifetime = 100
        
    def move(self, increment_x, increment_y):
        self.lifetime -= 1
        self.x +=increment_x
        self.y +=increment_y
        

def drawColorFromCmap(rand_nummer, colormap):
    rgb_tuple = colormap(rand_nummer)
    return (np.int(rgb_tuple[0]*255), np.int(rgb_tuple[1]*255), np.int(rgb_tuple[2]*255))   

itemList = []
words = ["Frieder Carlo", "Dr. Dr. Hyper!"]

# initialise pyaudio
p = pyaudio.PyAudio()

clock = pygame.time.Clock()

# open stream

buffer_size = 4096 # needed to change this to get undistorted audio
pyaudio_format = pyaudio.paFloat32
n_channels = 1
samplerate = 44100
stream = p.open(format=pyaudio_format,
                channels=n_channels,
                rate=samplerate,
                input=True,
                input_device_index=args.input,
                frames_per_buffer=buffer_size)

time.sleep(1)

# setup onset detector
tolerance = 0.8
win_s = 4096 # fft size
hop_s = buffer_size // 2 # hop size
onset = ab.onset("default", win_s, hop_s, samplerate)

pitch_o = ab.pitch("default", win_s, hop_s, samplerate)
pitch_o.set_unit("midi")
pitch_o.set_tolerance(0.9)

sound_features = [] #init empty list to later contain note, freq and energy

q = queue.Queue()

def draw_pygame():
    running = True
    note_counter = 0
    while running:
        key = pygame.key.get_pressed()

        if key[pygame.K_q]:
            running = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if not q.empty():
            note_counter +=1
            b = q.get()
            newItem = TextSurface(random.randint(0, screenWidth), random.randint(0, screenHeight),
                                  drawColorFromCmap(random.randint(0, 255), plt.cm.rainbow),
                                  random.randint(20, 200), random.choice(words))
#           newCircle = TextSurface(screenWidth/6, screenHeight/2,
#                                   drawColorFromCmap(random.randint(0, 255), plt.cm.jet),
#                                   100, random.choice(words))
            itemList.append(newItem)
        for place, item in enumerate(itemList):
            if item.lifetime < 1:
                itemList.pop(place)
            else:
                screen.blit(item.textsurface,(item.x, item.y))
                
            item.move(-1, -1)
                
        pygame.display.flip()
        clock.tick(10)
        

        if note_counter > 20:
            note_counter = 0

def get_onsets():
    while True:
        try:
            buffer_size = 2048 # needed to change this to get undistorted audio
            audiobuffer = stream.read(buffer_size, exception_on_overflow=False)
            signal = np.fromstring(audiobuffer, dtype=np.float32)

            if onset(signal):
                q.put(True)

        except KeyboardInterrupt:
            print("*** Ctrl+C pressed, exiting")
            break


t = Thread(target=get_onsets, args=())
t.daemon = True
t.start()

draw_pygame()
stream.stop_stream()
stream.close()
pygame.display.quit()
