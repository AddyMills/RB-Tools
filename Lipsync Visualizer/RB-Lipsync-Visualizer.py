import os
import sys
import matplotlib.pyplot as plt
#from multiprocessing import Process
from progress.bar import IncrementalBar as progressBar

#pool_size = 5

charTypes = {
    "8bit" : 1,
    "16bit" : 2,
    "24bit": 3,
    "32bit": 4,
    "64bit": 8
}

class RB2lipsyncHeader:
    def __init__(self):
        self.version = bytearray([0,0,0,0x01])
        self.revision = bytearray([0,0,0,0x02])
        self.dtaImport = bytearray([0,0,0,0])
        self.embedDTB = bytearray([0,0,0,0])
        self.unknown1 = bytearray([0])
        self.propAnim = bytearray([0,0,0,0])
        
class RBlipData:
    def __init__(self, RB):
        if RB == 4:
            self.endian = "little"
        else:
            self.endian = "big"
        if self.endian == "little":
            self.opEndian = "big"
        else:
            self.opEndian = "little"
        self.visemeCount = charTypes["32bit"] # Bit value for number of visemes
        self.visemeItem = charTypes["32bit"] # Bit value for viseme entries

class lipsyncData:
    def __init__(self):
        self.visemeTotal = 0
        self.visemeOrder = []

def lipsyncParts(rbsong): # Figure out starting points for lipsync parts (if present)
    lip1_start = -1
    lip2_start = -1
    lip3_start = -1
    lip4_start = -1
    if rbsong.find(b'RBCharLipSync') == -1:
        print("No lipsync found. Continuing...")
    else:
        lip1_start = rbsong.find(b'frames', rbsong.find(b'RBCharLipSync')) + 10
        if rbsong.find(b'part2_', lip1_start) == rbsong.find(b'part2', lip1_start):
            print("No part 2 lipsync found. Continuing...")
        else:
            lip2_start = rbsong.find(b'frames', lip1_start) + 10
        if rbsong.find(b'part3_', lip1_start) == rbsong.find(b'part3', lip1_start):
            print("No part 3 lipsync found. Continuing...")
        else:
            lip3_start = rbsong.find(b'frames', lip2_start) + 10
        if rbsong.find(b'part4_', lip1_start) == rbsong.find(b'part4', lip1_start):
            print("No part 4 lipsync found. Continuing...")
        else:
            lip4_start = rbsong.find(b'frames', lip3_start) + 10
    return [lip1_start, lip2_start, lip3_start, lip4_start]

def getLipData(rbsong, lipstart, lipdata):
    visemeCount = []
    for x in range(0, lipdata.visemeCount):
        visemeCount.append(rbsong[lipstart])
        lipstart += 1
    if lipdata.endian == "little":
        visemeCount.reverse()
    visemeNum = bytearray(visemeCount) #Use bytearray.append(x) to combine bytearray strings
    visemeCount = int.from_bytes(visemeNum, byteorder="big", signed=False) #Get an int from the 32-bit array to make the counter for the visemes
    visemes = []
    
    for x in range(0, visemeCount):
        visemeName = []
        visemeNameCount = []
        for x in range(0, lipdata.visemeItem):
            visemeNameCount.append(rbsong[lipstart])
            lipstart += 1

        if lipdata.endian == "little":
            visemeNameCount.reverse()
        
        visemeNameLen = int.from_bytes(bytearray(visemeNameCount), byteorder="big", signed=False)

        for x in range(0, visemeNameLen):
            visemeName.append(chr(rbsong[lipstart]))
            lipstart += 1
        visemes.append(''.join(visemeName).capitalize())

    visemeElements = []
    frameCount = []
    for x in range(0, lipdata.visemeItem):
        frameCount.append(rbsong[lipstart])
        lipstart += 1
    if lipdata.endian == "little":
        frameCount.reverse()
    frameByteTemp = bytearray(frameCount) # Number of frames in song. Divide by 30 to get total in seconds.
    frameCount = int.from_bytes(frameByteTemp, byteorder="big", signed=False)

    for x in range(0, lipdata.visemeItem):
        visemeElements.append(rbsong[lipstart])
        lipstart += 1
    if lipdata.endian == "little":
        visemeElements.reverse()

    visemeStart = lipstart # Create copy of viseme starting point

    lipstart = visemeStart #Return to viseme data

    frameDataNum = []
    frameDataName = []
    visemeData = []
    for x in range(0, frameCount):
        if rbsong[lipstart] != 0:
            tempChangeNum = []
            tempChangeName = []
            for y in range(0, rbsong[lipstart]*2+1):
                visemeData.append(rbsong[lipstart])
                if y == 0:
                    changes = rbsong[lipstart]
                    lipstart += 1
                elif y%2 == 1:
                    visemeChange = rbsong[lipstart]
                    tempChangeNum.append(visemeChange)
                    tempChangeName.append(visemes[visemeChange])
                    lipstart += 1
                else:
                    visemeValue = rbsong[lipstart]
                    tempChangeNum.append(visemeValue)
                    tempChangeName.append(visemeValue)
                    lipstart += 1
            frameDataNum.append([changes, tempChangeNum])
            frameDataName.append([changes, tempChangeName])
        else:
            visemeData.append(rbsong[lipstart])
            frameDataNum.append(rbsong[lipstart])
            frameDataName.append(rbsong[lipstart])
            lipstart += 1

    return frameDataNum, visemes

def genRB2LipData(header, vData):
    tempArray = bytearray()
    tempArray.extend(header.version+header.revision+header.dtaImport+header.embedDTB+header.unknown1)
    tempArray.extend(vData)
    tempArray.extend(header.propAnim)
    return tempArray
    
if len(sys.argv) != 2:
    print("No file found. Please use a \".lipsync\" file as an argument when running the script.")
    exit()

filename = sys.argv[1]

if os.path.splitext(filename)[1] != ".lipsync":
    print("Invalid file found. Please use an \".lipsync\" file as an argument when running the script.")
    exit()

with open(filename, "rb") as f:
    s = f.read()

lipdataSep = []
RB2 = RBlipData(2)
header = RB2lipsyncHeader()

lipsyncData, visemes = getLipData(s, 17, RB2)

for x in range(0, len(visemes)): #Lower every 2nd x-axis label
    if x%2 == 1:
        visemes[x] = "\n" + visemes[x]

visemeFrame = []

for x in range(0, len(visemes)):
    visemeFrame.append(0)

visemeState = []

for x, lips in enumerate(lipsyncData):
    if lips == 0:
        pass
    else:
        visemeEdit = -1
        for y in range(0, lips[0]*2):
            if y%2 == 0:
                visemeEdit = lips[1][y]
            else:
                visemeFrame[visemeEdit] = lips[1][y]
    visemeState.append(visemeFrame.copy())

print("Starting image saving.")

fig, ax = plt.subplots(figsize=(19.2, 10.8))
ax.set_title(filename)
ax.set_xlabel('Visemes', fontsize = 20)
ax.set_ylabel('Strength', fontsize = 20)
ax.set_ylim((0,255))
y = len(visemeState)
progress = progressBar('Generating Images', max=y)

for x,item in enumerate(visemeState):
    pc = ax.bar(visemes,item, color = ["#800000","#000099"]) #Each image seems to get a different colour if undefined, so I'm defining an alternating pattern for each image.
    fig.savefig('output/{0}.png'.format(x))
    pc.remove()
    progress.next()