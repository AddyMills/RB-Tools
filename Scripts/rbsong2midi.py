import math
import os
import struct
import sys

import common.classes as cls
import common.functions as fns

from mido import Message, MetaMessage, MidiFile, MidiTrack
from mido import merge_tracks

console = cls.consoleType('PS4')
tpb = 480

# All venue anim parts have 13 unknown bytes after them (always seems to be 13)
# Format: 1 byte, 4 bytes, 4 bytes, 4 bytes
# 4 bytes after these 13 are the first event

animParts = {
    'bass_intensity': b'bass_intensity',
    'guitar_intensity': b'guitar_intensity',
    'drum_intensity': b'drum_intensity',
    'mic_intensity': b'mic_intensity',
    'keyboard_intensity': b'keyboard_intensity',
    'shot_bg': b'shot_bg',
    'shot_bk': b'shot_bk',
    'shot_gk': b'shot_gk',
    'shot_5': b'shot_5',
    'crowd': b'\x05crowd',
    'postproc': b'postproc_interp',
    'fog': b'stagekit_fog',
    'lights': b'lightpreset_interp',
    'keyframe': b'lightpreset_keyframe_interp',
    'spot_guitar': b'spot_guitar',
    'spot_bass': b'spot_bass',
    'spot_drums': b'spot_drums',
    'spot_vocal': b'spot_vocal',
    'spot_keyboard': b'spot_keyboard',
    'part2_sing': b'part2_sing',
    'part3_sing': b'part3_sing',
    'part4_sing': b'part4_sing',
    'world_event': b'world_event'
}

legalProcs = ("[bloom.pp]",
              "[bright.pp]",
              "[clean_trails.pp]",
              "[contrast_a.pp]",
              "[desat_blue.pp]",
              "[desat_posterize_trails.pp]",
              "[film_16mm.pp]",
              "[film_b+w.pp]",
              "[film_blue_filter.pp]",
              "[film_contrast.pp]",
              "[film_contrast_blue.pp]",
              "[film_contrast_green.pp]",
              "[film_contrast_red.pp]",
              "[film_sepia_ink.pp]",
              "[film_silvertone.pp]",
              "[flicker_trails.pp]",
              "[horror_movie_special.pp]",
              "[photo_negative.pp]",
              "[photocopy.pp]",
              "[posterize.pp]",
              "[ProFilm_a.pp]",
              "[ProFilm_b.pp]",
              "[ProFilm_mirror_a.pp]",
              "[ProFilm_psychedelic_blue_red.pp]",
              "[shitty_tv.pp]",
              "[space_woosh.pp]",
              "[video_a.pp]",
              "[video_bw.pp]",
              "[video_security.pp]",
              "[video_trails.pp]")

playerAnim = ['bass_intensity',
              'guitar_intensity',
              'drum_intensity',
              'mic_intensity',
              'keyboard_intensity'
              ]

lights = ['lightpreset',
          'lightpreset_keyframe',
          'world_event',
          'spot_guitar',
          'spot_bass',
          'spot_drums',
          'spot_vocal',
          'part2_sing',
          'part3_sing',
          'part4_sing']

separate = ['postproc',
            'shot_bg',
            'crowd',
            'stagekit_fog']

rest = ['shot_5',  # Potentially for the future
        'spot_keyboard',
        'shot_bk',
        'shot_gk',
        ]

oneVenueTrack = ['lightpreset', 'lightpreset_keyframe', 'world_event', 'spot_guitar', 'spot_bass', 'spot_drums',
                 'spot_keyboard',
                 'spot_vocal', 'part2_sing', 'part3_sing', 'part4_sing', 'postproc', 'shot_bg']

oneVenueSep = ['crowd', 'stagekit_fog']

dataToPull = oneVenueTrack + oneVenueSep

ppDic = {
    'profilm_a': 'ProFilm_a',
    'profilm_b': 'ProFilm_b',
    'profilm_mirror_a': 'ProFilm_mirror_a',
    'profilm_psychedelic_blue_red': 'ProFilm_psychedelic_blue_red'
}

