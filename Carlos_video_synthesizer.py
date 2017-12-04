import pyaudio
import sys
import numpy as np
import matplotlib.pyplot as plt
import aubio

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
    screenWidth, screenHeight = 1024, 768
    screen = pygame.display.set_mode((screenWidth, screenHeight), pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF)

else:
    screenWidth, screenHeight = 600, 600
    screen = pygame.display.set_mode((screenWidth, screenHeight))

white = (255, 255, 255)
black = (0, 0, 0)



class Circle(object):
    def __init__(self, x, y, color, size):
        self.x = x
        self.y = y
        self.color = color
        self.size = size

    def shrink(self):
        self.size -= 1
        
class TextSurface(object):
    def __init__(self, x, y, color, size, text):
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.text = text
        self.myfont = pygame.font.SysFont('Wingdings', self.size)
        self.textsurface = self.myfont.render(self.text, False, self.color)
        self.lifetime = 100
        
    def shrink(self):
        self.lifetime -= 1
        self.x -=1
        self.y -=1

def drawColorFromCmap(rand_nummer, colormap):
    rgb_tuple = colormap(rand_nummer)
    return (np.int(rgb_tuple[0]*255), np.int(rgb_tuple[1]*255), np.int(rgb_tuple[2]*255))                        
        

colors = [(229, 244, 227), (93, 169, 233), (0, 63, 145), (255, 255, 255), (109, 50, 109)]
circleList = []
words = ["Frieder Carlo", "Dr. Dr. Hyper!"]
circle_poitions = [(0, 0), (0, screenHeight), (screenWidth, 0), (screenWidth, screenHeight)]

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
onset = aubio.onset("default", win_s, hop_s, samplerate)

q = queue.Queue()

def draw_pygame():
    running = True
    while running:
        key = pygame.key.get_pressed()

        if key[pygame.K_q]:
            running = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if not q.empty():
            b = q.get()
            newCircle = TextSurface(random.randint(0, screenWidth), random.randint(0, screenHeight),
                               drawColorFromCmap(random.randint(0, 255), plt.cm.rainbow),
                               random.randint(20, 200), random.choice(words))
#            newCircle = TextSurface(screenWidth/6, screenHeight/2,
#                               drawColorFromCmap(random.randint(0, 255), plt.cm.jet),
#                               100, random.choice(words))
            circleList.append(newCircle)

#            pygame.draw.circle(screen,
#                             drawColorFromCmap(random.randint(0, 255), plt.cm.jet),
#                             random.choice(circle_poitions), random.randint(20, np.int(0.9*screenWidth)))

        for place, circle in enumerate(circleList):
            if circle.lifetime < 1:
                circleList.pop(place)
            else:
                screen.blit(circle.textsurface,(circle.x, circle.y))

            circle.shrink()
        
        
        pygame.display.flip()
        clock.tick(10)

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
