import os
import struct
import sys
import common.classes as cls
import common.functions as fns
from mido import Message, MetaMessage, MidiFile, MidiTrack
from mido import merge_tracks
from pathlib import Path

console = cls.consoleType('PS4')
tpb = 480

songDtaTypes = {
    "songdta_type": "uint",
    "song_id": "uint",
    "version": "short",
    "game_origin": 18,
    "preview_start": "float",
    "preview_end": "float",
    "name": 256,
    "artist": 256,
    "album_name": 256,
    "album_track_number": "short",
    "album_year": "int",
    "original_year": "int",
    "genre": 64,
    "song_length": "float",
    "guitar": "float",
    "bass": "float",
    "vocals": "float",
    "drum": "float",
    "band": "float",
    "keys": "float",
    "real_keys": "float",
    "tutorial": "byte",
    "album_art": "byte",
    "cover": "byte",
    "vocal_gender": "enum",
    "anim_tempo": 16,
    "has_markup": "byte",
    "vocal_parts": "int",
    "solos": "int",
    "fake": "byte",
    "shortname": 256
}

dataTypes = {
    "uint": 4,
    "short": 2,
    "float": 4,
    "int": 4,
    "byte": 1,
    "enum": 1

}

steps = ["songdta_type", "song_id", "version", "game_origin", "preview_start", "preview_end", "name", "artist",
         "album_name", "album_track_number", 2, "album_year", "original_year", "genre", "song_length", "guitar",
         "bass", "vocals", "drum", "band", "keys", "real_keys", "tutorial", "album_art", "cover", "vocal_gender",
         "anim_tempo", "has_markup", 3, "vocal_parts", "solos", "fake",
         "shortname"
         ]
         
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

def grabSongData(songdta):
    start = 0
    songsFile = {}

    for x in steps:
        if type(x) is int:
            start += x
        else:
            if type(songDtaTypes[x]) is int:
                a = []
#                print(x, songDtaTypes[x])
                for y in range(0, songDtaTypes[x]):
                    if songdta[y+start] == 0:
                        break
                    a.append(songdta[y+start])
                start += songDtaTypes[x]
                a = bytearray(a).decode('utf-8')
                songsFile[x] = a
#                print(x, a)
            else:
                a = []
                for y in range(0, dataTypes[songDtaTypes[x]]):
                    a.append(songdta[y + start])
                a = bytearray(a)
                if songDtaTypes[x] == "float":
                    a = int(round(struct.unpack('<f',a)[0],0))
                else:
                    a = int.from_bytes(a, 'little')
                songsFile[x] = a
                start += dataTypes[songDtaTypes[x]]
#                print(x, a)
    return songsFile
    
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
    metadataValues = []
    for x in range(0, events):
        #print(metadataEvents[x], start)
        if metadataTypes[metadataEvents[x]] == "symbol" or metadataTypes[metadataEvents[x]] == "string":
            toAppend, start = pullString(anim, start)
            if metadataEvents[x] == 'Vocal Percussion Patch' or metadataEvents[x] == 'Band Fail Sound Event':
                start += 1
            #print(toAppend)
            metadataValues.append(toAppend)
        elif metadataTypes[metadataEvents[x]] == "enum":
            enumArray = bytearray()
            for y in range(0,8):
                enumArray.append(anim[start])
                start += 1
            metadataValues.append(int.from_bytes(enumArray, console.endian))
        elif metadataTypes[metadataEvents[x]] == "float":
            floatArray = bytearray()
            for y in range(0,4):
                floatArray.append(anim[start])
                start += 1
            metadataValues.append(struct.unpack('f', floatArray)[0])
        elif metadataTypes[metadataEvents[x]] == "int":
            intArray = bytearray()
            for y in range(0,4):
                intArray.append(anim[start])
                start += 1
            metadataValues.append(int.from_bytes(intArray, console.endian))
            
    metadata_dict = {}
    for x in range(0, events):
        if metadataEvents[x] == "Drum Kit Patch":
            kitNumber = metadataValues[x][-12:]
            metadata_dict[f"{metadataEvents[x]}"] = f"{metadataValues[x]} ({kitTypes[kitNumber[:5]]})"
        else:
            metadata_dict[f"{metadataEvents[x]}"] = f"{metadataValues[x]}"
    return metadata_dict
    
def pullMoggData(dta):
    tracks = []
    pans = []
    vols = []
    which_arr = 0

    mogg_dict = {}

    with open(dta, "r") as f:
        while True:
            line = f.readline().replace("\n","")
            if not line:
                break
            else:
                if "pans" in line:
                    which_arr = 1
                if "vols" in line:
                    which_arr = 2
                if which_arr == 0:
                    tracks.append(line.lstrip())
                elif which_arr == 1:
                    pans.append(line)
                else:
                    vols.append(line)

    pan_values = [float(x) for x in pans[1][4:-1].split(" ")]
    vol_values = [float(x) for x in vols[1][4:-1].split(" ")]

    tracks = tracks[2:-2]
    mogg_dict["drum"] = ""
    for x in range(len(tracks)):
        line = tracks[x]
        if "drum" in line:
            mogg_dict["drum"] += f"{tracks[x+1][1:-1]} "
        elif "bass" in line:
            mogg_dict["bass"] = f"{tracks[x+1][1:-1]}"
        elif "guitar" in line:
            mogg_dict["guitar"] = f"{tracks[x+1][1:-1]}"
        elif "vocals" in line:
            mogg_dict["vocals"] = f"{tracks[x+1][1:-1]}"
        elif "fake" in line:
            mogg_dict["fake"] = f"{tracks[x+1][1:-1]}"

    mogg_dict["drum"] = mogg_dict["drum"].rstrip()
    mogg_dict["pans"] = " ".join(str(x) for x in pan_values)
    mogg_dict["vols"] = " ".join(str(x) for x in vol_values)
    
    return mogg_dict

def main():
    # pass in a folder containing a mid, mogg_dta, songdta_ps4, and rbsong
#    print(len(sys.argv))
    
    # get current working directory
    cwd = Path().absolute()
    files = []
    for ext in ["*.mogg.dta", "*.songdta_ps4", "*.rbsong"]:
        # need songdta_ps4, mogg_dta and rbsong
        files.extend(cwd.glob(f"{sys.argv[1]}/{ext}"))
#    print(files)
    
    songdta_file = []
    songdta_file.extend(cwd.glob(f"{sys.argv[1]}/*.songdta_ps4"))
    if len(songdta_file) != 1:
        print("songdta error")
        exit()
        
    with open(songdta_file[0], "rb") as f:
        songdta = grabSongData(f.read())
    
    print(songdta)
    
    rbsong_file = []
    rbsong_file.extend(cwd.glob(f"{sys.argv[1]}/*.rbsong"))
    if len(rbsong_file) != 1:
        print("rbsong error")
        exit()
        
    with open(rbsong_file[0], "rb") as f:
        rbsong = pullMetaData(f.read())
        
    print(rbsong)
        
    mogg_dta_file = []
    mogg_dta_file.extend(cwd.glob(f"{sys.argv[1]}/*.mogg.dta"))
    if len(mogg_dta_file) != 1:
        print("mogg dta error")
        exit()
        
    mogg_dta = pullMoggData(mogg_dta_file[0])
    
    print(mogg_dta)
    
if __name__ == "__main__":
    main()