ppDefChange = {  # Change the "filter" effects from RB4 to less annoying ones by default
    "bloom": "ProFilm_a",
    "bright": "ProFilm_a",
    "clean_trails": "ProFilm_a",
    "contrast_a": "ProFilm_a",
    "desat_blue": "ProFilm_a",
    "desat_posterize_trails": "ProFilm_a",
    "film_16mm": "ProFilm_a",
    "film_b+w": "film_b+w",
    "film_blue_filter": "ProFilm_a",
    "film_contrast": "ProFilm_a",
    "film_contrast_blue": "ProFilm_a",
    "film_contrast_green": "ProFilm_a",
    "film_contrast_red": "ProFilm_a",
    "film_sepia_ink": "film_sepia_ink",
    "film_silvertone": "film_silvertone",
    "flicker_trails": "ProFilm_a",
    "horror_movie_special": "ProFilm_b",
    "photo_negative": "film_sepia_ink",
    "photocopy": "photocopy",
    "posterize": "ProFilm_a",
    "ProFilm_a": "ProFilm_a",
    "ProFilm_b": "ProFilm_b",
    "ProFilm_mirror_a": "ProFilm_a",
    "ProFilm_psychedelic_blue_red": "ProFilm_a",
    "shitty_tv": "ProFilm_a",
    "space_woosh": "ProFilm_a",
    "video_a": "ProFilm_a",
    "video_bw": "video_bw",
    "video_security": "ProFilm_a",
    "video_trails": "ProFilm_a"}


def readSixteenBytes(anim, start):
    x = []
    for y in range(16):  # Iterate through the 16 bytes to determine rbsong type
        x.append(chr(anim[start]))
        start += 1
    check = ''.join(x)
    if check == "hidden_in_editor":
        return True
    else:
        return False


def pullEventName(anim, start):
    eventname_loc = b'RBVenueAuthoring'
    eventstart = anim.find(eventname_loc, start) + len(eventname_loc) + 12
    animNameLen, animNameLenByte, eventstart = fns.readFourBytes(anim, eventstart, console)

    animName = []
    for y in range(animNameLen):
        animName.append(chr(anim[eventstart]))
        eventstart += 1
    animName = ''.join(animName)
    # exit()
    return animName


def pullData(anim, start, beat, origPP):
    start_loc = b'driven_prop'
    start = anim.find(start_loc, start) + len(start_loc) + 4
    animName = pullEventName(anim, start)
    if animName not in dataToPull:
        return -1, -1, start
    events, eventsByte, start = fns.readFourBytes(anim, start, console)
    if readSixteenBytes(anim, start):
        start += 43
        events, eventsByte, start = fns.readFourBytes(anim, start, console)

    eventsList = []
    for x in range(events):
        time, timeByte, start = fns.readFourBytes(anim, start)
        eventLen, eventLenByte, start = fns.readFourBytes(anim, start, console)
        event = []
        for y in range(eventLen):
            event.append(chr(anim[start]))
            start += 1
        if not event:
            if eventsList:
                event = eventsList[-1].event
            else:
                eventList = -1
        else:
            event = ''.join(event)
            if event in ppDic:
                event = ppDic[event]
            if origPP == False:
                if event in ppDefChange:
                    event = ppDefChange[event]
        if eventsList != -1:
            roundFloat = round(struct.unpack(console.pack, timeByte)[0], 3)
            splitFloat = math.modf(roundFloat)
            try:
                nextBeatTicks = beat[int(splitFloat[1]) + 1] - beat[int(splitFloat[1])]
                timeFromBeat = round(nextBeatTicks * splitFloat[0])
                timeInSong = beat[int(splitFloat[1])] + timeFromBeat
                eventsList.append(cls.venueItem(timeInSong, event))
            except:
                continue

    # print(animName)
    return eventsList, animName, start

def update_text_event(textEvent):
    if textEvent.startswith('band'):
        textEvent = f'coop{textEvent[4:]}'
    if textEvent.endswith('crowd') and not textEvent.startswith('directed'):
        textEvent = textEvent[:-5] + 'behind'
    if textEvent.endswith('near_head'):
        if textEvent[:7] == 'coop_v_':
            textEvent = textEvent[:-9] + 'closeup'
        else:
            textEvent = textEvent[:-9] + 'closeup_head'
    if textEvent.endswith('near_hand'):
        if textEvent[:7] == 'coop_v_':
            textEvent = textEvent[:-9] + 'closeup'
        else:
            textEvent = textEvent[:-9] + 'closeup_hand'
    return textEvent

