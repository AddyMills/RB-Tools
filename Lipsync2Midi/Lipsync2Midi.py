import os
import sys

import numpy as np
from mido import MetaMessage, MidiFile, MidiTrack
from mido import second2tick as s2t
from mido import tick2second as t2s

# from multiprocessing import Process

# pool_size = 5

charTypes = {
    "8bit": 1,
    "16bit": 2,
    "24bit": 3,
    "32bit": 4,
    "64bit": 8
}

tpb = 480

"""visemeNote = [50, 51, 52, 53, 54, 55, 56, 57, 58, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80,
              81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 105, 106,
              107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127,
              128
              ]
visemeName = ["Default", "Blink", "Brow_up", "Brow_down", "Brow_aggressive", "Brow_dramatic", "Brow_pouty",
              "Brow_openmouthed", "Squint", "Sad", "Rock_1", "Rock_2", "Rock_3", "Rock_4", "exp_rock_normal1",
              "exp_rock_normal2", "exp_rock_normal3", "exp_rock_normal4", "exp_rock_normal5", "exp_rock_normal6",
              "exp_rock_mellow1", "exp_rock_mellow2", "exp_rock_intense1", "exp_rock_intense2", "exp_rock_intense3",
              "exp_rock_intense4", "exp_metal_mellow", "exp_metal_intense_first", "exp_metal_intense",
              "accent_metal_sustain", "accent_metal_wince", "accent_twitch1", "accent_twitch2", "accent_twitch3",
              "accent_twitch4", "accent_twitch5", "accent_twitch6", "accent_twitch7", "accent_twitch8",
              "accent_twitch9", "accent_twitch10", "accent_side", "accent_forward", "accent_forward_snare",
              "accent_forward_kick", "accent_groove_forward", "accent_groove_side_l", "accent_groove_side_r",
              "accent_sustain", "exp_banger_slackjawed_01", "exp_banger_oohface_01", "exp_banger_teethgrit_01",
              "exp_banger_roar_01", "exp_dramatic_happy_eyesopen_01", "exp_dramatic_happy_eyesclosed_01",
              "exp_dramatic_pouty_01", "exp_dramatic_mouthopen_01", "exp_rocker_smile_mellow_01",
              "exp_rocker_smile_intense_01", "exp_rocker_teethgrit_happy_01", "exp_rocker_teethgrit_pained_01",
              "exp_rocker_bassface_cool_01", "exp_rocker_bassface_aggressive_01", "exp_rocker_soloface_01",
              "exp_rocker_shout_eyesopen_01", "exp_rocker_shout_eyesclosed_01", "exp_rocker_shout_quick_01",
              "exp_rocker_slackjawed_01", "exp_spazz_eyesclosed_01", "exp_spazz_snear_mellow_01",
              "exp_spazz_snear_intense_01", "exp_spazz_tongueout_front_01", "exp_spazz_tongueout_side_01",
              ]"""


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


class tempoMapItem:
    def __init__(self, time, tempo, avgTempo):
        self.time = time
        self.tempo = tempo
        self.avgTempo = avgTempo  # Avg Tempo up to that point


class lipsyncData:
    def __init__(self):
        self.visemeTotal = 0
        self.visemeOrder = []


def rollingAverage(x, y, z, a):  # x = prevTime, y = curTime, z = avgTempo, a = curTempo
    newTempo = ((x / y) * z) + (a * (y - x) / y)
    return newTempo


def returnSeconds(avgTick, avgTempo, tick, tempo):
    seconds = t2s(avgTick, tpb, avgTempo) + t2s(tick, tpb, tempo)
    return seconds


