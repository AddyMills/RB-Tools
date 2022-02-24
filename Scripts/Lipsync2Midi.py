import os
import sys

import common.classes as cls
import common.functions as fns
import numpy as np

def getLipData(rbsong, lipstart, lipdata):
    visemeCount = []
    for x in range(0, lipdata.visemeCount):
        visemeCount.append(rbsong[lipstart])
        lipstart += 1
    if lipdata.endian == "little":
        visemeCount.reverse()
    visemeNum = bytearray(visemeCount)  # Use bytearray.append(x) to combine bytearray strings
    visemeCount = int.from_bytes(visemeNum, byteorder="big",
                                 signed=False)  # Get an int from the 32-bit array to make the counter for the visemes
    visemes = []

    for x in range(0, visemeCount):
        visemeName = []
        visemeNameCount = []
        for y in range(0, lipdata.visemeItem):
            visemeNameCount.append(rbsong[lipstart])
            lipstart += 1

        if lipdata.endian == "little":
            visemeNameCount.reverse()

        visemeNameLen = int.from_bytes(bytearray(visemeNameCount), byteorder="big", signed=False)

        for y in range(0, visemeNameLen):
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
    frameByteTemp = bytearray(frameCount)  # Number of frames in song. Divide by 30 to get total in seconds.
    frameCount = int.from_bytes(frameByteTemp, byteorder="big", signed=False)

    for x in range(0, lipdata.visemeItem):
        visemeElements.append(rbsong[lipstart])
        lipstart += 1
    if lipdata.endian == "little":
        visemeElements.reverse()

    visemeStart = lipstart  # Create copy of viseme starting point

    lipstart = visemeStart  # Return to viseme data

    frameDataNum = []
    frameDataName = []
    visemeData = []
    for x in range(0, frameCount):
        if rbsong[lipstart] != 0:
            tempChangeNum = []
            tempChangeName = []
            for y in range(0, rbsong[lipstart] * 2 + 1):
                visemeData.append(rbsong[lipstart])
                if y == 0:
                    changes = rbsong[lipstart]
                    lipstart += 1
                elif y % 2 == 1:
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
    for y, x in enumerate(visemes):
        if x.startswith("Exp"):
            visemes[y] = x.lower()
        elif x.startswith("Accent"):
            visemes[y] = x.lower()

    return frameDataNum, visemes

def main(lipsyncs, mid):
    RB = cls.RBlipData(2)

    for b, a in enumerate(lipsyncs):

        with open(a, "rb") as f:
            s = f.read()

        startPos = fns.getStart(s) + 17

        lipsyncData, visemes = getLipData(s, startPos, RB)

        visemeFrame = []

        for x in range(0, len(visemes)):
            visemeFrame.append(0)

        visemeState = []
        prevFrame = visemeFrame.copy()
        for x, lips in enumerate(lipsyncData):
            if lips == 0:
                pass
            else:
                visemeEdit = -1
                for y in range(0, lips[0] * 2):
                    if y % 2 == 0:
                        visemeEdit = lips[1][y]
                    else:
                        visemeFrame[visemeEdit] = lips[1][y]
            visemeState.append(visemeFrame.copy())
        songMap = fns.midiProcessing(mid)
        songTime, songSeconds, songTempo, songAvgTempo = fns.songArray(songMap)
        secondsArray = np.array(songSeconds)
        mid.add_track(name=f'LIPSYNC{b + 1}')
        timeStart = 0
        for y, x in enumerate(visemeState):
            # print(x)
            secs = y * (1 / 30)
            mapLower = secondsArray[secondsArray <= secs].max()
            arrIndex = songSeconds.index(mapLower)
            timeFromChange = secs - songSeconds[arrIndex]
            ticksFromChange = fns.s2t(timeFromChange, fns.tpb, songTempo[arrIndex])
            timeVal = songTime[arrIndex] + round(ticksFromChange) - timeStart
            timeAdd = songTime[arrIndex] + round(ticksFromChange) - timeStart

            if timeVal < 0:
                input("Here")
            if prevFrame != x:

                for i, j in enumerate(x):
                    if j != prevFrame[i]:
                        # if y < 5:
                        # print(j)
                        if startPos != 17:
                            textEvent = f'[{visemes[i]} {j} hold]'.lower()
                        else:
                            textEvent = f'[{visemes[i]} {j} hold]'
                        mid.tracks[-1].append(fns.MetaMessage('text', text=textEvent, time=timeVal))
                        timeVal = 0

                prevFrame = x
                timeStart += timeAdd

    mid.save(filename=f'{os.path.splitext(lipsyncs[0])[0]}_lipsync.mid')
    