def parseData(eventsDict, mid, oneVenue):
    if oneVenue:
        combined = oneVenueTrack
        sep = oneVenueSep
    else:
        combined = lights
        sep = separate
    toMerge = []
    for tracks in combined:
        if tracks in eventsDict:
            if eventsDict[tracks] != -1:
                timeStart = 0
                tempTrack = MidiTrack()
                prevType = 'note_off'
                for y, x in enumerate(eventsDict[tracks]):
                    if x.event == 'none' or not x.event:
                        continue
                    timeVal = x.time - timeStart
                    noteVal = 0
                    if tracks.endswith('_sing') or tracks.startswith('spot_'):
                        if tracks.endswith('_sing'):
                            if tracks.startswith('part2'):
                                noteVal = 87
                            elif tracks.startswith('part3'):
                                noteVal = 85
                            elif tracks.startswith('part4'):
                                noteVal = 86
                            else:
                                print(f"Unknown singalong event found at {x.time}")
                                exit()
                        if tracks.startswith('spot_'):
                            if tracks.endswith('keyboard'):
                                noteVal = 41
                            elif tracks.endswith('vocal'):
                                noteVal = 40
                            elif tracks.endswith('guitar'):
                                noteVal = 39
                            elif tracks.endswith('drums'):
                                noteVal = 38
                            elif tracks.endswith('bass'):
                                noteVal = 37
                            else:
                                print(f"Unknown spotlight event found at {x.time}")
                                exit()
                        if x.event.endswith('on'):
                            if prevType == 'note_on':
                                tempTrack.append(Message('note_off', note=noteVal, velocity=0, time=timeVal))
                                timeStart = x.time
                                tempTrack.append(Message('note_on', note=noteVal, velocity=100, time=0))
                            else:
                                tempTrack.append(Message('note_on', note=noteVal, velocity=100, time=timeVal))
                            prevType = 'note_on'
                        elif x.event.endswith('off'):
                            if timeVal != 0:
                                tempTrack.append(Message('note_off', note=noteVal, velocity=0, time=timeVal))
                                prevType = 'note_off'
                        else:
                            print(f"Unknown state event found at {x.time}")
                            exit()
                    else:
                        if tracks == 'lightpreset':
                            textEvent = f'[lighting ({x.event})]'
                        elif tracks == 'postproc':
                            textEvent = f'[{x.event}.pp]'
                            if 'rb4PP' in locals():
                                if not rb4PP:
                                    if textEvent not in legalProcs:
                                        textEvent = '[ProFilm_a.pp]'
                            else:
                                if textEvent not in legalProcs:
                                    textEvent = '[ProFilm_a.pp]'
                        else:
                            textEvent = f'[{update_text_event(x.event)}]'
                        tempTrack.append(MetaMessage('text', text=textEvent, time=timeVal))
                    timeStart = x.time
                toMerge.append(tempTrack)
    mid.tracks.append(merge_tracks(toMerge))
    if combined == oneVenueTrack:
        mid.tracks[-1].name = "VENUE"
    else:
        mid.tracks[-1].name = "lights"
    for tracks in sep:
        if tracks in eventsDict:
            if eventsDict[tracks] != -1:
                tname = tracks
                mid.add_track(name=tname)
                timeStart = 0
                for y, x in enumerate(eventsDict[tracks]):
                    """mapLower = beat[beat <= x.time].max()
                    if tracks == 'shot_bg':
                        print(mapLower, x.time)"""
                    timeVal = x.time - timeStart
                    if tracks == 'stagekit_fog':
                        textEvent = f'[Fog{x.event.capitalize()}]'
                    elif tracks == 'postproc':
                        textEvent = f'[{x.event}.pp]'
                    else:
                        textEvent = f'[{update_text_event(x.event)}]'
                    mid.tracks[-1].append(MetaMessage('text', text=textEvent, time=timeVal))
                    timeStart = x.time
    # Remove bullshit events from RB4 MIDI
    newMid = MidiFile()
    for y, x in enumerate(mid.tracks):
        if y == 0:
            newMid.add_track()
            newMid.tracks[-1] = x
        elif x.name != "EVENTS":
            newMid.add_track()
            newMid.tracks[-1] = fns.unmellow(x)
        else:
            newMid.add_track()
            # Credit to rjkiv for the below snippet
            event_msgs = [msg.dict() for msg in x]
            for i in range(len(event_msgs)):
                if "text" in event_msgs[i] and "preview" in event_msgs[i]["text"]:
                    event_msgs[i + 1]["time"] += event_msgs[i]["time"]
                    event_msgs.pop(i)
                    break
            for msg in event_msgs:
                if "note_" in msg['type']:
                    newMid.tracks[-1].append(Message.from_dict(msg))
                else:
                    newMid.tracks[-1].append(MetaMessage.from_dict(msg))
    # print(newMid.tracks)
    return newMid


def grabBeatTrack(mid):
    beatNotes = []
    time = 0
    for tracks in mid.tracks:
        if tracks.name == "BEAT":
            for msg in tracks:
                time += msg.time
                if msg.type == "note_on":
                    beatNotes.append(time)
    beatNotes.append(beatNotes[-1] + tpb)

    return beatNotes


metadataTypes = {'Tempo': "symbol", 'Vocal Tonic Note': "enum", 'Vocal Track Scroll Duration Ms': "enum",
                 'Global Tuning Offset': "float", 'Band Fail Sound Event': "symbol", 'Vocal Percussion Patch': "string",
                 'Drum Kit Patch': "string", 'Improv Solo Patch': "symbol", 'Dynamic Drum Fill Override': "int",
                 'Improv Solo Volume Db': "float"}

