import os
import sys
import struct
import itertools

import common.classes as cls
import common.functions as fns
import common.dicts as dicts

possVisemes = (
"Neutral", "Eat", "Earth", "If", "Ox", "Oat", "Wet", "Size", "Church", "Fave", "Though", "Told", "Bump", "New", "Roar",
"Cage", "Blink")

class GHlipData:
    def __init__(self):
        self.endian = "little"
        self.opEndian = "big"
        self.visemeCount = dicts.charTypes["32bit"]  # Bit value for number of visemes
        self.visemeItem = dicts.charTypes["32bit"]  # Bit value for viseme entries


GH2 = GHlipData()
framerate = 30

def vocHeader(voc, start):
    dummy, devNameLen, start = fns.readFourBytes(voc, start, GH2)
    devName = []
    for x in range(fns.toInt(devNameLen, GH2)):
        devName.append(chr(voc[start]))
        start += 1
    devName = ''.join(devName)
    start += 2
    dummy, gamemetaLen, start = fns.readFourBytes(voc, start, GH2)
    gamemeta = []
    for x in range(fns.toInt(gamemetaLen, GH2)):
        gamemeta.append(chr(voc[start]))
        start += 1
    gamemeta = ''.join(gamemeta)
    start += 12
    dummy, songnameLen, start = fns.readFourBytes(voc, start, GH2)
    songname = []
    for x in range(fns.toInt(songnameLen, GH2)):
        songname.append(chr(voc[start]))
        start += 1
    songname = ''.join(songname)
    start += 2
    dummy, fileSize, start = fns.readFourBytes(voc, start, GH2)
    start += 2
    dummy, visemeCount, start = fns.readFourBytes(voc, start, GH2)
    return fns.toInt(visemeCount, GH2), start


def pullViseme(voc, start):
    start += 8  # Skip first 8 byte of viseme entry
    dummy, visemeNameLen, start = fns.readFourBytes(voc, start, GH2)
    visemeName = []
    for x in range(fns.toInt(visemeNameLen, GH2)):
        visemeName.append(chr(voc[start]))
        start += 1
    visemeName = ''.join(visemeName)
    start += 8
    dummy, eventNum, start = fns.readFourBytes(voc, start, GH2)
    events = []
    maxValue = 0
    for x in range(fns.toInt(eventNum, GH2)):
        start += 2
        dummy, eventTime, start = fns.readFourBytes(voc, start, GH2)
        eventTime = struct.unpack('<f', eventTime)[0]
        dummy, eventValue, start = fns.readFourBytes(voc, start, GH2)
        if round(struct.unpack('<f', eventValue)[0]) > maxValue:
            maxValue = round(struct.unpack('<f', eventValue)[0])
        eventValue = round(struct.unpack('<f', eventValue)[0] * 255)
        start += 8
        events.append([eventTime, eventValue])

    return visemeName, events, start


def main(voc, exaggerate = 1):
    with open(voc, "rb") as f:
        voc = f.read()
    start = 10
    visemeCount, start = vocHeader(voc, start)
    toConvert = {}
    for x in range(visemeCount):
        visemeName, events, start = pullViseme(voc, start)
        if visemeName in possVisemes:
            toConvert[visemeName] = events
    convertNames = {}
    for x in toConvert:
        maxFrame = toConvert[x].copy()
        if toConvert[x]:
            lastFrame = round(maxFrame[-1][0]*30)
            tempArray = [0] * (lastFrame+1)
            for z, y in enumerate(toConvert[x]):
                tempArray[round(y[0]*30)] = y[1]
                try:
                    z1 = round(y[0]*30)
                    z2 = round(toConvert[x][z+1][0]*30)
                    if x == "Blink":
                        z1_val = round(y[1])
                        z2_val = round(toConvert[x][z+1][1])
                    else:
                        z1_val = round(y[1] * exaggerate)
                        z2_val = round(toConvert[x][z+1][1] * exaggerate)
                except IndexError:
                    z2_val = 0
                frameDiff = z2-z1
                try:
                    valueDiff = (z2_val - z1_val)/frameDiff
                except ZeroDivisionError:
                    valueDiff = 0
                if frameDiff > 1:
                    for i in range(1, frameDiff):
                        tempArray[z1+i] = round((z1_val + (valueDiff*i)))
            if x == 'Blink':
                convertNames[f'{x}'] = tempArray.copy()
            else:
                tempLo = []
                tempHi = []
                for y in tempArray:
                    tempLo.append(round(y*2/3))
                    tempHi.append(round(y*1/3))
                convertNames[f'{x}_lo'] = tempLo.copy()
                convertNames[f'{x}_hi'] = tempHi.copy()
    maxLen = 0
    for x in convertNames:
        if len(convertNames[x]) > maxLen:
            maxLen = len(convertNames[x])
    visemeData = []
    for combo in itertools.zip_longest(*list(convertNames.values()), fillvalue=0):
        visemeData.append(list(combo).copy())
    currFrame = [0] * len(convertNames)
    frames = []
    for y, x in enumerate(visemeData):
        if x != currFrame:
            tempFrame = []
            for j, i in enumerate(x):
                if i != currFrame[j]:
                    tempFrame.extend([j, i])
            frames.append(tempFrame)
        else:
            frames.append(0)
        currFrame = x.copy()
    lipsyncData = []
    for x in frames:
        if x == 0:
            lipsyncData.append(0)
        else:
            if not (len(x)/2).is_integer():
                input("Uneven viseme data found. Please contact AddyMills on Discord (#9593) or GitHub and send me the file you were trying to convert.")
                exit()
            lipsyncData.append(int(len(x)/2))
            for y in x:
                lipsyncData.append(y)
    # print(lipsyncData)
    visemeHeader = bytearray()
    visemeHeader.extend(len(convertNames).to_bytes(4, byteorder='big', signed=False))
    for x in convertNames:
        y = len(x).to_bytes(4, byteorder='big', signed=False) + bytearray(x, 'utf-8')
        visemeHeader.extend(y)
    visemeHeader.extend(len(frames).to_bytes(4, byteorder='big', signed=False))
    visemeHeader.extend(len(lipsyncData).to_bytes(4, byteorder='big', signed=False))
    #print(lipsyncVals)
    visemeHeader.extend(bytearray(lipsyncData))
    lipsyncFile = fns.genRB2LipData(cls.RB2lipsyncHeader(), visemeHeader)
    with open(f'{os.path.splitext(filename)[0]}.lipsync', "wb") as g:
        g.write(lipsyncFile)
    return


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("No file found. Please use a \"voc\" file as an argument when running the script.")
        exit()

    filename = sys.argv[1]

    if len(sys.argv) == 3:
        try:
            if float(sys.argv[2]) >= 1.5:
                exaggerate = 1.5
            else:
                exaggerate = float(sys.argv[2])
        except:
            exaggerate = 1

    if os.path.splitext(filename)[1] != ".voc":
        print("Invalid file found. Please use a \".voc\" file as an argument when running the script.")
        exit()
    if len(sys.argv) == 2:
        main(filename)
    else:
        main(filename, exaggerate)
