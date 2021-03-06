#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec  7 21:07:26 2017

@author: pkreyenb
"""

import pyaudio
import sys
import numpy as np
import matplotlib.pyplot as plt
import aubio as ab

import pygame as pg
pg.font.init() # you have to call this at the start, 
                   # if you want to use this module.
import random

from threading import Thread

import queue
import time

import argparse

item_switch = "drifting_words" # "wobbling_circle", "drifting_words"

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

pg.init()

if args.f:
    screenWidth, screenHeight = 1024, 768
    screen = pg.display.set_mode((screenWidth, screenHeight), pg.FULLSCREEN | pg.HWSURFACE | pg.DOUBLEBUF)

else:
    screenWidth, screenHeight = 600, 600
    screen = pg.display.set_mode((screenWidth, screenHeight))

white = (255, 255, 255)
black = (0, 0, 0)



class Circle(object):
    def __init__(self, x, y, color, size, tone_energy, wobble_scaling, lifetime):
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.init_size = size
        self.energy = tone_energy
        self.wobble_scaling = wobble_scaling
        self.lifetime = lifetime

    def draw(self, surface):
        pg.draw.circle(surface, self.color, (self.x, self.y), self.size)

    def wobble(self, surface):
        self.lifetime -= 1
        self.size = self.init_size + np.int(self.energy*self.wobble_scaling)
#        self.size += self.lifetime*random.randint(np.int(-self.energy*self.wobble_scaling),
#                                                  np.int(self.energy*self.wobble_scaling))
        self.draw(surface)
        
        

def drawColorFromCmap(rand_nummer, colormap):
    rgb_tuple = colormap(rand_nummer)
    return (np.int(rgb_tuple[0]*255), np.int(rgb_tuple[1]*255), np.int(rgb_tuple[2]*255))   


colors = [(229, 244, 227), (93, 169, 233), (0, 63, 145), (255, 255, 255), (109, 50, 109)]
itemList = []
words = ["Frieder Carlo", "Dr. Dr. Hyper!"]
wobble_sizes = [1,0,-1,0]

# initialise pyaudio
p = pyaudio.PyAudio()

clock = pg.time.Clock()

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

item = Circle(screenWidth//2, screenHeight//2,
              random.choice(colors), 100, 0, 1e4, 10)

running = True
while running:
    key = pg.key.get_pressed()

    if key[pg.K_q]:
        running = False
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False
            
    try:
        buffer_size = 2048 # needed to change this to get undistorted audio
        audiobuffer = stream.read(buffer_size, exception_on_overflow=False)
        signal = np.fromstring(audiobuffer, dtype=np.float32)

        pitch_midi = pitch_o(signal)[0]
        pitch_note = ab.midi2note(np.int(pitch_midi))
        pitch_freq = ab.miditofreq(pitch_midi)
        energy = np.sum(signal**2)/len(signal)
#            print(pitch_note)
        sound_features = [pitch_note, pitch_freq, energy]

    except KeyboardInterrupt:
        print("*** Ctrl+C pressed, exiting")
        break

    item.energy = sound_features[2]
    screen.fill(black)
    item.wobble(screen)
                
        
                
    pg.display.flip()
    clock.tick(90)

stream.stop_stream()
stream.close()
pg.display.quit()