kitTypes = {
    "kit01": "Default",
    "kit02": "Arena",
    "kit03": "Vintage",
    "kit04": "Trashy",
    "kit05": "Electronic"
}

def pullString(anim, start):
    length, lengthByte, start = fns.readFourBytes(anim, start, console)
    blankArray = []
    for y in range(0, length):
        blankArray.append(chr(anim[start]))
        start += 1
    if length == 0:
        toReturn = ""
    else:
        toReturn = ''.join(blankArray)
    #print(length)
    return toReturn, start


def pullMetaData(anim):
    version = int.from_bytes(anim[0:3], console.endian)
    #print(version)
    start_loc = b'RBSongMetadata'
    if version == 18:
        start = anim.find(start_loc) + len(start_loc) + 12
    else:
        start = anim.find(start_loc) + (
            len(start_loc) * 2) + 4 + 12  # Skip the name twice, length of name once, and 12 bytes afterwards
    #print(start)
    events, eventsByte, start = fns.readFourBytes(anim, start, console)
    #print(events, start)
    metadataEvents = []
    for x in range(0, events):
        toAppend, start = pullString(anim, start)
        metadataEvents.append(toAppend.title().replace('_', " "))
        start += 4
    metadataDict = {}
    for x in range(0, events):
        #print(metadataEvents[x], start)
        if metadataTypes[metadataEvents[x]] == "symbol" or metadataTypes[metadataEvents[x]] == "string":
            toAppend, start = pullString(anim, start)
            if metadataEvents[x] == 'Vocal Percussion Patch' or metadataEvents[x] == 'Band Fail Sound Event':
                start += 1
            #print(toAppend)
            metadataDict[metadataEvents[x]] = toAppend
        elif metadataTypes[metadataEvents[x]] == "enum":
            enumArray = bytearray()
            for y in range(0,8):
                enumArray.append(anim[start])
                start += 1
            metadataDict[metadataEvents[x]] = int.from_bytes(enumArray, console.endian)
        elif metadataTypes[metadataEvents[x]] == "float":
            floatArray = bytearray()
            for y in range(0,4):
                floatArray.append(anim[start])
                start += 1
            metadataDict[metadataEvents[x]] = struct.unpack('f', floatArray)[0]
        elif metadataTypes[metadataEvents[x]] == "int":
            intArray = bytearray()
            for y in range(0,4):
                intArray.append(anim[start])
                start += 1
            metadataDict[metadataEvents[x]] = int.from_bytes(intArray, console.endian)

    return metadataDict


def main(anim, mid, oneVenue = True, rb4PP = False):
    beat = grabBeatTrack(mid)
    start = 0
    eventTotal = anim.count(b'driven_prop')
    # print(eventTotal)
    eventsDict = {}
    for x in range(eventTotal):
        events, eventsName, start = pullData(anim, start, beat, rb4PP)
        # print(eventsName)
        eventsDict[eventsName] = events
    mid = parseData(eventsDict, mid, oneVenue)
    return mid


if __name__ == "__main__":

    if len(sys.argv) == 1:
        print(
            "No file found. Please run this script with a \".rbsong\" file and a MIDI file to merge together")
        input("Press any key to exit")
        exit()
    if sys.argv[1].endswith(".rbsong"):
        with open(sys.argv[1], "rb") as f:
            anim = f.read()
        #try:
        metadata = pullMetaData(anim)
        with open(os.path.splitext(sys.argv[1])[0] + "_metadata.txt", "w") as f:
            for x in metadata:
                if x == "Drum Kit Patch":
                    kitNumber = metadata[x][-12:]
                    f.write(f'{x}: {metadata[x]} ({kitTypes[kitNumber[:5]]})\n')
                else:
                    f.write(f'{x}: {metadata[x]}\n')
            print("Extracted metadata")
        """except:
            print("Metadata failed to extract")"""
        try:
            mid = MidiFile(os.path.splitext(sys.argv[1])[0] + '.mid')
        except:
            print("No midi file found. It must be located in the same folder as your rbsong file.")
            input("Press any key to exit")
            exit()
    else:
        print("No rbsong file found.")
        input("Press any key to exit")
        exit()
    output = os.path.splitext(sys.argv[1])[0]
    if '-rb4' in sys.argv:
        rb4PP = True
    else:
        rb4PP = False
    if '-separate' in sys.argv:
        oneVenue = False
    else:
        oneVenue = True
    mid = main(anim, mid, oneVenue, rb4PP)
    mid.save(filename=f'{output}_venue.mid')
