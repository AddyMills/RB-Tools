import common.classes as cls
import common.dicts
from mido import tick2second as t2s
from mido import Message, MetaMessage, MidiFile, MidiTrack, merge_tracks
from mido import second2tick as s2t

RB4 = cls.RBlipData(4)

tpb = 480

def defaultMidi():
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)
    track.append(MetaMessage('set_tempo', tempo=500000, time=0))
    track.append(MetaMessage('time_signature', numerator=4, denominator=4, time=0))
    return mid

def genFrameData(rbsong, frameCount, visemes, lipstart):
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

    return visemeData, frameDataNum, frameDataName

def genRB2LipData(header, vData):
    tempArray = bytearray()
    tempArray.extend(header.version + header.revision + header.dtaImport + header.embedDTB + header.unknown1)
    tempArray.extend(vData)
    tempArray.extend(header.propAnim)
    return tempArray

def getStart(lipsync, lipdata = RB4):
    DTAImport, DTABytes, start = readFourBytes(lipsync, 8, lipdata)
    return DTAImport

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
                x.append(cls.tempoMapItem(totalTime, msg.tempo, msg.tempo))
                z.append(totalTime)
                y = y + 1
            elif y == 1:
                avgTempo = x[y - 1].tempo
                x.append(cls.tempoMapItem(totalTime, msg.tempo, avgTempo))
                z.append(totalTime)
                y = y + 1
            else:
                avgTempo = rollingAverage(x[y - 1].time, totalTime, avgTempo, x[y - 1].tempo)
                x.append(cls.tempoMapItem(totalTime, msg.tempo, avgTempo))
                z.append(totalTime)
                y = y + 1

    return x, z

def readFourBytes(anim, start, lipdata=RB4):
    x = []
    for y in range(4):  # Iterate through the 4 bytes that make up the starting number
        x.append(anim[start])
        start += 1
    xBytes = bytearray(x)
    x = int.from_bytes(xBytes, lipdata.endian)
    return x, xBytes, start

def returnSeconds(avgTick, avgTempo, tick, tempo):
    seconds = t2s(avgTick, tpb, avgTempo) + t2s(tick, tpb, tempo)
    return seconds

def rollingAverage(x, y, z, a):  # x = prevTime, y = curTime, z = avgTempo, a = curTempo
    newTempo = ((x / y) * z) + (a * (y - x) / y)
    return newTempo

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

def toInt(x, lipdata=RB4):
    x = int.from_bytes(x, lipdata.endian)
    return x

def lipsyncEvents(mid):
    singalongs = []

    time = 0
    for x in mid:
        time += x.time
        if x.type == "note_on" or x.type == "note_off":
            singalongs.append(cls.midiEvent(x.note, time, x.type))

    return singalongs