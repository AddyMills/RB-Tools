import os
import sys
import struct

import common.classes as cls
import common.functions as fns

singalongNames = ("Bass_singalong",
                  "Drum_singalong",
                  "Guitar_singalong",
                  "Singalong",
                  "singalong")

RB4 = cls.RBlipData(4)

def getVisemes(lipsync, start, lipdata):
    singalongViseme = []
    singalongVisemeNum = []
    dummy, visemeCount, start = fns.readFourBytes(lipsync, start, lipdata)
    # print(visemeCount)
    visemeByte = bytearray()
    visemes = []
    for x in range(0, fns.toInt(visemeCount)):
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
    dummy, numParts, start = fns.readFourBytes(lipsync, start, RB4)
    parts = []
    for x in range(0, fns.toInt(numParts)):
        partName = []
        dummy, partLen, start = fns.readFourBytes(lipsync, start, RB4)
        for y in range(0, fns.toInt(partLen)):
            partName.append(chr(lipsync[start]))
            start += 1
        parts.append(''.join(partName).capitalize())
    return parts, start


def lipsyncParts(rbsong):  # Figure out starting points for lipsync parts (if present)
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
    visemeNum = bytearray(visemeCount)  # Use bytearray.append(x) to combine bytearray strings
    visemeByte.extend(visemeNum)
    visemeCount = int.from_bytes(visemeNum, byteorder="big",
                                 signed=False)  # Get an int from the 32-bit array to make the counter for the visemes
    # print(visemeCount)
    visemes = []

    for x in range(0, visemeCount):
        visemeName = []
        visemeNameCount = []
        for x in range(0, lipdata.visemeItem):
            visemeNameCount.append(rbsong[lipstart])
            lipstart += 1
        # print(visemeNameCount)
        if lipdata.endian == "little":
            visemeNameCount.reverse()
        visemeByteTemp = bytearray(visemeNameCount)

        visemeNameLen = int.from_bytes(bytearray(visemeNameCount), byteorder="big", signed=False)
        # print(visemeNameLen)
        for x in range(0, visemeNameLen):
            visemeName.append(chr(rbsong[lipstart]))
            if x == 0:  # RB2/3 have the visemes capitalized, while RB4 does not. This converts the first letter to a capital in hex
                if chr(rbsong[lipstart]) == "e":  # Except if the viseme name starts with "exp" apparently
                    visemeByteTemp.append(rbsong[lipstart])
                else:
                    visemeByteTemp.append(rbsong[lipstart] - 0x20)
            else:
                visemeByteTemp.append(rbsong[lipstart])
            lipstart += 1
        exp_check = visemeByteTemp[4:7]
        if exp_check != b'exp':
            if chr(visemeByteTemp[4]) == 'e':
                visemeByteTemp[4] -= 0x20
        # print(visemeByteTemp)
        # print(exp_check)
        visemes.append(''.join(visemeName).capitalize())
        visemeByte.extend(visemeByteTemp)
    # print(len(visemes), visemes)

    # print(hex(lipstart))
    visemeElements = []
    for x in range(0, lipdata.visemeItem):
        visemeElements.append(rbsong[lipstart])
        lipstart += 1
    # print(visemeNameCount)
    if lipdata.endian == "little":
        visemeElements.reverse()
    visemeElementsTemp = bytearray(visemeElements)

    # print(visemeByte)
    visemeElements = int.from_bytes(visemeElementsTemp, byteorder="big", signed=False)
    frameCount = []
    visemeStart = lipstart  # Create copy of viseme starting point
    lipstart = lipstart + visemeElements  # Go to end of viseme data to find frames
    for x in range(0, lipdata.visemeItem):
        frameCount.append(rbsong[lipstart])
        lipstart += 1
    if lipdata.endian == "little":
        frameCount.reverse()
    frameByteTemp = bytearray(frameCount)  # Number of frames in song. Divide by 30 to get total in seconds.
    frameCount = int.from_bytes(frameByteTemp, byteorder="big", signed=False)
    lipstart = visemeStart  # Return to viseme data
    # print(frameByteTemp)
    visemeByte.extend(frameByteTemp)
    visemeByte.extend(visemeElementsTemp)

    visemeData, frameDataNum, frameDataName = fns.genFrameData(rbsong, frameCount, visemes, lipstart)

    visemeByte.extend(bytearray(visemeData))
    # print(visemeByte)
    return visemeByte

def main_lipsync_new(lipsync):
    with open(lipsync, "rb") as f:  # Open the file
        s = f.read()
    lipsync = s  # Rename lipsync variable for use later on
    frames = []
    header = cls.RB2lipsyncHeader()  # Prepare the RB2/3 header for writing later
    dummy, frameRate, start = fns.readFourBytes(lipsync,
                                     8)  # Grab the framerate. Seems to all be 30, but if not, I can use it later on
    frameRate = round(struct.unpack('<f', frameRate)[0])  # Frame rate is a float

    visemes, singalongs, singalongsNum, start = getVisemes(lipsync, start, RB4)
    lipParts, start = readLipParts(lipsync, start)
    # print(lipParts)
    dummy, frameNum, start = fns.readFourBytes(lipsync, start)
    for x in range(fns.toInt(frameNum)):
        dummy, frameData, start = fns.readFourBytes(lipsync, start)
        frames.append(fns.toInt(frameData))
    currFrame = 0
    lipsyncFile = []

    for x in range(len(lipParts)):
        lipsyncFile.append([])
    # print(frames[:150])

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
        lipsyncVals[i] = fns.genRB2LipData(header, visemeHeader)
    #print(testLipsync)
    #print(lipSingalongs)
    for y, x in enumerate(lipParts):
        with open(f"{y}-Part_{x}.lipsync", "wb") as g:
            g.write(lipsyncVals[y])

    return

def main_rbsong(filename):
    with open(filename, "rb") as f:
        s = f.read()
    parts = lipsyncParts(s)
    lipdataSep = []
    RB4 = cls.RBlipData(4)
    header = cls.RB2lipsyncHeader()
    for x in range(0, len(parts)):
        if parts[x] != -1:
            lipsyncData = getLipData(s, parts[x], RB4)
            lipdataSep.append(fns.genRB2LipData(header, lipsyncData))

    for x in range(0, len(lipdataSep)):
        lipSave = "{0}_part{1}.lipsync".format(os.path.splitext(filename)[0], x + 1)
        with open(lipSave, "wb") as lipFile:
            lipFile.write(lipdataSep[x])


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("No file found. Please use an \"rbsong\" or \"lipsync_ps4\" file as an argument when running the script.")
        exit()

    filename = sys.argv[1]

    if os.path.splitext(filename)[1] != ".rbsong":
        if os.path.splitext(filename)[1] != ".lipsync_ps4":
            if os.path.splitext(filename)[1] != ".lipsync_pc":
                print("Invalid file found. Please use an \".rbsong\" file as an argument when running the script.")
                exit()
            else:
                main_lipsync_new(filename)
        else:
            main_lipsync_new(filename)
    else:
        main_rbsong(filename)