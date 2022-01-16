import os
import sys
import struct

charTypes = {
    "8bit": 1,
    "16bit": 2,
    "24bit": 3,
    "32bit": 4,
    "64bit": 8
}

singalongNames = ("Bass_singalong",
                  "Drum_singalong",
                  "Guitar_singalong",
                  "Singalong",
                  "singalong")



class RB2lipsyncHeader:
    def __init__(self):
        self.version = bytearray([0, 0, 0, 0x01])
        self.revision = bytearray([0, 0, 0, 0x02])
        self.dtaImport = bytearray([0, 0, 0, 0])
        self.embedDTB = bytearray([0, 0, 0, 0])
        self.unknown1 = bytearray([0])
        self.propAnim = bytearray([0, 0, 0, 0])


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
        self.visemeCount = charTypes["32bit"]  # Bit value for number of visemes
        self.visemeItem = charTypes["32bit"]  # Bit value for viseme entries


class lipsyncData:
    def __init__(self):
        self.visemeTotal = 0
        self.visemeOrder = []


RB4 = RBlipData(4)


def genRB2LipData(header, vData):
    tempArray = bytearray()
    tempArray.extend(header.version + header.revision + header.dtaImport + header.embedDTB + header.unknown1)
    tempArray.extend(vData)
    tempArray.extend(header.propAnim)
    return tempArray

def readFourBytes(anim, start, lipdata=RB4):
    x = []
    for y in range(4):  # Iterate through the 4 bytes that make up the starting number
        x.append(anim[start])
        start += 1
    xBytes = bytearray(x)
    return xBytes, start


def toInt(x, lipdata=RB4):
    x = int.from_bytes(x, lipdata.endian)
    return x


def getVisemes(lipsync, start, lipdata):
    singalongViseme = []
    singalongVisemeNum = []
    visemeCount, start = readFourBytes(lipsync, start, lipdata)
    # print(visemeCount)
    visemeByte = bytearray()
    visemes = []
    for x in range(0, toInt(visemeCount)):
        lenCount = 0
        # y = 0 # Counter for the length of viseme name
        visemeName = []
        visemeNameCount = []
        for z in range(0, lipdata.visemeItem):
            visemeNameCount.append(lipsync[start])
            start += 1
        # print(visemeNameCount)
        if lipdata.endian == "little":
            visemeNameCount.reverse()
        visemeByteTemp = bytearray(visemeNameCount)

        visemeNameLen = int.from_bytes(bytearray(visemeNameCount), byteorder="big", signed=False)
        # print(visemeNameLen)
        for z in range(0, visemeNameLen):
            visemeName.append(chr(lipsync[start]))
            start += 1
        y = ''.join(visemeName).capitalize()
        if y in singalongNames:
            singalongViseme.append(y)
            singalongVisemeNum.append(x)
            # visemes.append(y)
        else:
            visemes.append(y)
        visemeByte.extend(visemeByteTemp)
    return visemes, singalongViseme, singalongVisemeNum, start


def readLipParts(lipsync, start):
    # print(start)
    numParts, start = readFourBytes(lipsync, start)
    parts = []
    for x in range(0, toInt(numParts)):
        partName = []
        partLen, start = readFourBytes(lipsync, start)
        for y in range(0, toInt(partLen)):
            partName.append(chr(lipsync[start]))
            start += 1
        parts.append(''.join(partName).capitalize())
    return parts, start


