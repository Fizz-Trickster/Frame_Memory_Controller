# -*- coding: utf-8 -*-
"""
Created on Sat Feb  5 17:00:02 2022

@author: yoonys
"""

import numpy as np

#=====================================================
# Parameter
#=====================================================
MAX_HRES = 512
MAX_VRES = 512

#=====================================================
# Function
#=====================================================
def dec2hex(decVar, hexLen=4, char="0"):
    hexVar   = hex(decVar)
    hexValid = hexVar[2:]
    
    return hexValid.rjust(hexLen, char)
#=====================================================
# Class
#=====================================================
class Image:
  def __init__(self, filePath):
    self.filePath = filePath
    self.header = {}
    self.pixelData = np.array([])

class ImageInput(Image):
  def __init__(self, filePath):
    Image.__init__(self, filePath)
    self.readFile()

  def readFile(self):
    file = open(self.filePath, 'r')
    data = file.readlines()
    self.setHeader(data)
    self.setPixelData(data)
    
  def setHeader(self, data):
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
    Image.__init__(self, filePath)
    self.header = header
    self.pixelData = pixelData
    self.writeFile()

  def writeFile(self):
    file = open(self.filePath, 'w')
    file.write('{0}\n'.format(self.header['Format']))
    file.write('{0:<4} {1:<4}\n'.format(self.header['Hres'],self.header['Vres']))
    file.write('{0}\n'.format(self.header['MaxVal']))

    for pixel in self.pixelData:
      file.write('{0:>3} {1:>3} {2:>3}\n'.format(pixel[0], pixel[1], pixel[2]))

class FrameMem:
  def __init__(self, hres, vres):
    self.hres = hres
    self.vres = vres
    self.SP   = 0
    self.EP   = self.hres
    self.SC   = 0
    self.EC   = self.vres
    self.PSC  = 0
    self.PEC  = self.hres
    self.SR   = 0
    self.ER   = self.vres
    self.mem  = np.zeros(shape=(MAX_VRES*MAX_HRES, 3), dtype=int)

  def writeMem(self, pixelData):
    for idx, pixel in enumerate(pixelData):
      addr = idx
      self.mem[addr] = pixel 

  def setPageAddress(self, SP, EP):
    self.SP = SP
    self.EP = EP + 1
    print("Set Start Page Write Address : {0} End Page Write Address : {1}".format(self.SP, self.EP))

  def setColumnAddress(self, SC, EC):
    self.SC = SC
    self.EC = EC + 1
    print("Set Start Column Write Address : {0} End Column Write Address : {1}".format(self.SC, self.EC))
  
  def writePartialMem(self, pixelData):
    for idx, pixel in enumerate(pixelData):
      quo, rem = divmod(idx, (self.EC-self.SC)) 
      addr = (self.hres * (quo + self.SP)) + (rem + self.SC)
      self.mem[addr] = pixel 

  def reshapeMem(self, channel=4):
    self.mem3D = self.mem.reshape(int(MAX_VRES/(channel**(1/2))), int(MAX_HRES/(channel**(1/2))), 3*channel)

  def setPartialRows(self, SR, ER):
    self.SR = SR
    self.ER = ER + 1
    print("Set Start Row Read Address: {0} End Row Read Address: {1}".format(self.SR, self.ER))

  def setPartialColumns(self, PSC, PEC):
    self.PSC = PSC
    self.PEC = PEC + 1
    print("Set Start Column Read Address : {0} End Column Read Address : {1}".format(self.PSC, self.PEC))
    
  def readPartialMem(self):
    self.image  = np.zeros(shape=(MAX_VRES*MAX_HRES, 3), dtype=int)
    
    for idx in range(0, (((self.PEC+1)-self.PSC)*((self.ER+1)-self.SR))):
      quo, rem = divmod(idx, (self.PEC+1)-self.PSC)
      addr = (self.hres * (quo + self.SR)) + (rem + self.PSC)
      self.image[addr] = self.mem[addr] 
      
  def setMovePoint(self, X, Y):
    self.X = X 
    self.Y = Y
    print("Set Move Point X : {0} Move Point Y: {1}".format(self.X, self.Y))

  def moveImage(self):
    self.image  = np.zeros(shape=(MAX_VRES*MAX_HRES, 3), dtype=int)
    for idx in range(0, ((self.hres-self.X)*(self.vres-self.Y))):
      quo, rem = divmod(idx, (self.hres-self.X))
      addr = (self.hres * (quo + self.Y)) + (rem + self.X)
      readidx = (self.hres * quo) + rem
      self.image[addr] = self.mem[readidx] 