def tempMap(mid):
    x = []  # Tempo changes
    z = []  # Ticks of tempo changes
    y = 0  # Event counter
    totalTime = 0  # Cumulative total time
    avgTempo = 0
    for msg in mid.tracks[0]:
        totalTime = totalTime + msg.time
        if msg.type == "set_tempo":  # Just in case there are other events in the tempo map
            if y == 0:
                x.append(tempoMapItem(totalTime, msg.tempo, msg.tempo))
                z.append(totalTime)
                y = y + 1
            elif y == 1:
                avgTempo = x[y - 1].tempo
                x.append(tempoMapItem(totalTime, msg.tempo, avgTempo))
                z.append(totalTime)
                y = y + 1
            else:
                avgTempo = rollingAverage(x[y - 1].time, totalTime, avgTempo, x[y - 1].tempo)
                x.append(tempoMapItem(totalTime, msg.tempo, avgTempo))
                z.append(totalTime)
                y = y + 1

    return x, z


def midiProcessing(mid):
    tempoMap, ticks = tempMap(mid)
    endEvent = 0
    for track in mid.tracks:
        if track.name == "EVENTS":
            for msg in track:
                endEvent += msg.time
                if msg.type == 'text':
                    if msg.text == '[end]':
                        break
    for x, y in enumerate(tempoMap):
        y.seconds = t2s(y.time, tpb, y.avgTempo)
    return tempoMap  # tickList


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


def genRB2LipData(header, vData):
    tempArray = bytearray()
    tempArray.extend(header.version + header.revision + header.dtaImport + header.embedDTB + header.unknown1)
    tempArray.extend(vData)
    tempArray.extend(header.propAnim)
    return tempArray


def songArray(songMap):
    songTime = []
    songSeconds = []
    songTempo = []
    songAvgTempo = []
    for x, y in enumerate(songMap):
        songTime.append(y.time)
        songSeconds.append(y.seconds)
        songTempo.append(y.tempo)
        songAvgTempo.append(y.avgTempo)
    return songTime, songSeconds, songTempo, songAvgTempo


def defaultMidi():
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)
    track.append(MetaMessage('set_tempo', tempo=500000, time=0))
    track.append(MetaMessage('time_signature', numerator=4, denominator=4, time=0))
    return mid

def readFourBytes(anim, start):
    x = []
    for y in range(4):  # Iterate through the 4 bytes that make up the starting number
        x.append(anim[start])
        start += 1
    xBytes = bytearray(x)
    x = int.from_bytes(xBytes, "big")
    return x, xBytes, start

def getStart(lipsync):
    DTAImport, DTAbytes, start = readFourBytes(lipsync, 8)
    return DTAImport


def main(lipsyncs, mid):
    RB = RBlipData(2)


    for b, a in enumerate(lipsyncs):

        with open(a, "rb") as f:
            s = f.read()

        startPos = getStart(s) + 17

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
        songMap = midiProcessing(mid)
        songTime, songSeconds, songTempo, songAvgTempo = songArray(songMap)
        secondsArray = np.array(songSeconds)
        mid.add_track(name=f'LIPSYNC{b + 1}')
        timeStart = 0
        for y, x in enumerate(visemeState):
            # print(x)
            secs = y * (1 / 30)
            mapLower = secondsArray[secondsArray <= secs].max()
            arrIndex = songSeconds.index(mapLower)
            timeFromChange = secs - songSeconds[arrIndex]
            ticksFromChange = s2t(timeFromChange, tpb, songTempo[arrIndex])
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
                        mid.tracks[-1].append(MetaMessage('text', text=textEvent, time=timeVal))
                        timeVal = 0

                prevFrame = x
                timeStart += timeAdd

    mid.save(filename=f'{os.path.splitext(lipsyncs[0])[0]}_lipsync.mid')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("No file found. Please use a \".lipsync\" file as an argument when running the script.")
        exit()

    filename = sys.argv[1]

    if os.path.splitext(filename)[1] != ".lipsync":
        print("Invalid file found. Please use an \".lipsync\" file as an argument when running the script.")
        exit()
    dirname = os.path.dirname(os.path.abspath(filename))
    mid = ""
    lipsyncs = []
    for file in os.listdir(dirname):
        if file.endswith(".lipsync"):
            lipsyncs.append(file)
        if file.endswith(".mid"):
            mid = MidiFile(file)
    if mid == "":
        mid = defaultMidi()

    main(lipsyncs, mid)
