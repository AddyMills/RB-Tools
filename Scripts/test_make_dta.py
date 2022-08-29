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
    for x in range(len(tracks)):
        line = tracks[x]
        if "drum" in line:
            if "drum" not in mogg_dict:
                mogg_dict["drum"] = ""
            mogg_dict["drum"] += f"{tracks[x+1][1:-1]} "
        elif "bass" in line:
            mogg_dict["bass"] = f"{tracks[x+1][1:-1]}"
        elif "guitar" in line:
            mogg_dict["guitar"] = f"{tracks[x+1][1:-1]}"
        elif "vocals" in line:
            mogg_dict["vocals"] = f"{tracks[x+1][1:-1]}"
        elif "fake" in line:
            mogg_dict["fake"] = f"{tracks[x+1][1:-1]}"
        elif "crowd" in line:
            mogg_dict["crowd"] = f"{tracks[x+1][1:-1]}"

    mogg_dict["drum"] = mogg_dict["drum"].rstrip()
    mogg_dict["pans"] = " ".join(str(x) for x in pan_values)
    mogg_dict["vols"] = " ".join(str(x) for x in vol_values)

    mogg_dict["guitar_tracks"] = [int(x) for x in mogg_dict["guitar"].split(" ")]
    mogg_dict["total_tracks"] = len(pan_values)
    
    return mogg_dict
    
def fill_dta_template(song_dict, mogg_dict, rbsong_dict):
#    print(song_dict)
#    print(mogg_dict)
#    print(rbsong_dict)
#    print("\n\n\n")
    dta = []
    dta.append(f"({song_dict['shortname']}")
    dta.append(f"   (name \"{song_dict['name']}\")")
    dta.append(f"   (artist \"{song_dict['artist']}\")")
    if song_dict["cover"] == 0:
        dta.append(f"   (master TRUE)")
    dta.append(f"   (song_id {song_dict['song_id']})")
    
    # song info - tracks, mixing, etc
    dta.append(f"   (song")
    dta.append(f"      (name \"songs/{song_dict['shortname']}/{song_dict['shortname']}\")")
    dta.append(f"      (tracks\n         (")
    for inst in ["drum", "bass", "guitar", "vocals"]:
        if inst in mogg_dict:
            dta.append(f"            ({inst} ({mogg_dict[inst]}))")
    dta.append(f"         )\n      )")
    if "crowd" in mogg_dict:
        dta.append(f"      (crowd_channels {mogg_dict['crowd']})")
    if song_dict["vocal_parts"] > 1:
        dta.append(f"      (vocal_parts {song_dict['vocal_parts']})")
    dta.append(f"      (pans ({mogg_dict['pans']}))")
    dta.append(f"      (vols ({mogg_dict['vols']}))")
    cores = [-1] * mogg_dict["total_tracks"]
    for n in mogg_dict["guitar_tracks"]:
        cores[n] = 1
    cores = " ".join(str(x) for x in cores)
    dta.append(f"      (cores ({cores}))")
    dta.append(f"      (drum_solo (seqs (kick.cue snare.cue tom1.cue tom2.cue crash.cue)))")
    dta.append(f"      (drum_freestyle (seqs (kick.cue snare.cue hat.cue ride.cue crash.cue)))\n   )")
    
    # vocal percussion and drum kit banks
    if "cowbell" in rbsong_dict["Vocal Percussion Patch"]:
        dta.append(f"   (bank sfx/cowbell_bank.milo)")
    elif "handclap" in rbsong_dict["Vocal Percussion Patch"]:
        dta.append(f"   (bank sfx/handclap_bank.milo)")
    else:
        dta.append(f"   (bank sfx/tambourine_bank.milo)")
    dta.append(f"   (drum_bank sfx/{rbsong_dict['Drum Kit Patch'].replace('fusion/patches/','')[:5]}_bank.milo)")
    dta.append(f"   (anim_tempo kTempo{rbsong_dict['Tempo'].capitalize()})")
    dta.append(f"   (song_scroll_speed {rbsong_dict['Vocal Track Scroll Duration Ms']})")
    dta.append(f"   (preview {song_dict['preview_start']} {song_dict['preview_end']})")
    dta.append(f"   (song_length {song_dict['song_length']})")
    dta.append(f"   (rank")
    for inst in ["drum", "guitar", "bass", "vocals", "band"]:
        dta.append(f"      ({inst} {song_dict[inst]})")
    dta.append(f"   )")
    dta.append(f"   (solo (TODO: automate this via rbmid/mid) (guitar drum bass vocal_percussion))")
    dta.append(f"   (format 10)\n   (version 30)\n   (game_origin {song_dict['game_origin']})\n   (rating 2)")
    dta.append(f"   (genre {song_dict['genre']})")
    dta.append(f"   (vocal_gender {'female' if song_dict['vocal_gender'] == 2 else 'male'})")
    dta.append(f"   (year_released {song_dict['original_year']})")
    if song_dict["album_year"] != song_dict["original_year"]:
        dta.append(f"   (year_recorded {song_dict['year']})")
    dta.append(f"   (album_art {'TRUE' if song_dict['album_art'] == 1 else 'FALSE'})")
    dta.append(f"   (album_name {song_dict['album_name']})")
    dta.append(f"   (album_track_number {song_dict['album_track_number']})")
    dta.append(f"   (vocal_tonic_note {rbsong_dict['Vocal Tonic Note']})")
    if rbsong_dict["Global Tuning Offset"] != "0.0":
        dta.append(f"   (tuning_offset_cents {rbsong_dict['Global Tuning Offset']})")
    dta.append(f")")

#    for d in range(len(dta)):
#        print(dta[d])
        
    return dta

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
    
#    print(songdta)
    
    rbsong_file = []
    rbsong_file.extend(cwd.glob(f"{sys.argv[1]}/*.rbsong"))
    if len(rbsong_file) != 1:
        print("rbsong error")
        exit()
        
    with open(rbsong_file[0], "rb") as f:
        rbsong = pullMetaData(f.read())
        
#    print(rbsong)
        
    mogg_dta_file = []
    mogg_dta_file.extend(cwd.glob(f"{sys.argv[1]}/*.mogg.dta"))
    if len(mogg_dta_file) != 1:
        print("mogg dta error")
        exit()
        
    mogg_dta = pullMoggData(mogg_dta_file[0])
    
#    print(mogg_dta)
    
    dta_array = fill_dta_template(songdta, mogg_dta, rbsong)
    
    with open("songs.dta", "w") as f:
        for line in dta_array:
            f.write(f"{line}\n")
    
if __name__ == "__main__":
    main()