class FrameMemCompression(FrameMem):
  def __init__(self, hres, vres):
    FrameMem.__init__(self, hres, vres)
    self.mem = self.mem.reshape((MAX_VRES//2)*(MAX_HRES//2), 12)

  def writeMem(self, pixelData):
    for rowCnt in range(0, MAX_VRES//2):
      for colCnt in range(0, MAX_HRES//2):
        for idx in range(0, 12):
          quo, rem = divmod(idx, 3)
          addr = rowCnt*(MAX_HRES//2)+colCnt
          if idx < 6:
            self.mem[addr][idx] = pixelData[(rowCnt*2*MAX_HRES)+(colCnt*2+quo)][rem]
          else :
            self.mem[addr][idx] = pixelData[((rowCnt*2+1)*MAX_HRES)+(colCnt*2+(quo-2))][rem]

  def readMem(self):
    self.image = np.zeros(shape=(MAX_VRES*MAX_HRES, 3), dtype=int)
    
    for rowCnt in range(0, MAX_VRES):
      for colCnt in range(0, MAX_HRES):
        isEvenRow = (rowCnt % 2 == 0)
        isEvenCol = (colCnt % 2 == 0)
        addr = (rowCnt//2 * MAX_HRES//2) + (colCnt//2)
        if isEvenRow:
          if isEvenCol:
            self.image[rowCnt * MAX_HRES + colCnt] = self.mem[addr][0:3]
          else:
            self.image[rowCnt * MAX_HRES + colCnt] = self.mem[addr][3:6]
        else:
          if isEvenCol:
            self.image[rowCnt * MAX_HRES + colCnt] = self.mem[addr][6:9]
          else:
            self.image[rowCnt * MAX_HRES + colCnt] = self.mem[addr][9:12]

  def writePartialMem(self, pixelData):
    idx = 0
    for rowCnt in range(0, MAX_VRES):
      for colCnt in range(0, MAX_HRES):
        if (rowCnt >= self.SP and rowCnt < self.EP) and (colCnt >= self.SC and colCnt < self.EC):
          isEvenRow = (rowCnt % 2 == 0)
          isEvenCol = (colCnt % 2 == 0)
          addr = (rowCnt//2 * MAX_HRES//2) + (colCnt//2)
          if isEvenRow:
            if isEvenCol:
              self.mem[addr][0: 3] = pixelData[idx]
            else:
              self.mem[addr][3: 6] = pixelData[idx]
          else:
            if isEvenCol:
              self.mem[addr][6: 9] = pixelData[idx]
            else:
              self.mem[addr][9:12] = pixelData[idx]
          idx += 1

    #for idx, pixel in enumerate(pixelData):
    #  quo, rem = divmod(idx, (self.EC-self.SC)) 
    #  addr = (self.hres * (quo + self.SP)) + (rem + self.SC)
    #  self.mem[addr] = pixel 
#=====================================================
# Main
#=====================================================
i_fullImage1 = ImageInput('./image/lena.ppm')
#i_fullImage1 = ImageInput('./image/colorbar.ppm')
i_partImage1 = ImageInput('./image/flag.ppm')

SP = 100 
EP = 223
SC = 100
EC = 223
#=====================================================
# Frame Memory  
#=====================================================
frameMem = FrameMem(i_fullImage1.header['Hres'], i_fullImage1.header['Vres'])
frameMem.writeMem(i_fullImage1.pixelData)
frameMem.setPageAddress(SP, EP)
frameMem.setColumnAddress(SC, EC)
frameMem.writePartialMem(i_partImage1.pixelData)

frameMem.reshapeMem(1)

frameMem.setPartialRows(1, 5)
frameMem.setPartialColumns(2, 5)
frameMem.readPartialMem()

frameMem.setMovePoint(256, 256)
frameMem.moveImage()

#=====================================================
# Frame Memory 2x2 Compression 
#=====================================================
frameMemCompress = FrameMemCompression(i_fullImage1.header['Hres'], i_fullImage1.header['Vres'])
frameMemCompress.writeMem(i_fullImage1.pixelData)

frameMemCompress.setPageAddress(SP, EP)
frameMemCompress.setColumnAddress(SC, EC)
frameMemCompress.writePartialMem(i_partImage1.pixelData)

frameMemCompress.readMem()

#=====================================================
# Image Write  
#=====================================================
o_image1 = ImageOutput('./image/output1.ppm', i_fullImage1.header, frameMemCompress.image)

#o_image1 = ImageOutput('./image/output1.ppm', i_fullImage1.header, frameMem.mem)
#o_image1 = ImageOutput('./image/output1.ppm', i_fullImage1.header, frameMem.image)