def mainSplit(lipsyncs, mid):
    RB = cls.RBlipData(2)

    for b, a in enumerate(lipsyncs):

        with open(a, "rb") as f:
            s = f.read()

        startPos = fns.getStart(s) + 17

        lipsyncData, visemes = getLipData(s, startPos, RB)

        visemeFrame = []

        for x in range(0, len(visemes)):
            visemeFrame.append(0)

        visemeState = []
        for x, lips in enumerate(lipsyncData):
            if lips == 0:
                pass
            else:
                visemeEdit = -1
                for y in range(0, lips[0] * 2):
                    if y % 2 == 0:
                        visemeEdit = lips[1][y]
                    else:
                        visemeFrame[visemeEdit] = lips[1][y]
            visemeState.append(visemeFrame.copy())
        songMap = fns.midiProcessing(mid)
        songTime, songSeconds, songTempo, songAvgTempo = fns.songArray(songMap)
        secondsArray = np.array(songSeconds)
        
        # print(len(visemeState), visemes)
        # exit()
        for i, j in enumerate(visemes):
            timeStart = 0
            mid.add_track(name=f'part{b + 1}-{j}')
            # print(j)
            prevFrame = 0
            for y, x in enumerate(visemeState):
                # print(x[i])
                # exit()
                secs = y * (1 / 30)
                mapLower = secondsArray[secondsArray <= secs].max()
                arrIndex = songSeconds.index(mapLower)
                timeFromChange = secs - songSeconds[arrIndex]
                ticksFromChange = fns.s2t(timeFromChange, fns.tpb, songTempo[arrIndex])
                timeVal = songTime[arrIndex] + round(ticksFromChange) - timeStart
                timeAdd = songTime[arrIndex] + round(ticksFromChange) - timeStart

                # print(secs, mapLower, arrIndex, timeFromChange, ticksFromChange, timeVal, timeAdd)
                #if timeVal < 0:
                    #print(secs, timeVal)
                if prevFrame != x[i]:
                    if startPos != 17:
                        textEvent = f'[{visemes[i]} {x[i]} hold]'.lower()
                    else:
                        textEvent = f'[{visemes[i]} {x[i]} hold]'
                    mid.tracks[-1].append(fns.MetaMessage('text', text=textEvent, time=timeVal))
                    timeVal = 0

                    prevFrame = x[i]
                    timeStart += timeAdd

    mid.save(filename=f'{os.path.splitext(lipsyncs[0])[0]}_lipsync-split.mid')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("No file found. Please use a \".lipsync\" file as an argument when running the script.")
        exit()

    filename = sys.argv[1]

    if os.path.splitext(filename)[1] != ".lipsync":
        print("Invalid file found. Please use an \".lipsync\" file as the first argument when running the script.")
        exit()
    dirname = os.path.dirname(os.path.abspath(filename))
    mid = ""
    lipsyncs = []
    for file in os.listdir(dirname):
        if file.endswith(".lipsync"):
            lipsyncs.append(file)
        if file.endswith(".mid"):
            mid = fns.MidiFile(file)
    if mid == "":
        mid = fns.defaultMidi()
    if "-split" in sys.argv:
        mainSplit(lipsyncs, mid)
    else:
        main(lipsyncs, mid)