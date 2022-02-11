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

class GraphicRam:
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
    # self.mem = np.empty(shape=(MAX_VRES*MAX_HRES), dtype='U36')

  def writeMem(self, pixelData):
    for idx, pixel in enumerate(pixelData):
      addr = idx
      self.mem[addr] = pixel 

  def setPageAddress(self, SP, EP):
    self.SP = SP
    self.EP = EP
    print("Set Start Page Write Address : {0} End Page Write Address : {1}".format(self.SP, self.EP))

  def setColumnAddress(self, SC, EC):
    self.SC = SC
    self.EC = EC
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
    self.ER = ER
    print("Set Start Row Read Address: {0} End Row Read Address: {1}".format(self.SR, self.ER))

  def setPartialColumns(self, PSC, PEC):
    self.PSC = PSC
    self.PEC = PEC
    print("Set Start Column Read Address : {0} End Column Read Address : {1}".format(self.PSC, self.PEC))
    
  def readPartialMem(self):
    Hidx = self.SR
    self.fmem  = np.zeros(shape=(MAX_VRES*MAX_HRES, 3), dtype=int)
    for idx in range(0, ((self.PEC-self.PSC)*(self.ER-self.SR))):
      if idx % (self.PEC-self.PSC) == 0:
        addr = self.PSC + (Hidx * self.hres)
        Hidx = Hidx + 1 
      else : 
        addr = addr + 1
      self.fmem[addr] = self.mem[addr] 
      
  # def writeMem(self, pixeldata):
  #   for idx, pixel in enumerate(pixeldata):
  #     R = dec2hex(pixel[0], 3)
  #     G = dec2hex(pixel[1], 3)
  #     B = dec2hex(pixel[2], 3)
  #     strdata = R+G+B
  #     self.mem[idx] = strdata 
  #     # Vidx, Hidx = divmod(idx, self.hres) 
  #     # self.mem[Vidx][Hidx] = strdata 

#=====================================================
# Main
#=====================================================
i_fullImage1 = ImageInput('./image/lena.ppm')
#i_fullImage1 = ImageInput('./image/colorbar.ppm')
i_partImage1 = ImageInput('./image/flag.ppm')

gram = GraphicRam(i_fullImage1.header['Hres'], i_fullImage1.header['Vres'])
gram.writeMem(i_fullImage1.pixelData)
#gram.setPageAddress(0, 124)
gram.setPageAddress(100, 224)
#gram.setColumnAddress(0, 124)
gram.setColumnAddress(100, 224)
gram.writePartialMem(i_partImage1.pixelData)

gram.reshapeMem(1)

gram.setPartialRows(1, 500)
gram.setPartialColumns(1, 500)
gram.readPartialMem()

#o_image1 = ImageOutput('./image/output1.ppm', i_fullImage1.header, gram.mem)
o_image1 = ImageOutput('./image/output1.ppm', i_fullImage1.header, gram.fmem)