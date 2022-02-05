# -*- coding: utf-8 -*-
"""
Created on Sat Feb  5 17:00:02 2022

@author: yoonys
"""

import numpy as np

class Image:
  header = {}
  pixelData = np.array([])
  def __init__(self, filePath):
    self.filePath = filePath

class ImageInput(Image):
  def __init__(self, filePath):
    Image.__init__(self, filePath)
    self.readFile()

  def readFile(self):
    file = open(self.filePath, 'r')
    data = file.readlines()
    self.setHedaer(data)
    self.setPixelData(data)
    
  def setHedaer(self, data):
    self.header['Format'] = data.pop(0).rstrip()
    self.header['Hres'], self.header['Vres'] = map(int, data.pop(0).split())
    self.header['MaxVal'] = int(data.pop(0).rstrip())

  def setPixelData(self, data):
    ppmData = []
    for pixel in data:
      buf = []
      for subpixel in pixel.split():
        buf.append(int(subpixel))
      ppmData.append(buf)
    self.pixelData = np.array(ppmData)

class ImageOutput(Image):
  def __init__(self, filePath, header, pixelData):
      Image.__init__(filePath)
      self.header = header
      self.pixelData = pixelData
#=====================================================
# Main
#=====================================================

i_image1 = ImageInput('./image/flag.ppm')
i_image2 = ImageInput('./image/lena.ppm')

o_image1 = Image('./image/output1.ppm')