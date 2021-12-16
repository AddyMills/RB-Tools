import os
import sys

charTypes = {
    "8bit" : 1,
    "16bit" : 2,
    "24bit": 3,
    "32bit": 4,
    "64bit": 8
}

class visemeState:
    def __init__(self):
        self.Blink = 0x0
        self.Brow_aggressive = 0x0
        self.Brow_down = 0x0
        self.Brow_pouty = 0x0
        self.Brow_up = 0x0
        self.Bump_hi = 0x0
        self.Bump_lo = 0x0
        self.Cage_hi = 0x0
        self.Cage_lo = 0x0
        self.Church_hi = 0x0
        self.Church_lo = 0x0
        self.Earth_hi = 0x0
        self.Earth_lo = 0x0
        self.Eat_hi = 0x0
        self.Eat_lo = 0x0
        self.Fave_hi = 0x0
        self.Fave_lo = 0x0
        self.If_hi = 0x0
        self.If_lo = 0x0
        self.New_hi = 0x0
        self.New_lo = 0x0
        self.Oat_hi = 0x0
        self.Oat_lo = 0x0
        self.Ox_hi = 0x0
        self.Ox_lo = 0x0
        self.Roar_hi = 0x0
        self.Roar_lo = 0x0
        self.Size_hi = 0x0
        self.Size_lo = 0x0
        self.Squint = 0x0
        self.Though_hi = 0x0
        self.Though_lo = 0x0
        self.Told_hi = 0x0
        self.Told_lo = 0x0
        self.Wet_hi = 0x0
        self.Wet_lo = 0x0

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
    visemeByte = bytearray()
    visemeNum = bytearray(visemeCount) #Use bytearray.append(x) to combine bytearray strings
    visemeByte.extend(visemeNum)
    visemeCount = int.from_bytes(visemeNum, byteorder="big", signed=False) #Get an int from the 32-bit array to make the counter for the visemes
    #print(visemeCount)
    visemes = []
    
    for x in range(0, visemeCount):
        lenCount = 0
        # y = 0 # Counter for the length of viseme name
        visemeName = []
        visemeNameCount = []
        for x in range(0, lipdata.visemeItem):
            visemeNameCount.append(rbsong[lipstart])
            lipstart += 1
        #print(visemeNameCount)
        if lipdata.endian == "little":
            visemeNameCount.reverse()
        visemeByteTemp = bytearray(visemeNameCount)
        
        visemeNameLen = int.from_bytes(bytearray(visemeNameCount), byteorder="big", signed=False)
        #print(visemeNameLen)
        for x in range(0, visemeNameLen):
            visemeName.append(chr(rbsong[lipstart]))
            if x == 0: #RB2/3 have the visemes capitalized, while RB4 does not. This converts the first letter to a capital in hex
                if chr(rbsong[lipstart]) == "e": #Except if the viseme name starts with "exp" apparently
                    visemeByteTemp.append(rbsong[lipstart])
                else:
                    visemeByteTemp.append(rbsong[lipstart]-0x20)
            else:
                visemeByteTemp.append(rbsong[lipstart])
            lipstart += 1
        exp_check = visemeByteTemp[4:7]
        if exp_check != b'exp':
            if chr(visemeByteTemp[4]) == 'e':
                visemeByteTemp[4] -= 0x20
        #print(visemeByteTemp)
        #print(exp_check)
        visemes.append(''.join(visemeName).capitalize())
        visemeByte.extend(visemeByteTemp)
    #print(len(visemes), visemes)

    #print(hex(lipstart))
    visemeElements = []
    for x in range(0, lipdata.visemeItem):
        visemeElements.append(rbsong[lipstart])
        lipstart += 1
    #print(visemeNameCount)
    if lipdata.endian == "little":
        visemeElements.reverse()
    visemeElementsTemp = bytearray(visemeElements)

    #print(visemeByte)
    visemeElements = int.from_bytes(visemeElementsTemp, byteorder="big", signed=False)
    frameCount = []
    visemeStart = lipstart # Create copy of viseme starting point
    lipstart = lipstart + visemeElements # Go to end of viseme data to find frames
    for x in range(0, lipdata.visemeItem):
        frameCount.append(rbsong[lipstart])
        lipstart += 1
    if lipdata.endian == "little":
        frameCount.reverse()
    frameByteTemp = bytearray(frameCount) # Number of frames in song. Divide by 30 to get total in seconds.
    frameCount = int.from_bytes(frameByteTemp, byteorder="big", signed=False)
    lipstart = visemeStart #Return to viseme data
    #print(frameByteTemp)
    frameDataNum = []
    frameDataName = []
    visemeByte.extend(frameByteTemp)
    visemeByte.extend(visemeElementsTemp)
    visemeData = []
    for x in range(0, frameCount):
        if rbsong[lipstart] != 0:
            #print(hex(lipstart),rbsong[lipstart])
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
            #print(changes, tempChange)
        else:
            visemeData.append(rbsong[lipstart])
            #print(hex(lipstart),rbsong[lipstart])
            frameDataNum.append(rbsong[lipstart])
            frameDataName.append(rbsong[lipstart])
            lipstart += 1
    #print(bytearray(visemeData))
    visemeByte.extend(bytearray(visemeData))
    #print(visemeByte)
    return visemeByte

def genRB2LipData(header, vData):
    tempArray = bytearray()
    tempArray.extend(header.version+header.revision+header.dtaImport+header.embedDTB+header.unknown1)
    tempArray.extend(vData)
    tempArray.extend(header.propAnim)
    return tempArray

if len(sys.argv) != 2:
    print("No file found. Please use an \"rbsong\" file as an argument when running the script.")
    exit()

filename = sys.argv[1]

if os.path.splitext(filename)[1] != ".rbsong":
    print("Invalid file found. Please use an \".rbsong\" file as an argument when running the script.")
    exit()



f = open(filename, "rb")
s = f.read()
parts = lipsyncParts(s)
lipdataSep = []
RB4 = RBlipData(4)
header = RB2lipsyncHeader()
for x in range (0, len(parts)):
    if parts[x] != -1:
        lipsyncData = getLipData(s, parts[x], RB4)
        lipdataSep.append(genRB2LipData(header,lipsyncData))

for x in range(0, len(lipdataSep)):
    lipSave = "{0}_part{1}.lipsync".format(os.path.splitext(filename)[0],x+1)
    lipFile = open(lipSave, "wb")
    lipFile.write(lipdataSep[x])
    lipFile.close()

#print(lipdata)

#print(parts)
#print(s[parts[0]:parts[0]+10])


"""lip1File = open("bytetest.lipsync", "wb")
lip1File.write(lipdata)
lip1File.close()"""

f.close()