def main(lipsync):
    with open(lipsync, "rb") as f:  # Open the file
        s = f.read()
    lipsync = s  # Rename lipsync variable for use later on
    frames = []
    header = RB2lipsyncHeader()  # Prepare the RB2/3 header for writing later
    frameRate, start = readFourBytes(lipsync,
                                     8)  # Grab the framerate. Seems to all be 30, but if not, I can use it later on
    frameRate = round(struct.unpack('<f', frameRate)[0])  # Frame rate is a float
    print(frameRate)
    visemes, singalongs, singalongsNum, start = getVisemes(lipsync, start, RB4)
    lipParts, start = readLipParts(lipsync, start)
    # print(lipParts)
    frameNum, start = readFourBytes(lipsync, start)
    for x in range(toInt(frameNum)):
        frameData, start = readFourBytes(lipsync, start)
        frames.append(toInt(frameData))
    currFrame = 0
    lipsyncFile = []

    for x in range(len(lipParts)):
        lipsyncFile.append([])
    # print(frames[:150])
    print(lipsyncFile)
    for x in frames:
        if x != currFrame:
            toGo = x - currFrame
            currFrame = x
            visemeActive = 0
            lipsyncPart = 0
            lipChange = []
            for y in range(toGo):
                # print(y, toGo)
                if visemeActive == 0:
                    if lipsync[start] == 0xff:
                        if lipChange == []:
                            lipsyncFile[lipsyncPart].append(0)
                        else:
                            lipsyncFile[lipsyncPart].append(lipChange.copy())
                            lipChange = []
                        lipsyncPart += 1

                    else:
                        lipChange.append(lipsync[start])
                        visemeActive = 1
                else:
                    lipChange.append(lipsync[start])
                    visemeActive = 0
                start += 1
            # print(lipsyncPart)
            lipsyncFile[lipsyncPart].append(lipChange.copy())
            lipAppend = len(lipParts) - 1
            if lipsyncPart != lipAppend:
                for y in range(lipAppend - lipsyncPart):
                    lipsyncFile[lipsyncPart + y + 1].append(0)
        else:
            for y in range(len(lipParts)):
                lipsyncFile[y].append(0)
    lipsyncVals = [[],[],[],[]]
    for num, lips in enumerate(lipsyncFile):
        for j, i in enumerate(lips):  # Rewrite visemes removing singalong events
            skip = 0
            if i != 0:
                tempList = []
                for z, y in enumerate(i):
                    if z % 2 == 0:
                        if y in singalongsNum:
                            #lipSingalongs[singalongsNum.index(y)].append(j)
                            skip = 1
                        else:
                            tempList.append(y)
                    else:
                        if skip == 1:
                            skip = 0
                        else:
                            tempList.append(y)
                #print(len(tempList))
                if not (len(tempList)/2).is_integer():
                    print(i)
                lipsyncVals[num].append(round(len(tempList)/2))
                lipsyncVals[num].extend(tempList.copy())
            else:
                lipsyncVals[num].append(i)

    for i, lips in enumerate(lipsyncVals):
        visemeHeader = bytearray()
        visemeHeader.extend(len(visemes).to_bytes(4, byteorder='big', signed=False))
        for x in visemes:
            y = len(x).to_bytes(4, byteorder='big', signed=False) + bytearray(x, 'utf-8')
            visemeHeader.extend(y)
        visemeHeader.extend(len(frames).to_bytes(4, byteorder='big', signed=False))
        visemeHeader.extend(len(lips).to_bytes(4, byteorder='big', signed=False))
        #print(lipsyncVals)
        visemeHeader.extend(bytearray(lips))
        lipsyncVals[i] = genRB2LipData(header, visemeHeader)
    #print(testLipsync)
    #print(lipSingalongs)
    for y, x in enumerate(lipParts):
        with open(f"{y}-Part_{x}.lipsync", "wb") as g:
            g.write(lipsyncVals[y])

    # print(lipsyncVals)
    # print(lipSingalongs)
    """for x in range(len(frames)):
        print(lipsyncFile[0][x],lipsyncFile[1][x],lipsyncFile[2][x])"""


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("No file found. Please use an \"lipsync_ps4\" file as an argument when running the script.")
        exit()
    
    filename = sys.argv[1]
    
    if os.path.splitext(filename)[1] != ".lipsync_ps4":
        print("Invalid file found. Please use an \".lipsync_ps4\" file as an argument when running the script.")
        exit()

    main(filename)
