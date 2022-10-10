import os
import sys
import mido
import time
import subprocess
import shutil
import Lipsync_Converter_RB4 as lipsync_conv
import numpy as np
import common.functions as fns
from mido import MetaMessage
from songdta2txt import grabSongData
from rbsong2midi import pullMetaData
from rbsong2midi import main as mergeVenue
from readmoggdta import parseMoggDTA

# song = "D:\\RB\\RB4\\To Convert\\In Progress\\neverletemholdyaback"
song = sys.argv[1]

anim_speed = {"slow": 16,
              "medium": 32,
              "fast": 64}

allowed_tracks = ["PART DRUMS", "PART BASS", "PART GUITAR", "PART VOCALS", "HARM1", "HARM2", "HARM3", "EVENTS", "BEAT", "VENUE"]

filename = os.path.basename(song)

try:
    with open(f"{song}\\{filename}.mogg.dta", "r") as f:
        moggdta = f.readlines()
except:
    subprocess.run(['dependencies\dtxtool\DTXTool.exe', "dtb2a", f"{song}\\{filename}.mogg.dta_dta_ps4", 'temp.dta'],
                   check=True)
    with open(f"temp.dta", "r") as f:
        moggdta = f.readlines()
    os.remove('temp.dta')

with open(f"{song}\\{filename}.rbsong", "rb") as f:
    rbsong = f.read()

with open(f"{song}\\{filename}.songdta_ps4", "rb") as f:
    songdta = f.read()

moggdict = parseMoggDTA(moggdta)

songdict = grabSongData(songdta)

rbsongdict = pullMetaData(rbsong)

subgenres = {'alternative': ['alternative', 'college', 'other'],
             'blues': ['acoustic', 'chicago', 'classic', 'contemporary', 'country', 'delta', 'electric', 'other'],
             'classical': ['classical'],
             'classicrock': ['classicrock'],
             'country': ['alternative', 'bluegrass', 'contemporary', 'honkytonk', 'outlaw', 'traditionalfolk', 'other'],
             'emo': ['emo'],
             'fusion': ['fusion'],
             'glam': ['glam', 'goth', 'other'],
             'grunge': ['grunge'],
             'hiphoprap': ['alternativerap', 'gangsta', 'hardcorerap', 'hiphop', 'oldschoolhiphop', 'rap', 'triphop',
                           'undergroundrap', 'other'],
             'indierock': ['indierock', 'lofi', 'mathrock', 'noise', 'postrock', 'shoegazing', 'other'],
             'inspirational': ['inspirational'],
             'jazz': ['acidjazz', 'contemporary', 'experimental', 'ragtime', 'smooth', 'other'],
             'jrock': ['jrock'],
             'latin': ['latin'],
             'metal': ['alternative', 'black', 'core', 'death', 'hair', 'industrial', 'metal', 'power', 'prog', 'speed',
                       'thrash', 'other'],
             'new_wave': ['darkwave', 'electroclash', 'new_wave', 'synth', 'other'],
             'novelty': ['novelty'],
             'numetal': ['numetal'],
             'popdanceelectronic': ['ambient', 'breakbeat', 'chiptune', 'dance', 'downtempo', 'dub', 'drumandbass',
                                    'electronica', 'garage', 'hardcoredance', 'house', 'industrial', 'techno', 'trance',
                                    'other'],
             'poprock': ['contemporary', 'pop', 'softrock', 'teen', 'other'],
             'prog': ['progrock'],
             'punk': ['alternative', 'classic', 'dancepunk', 'garage', 'hardcore', 'pop', 'other'],
             'rbsoulfunk': ['disco', 'funk', 'motown', 'rhythmandblues', 'soul', 'other'],
             'reggaeska': ['reggae', 'ska', 'other'],
             'rock': ['arena', 'blues', 'folkrock', 'garage', 'hardrock', 'psychadelic', 'rock', 'rockabilly',
                      'rockandroll', 'surf', 'other'],
             'southernrock': ['southernrock'],
             'world': ['world'],
             'other': ['acapella', 'acoustic', 'contemporaryfolk', 'experimental', 'oldies', 'other']}

# Merge all three dictionaries
masterdict = songdict | rbsongdict | moggdict

# Clean up and add missing entries if needed
if masterdict['anim_tempo'] == "":
    masterdict['anim_tempo'] = masterdict["Tempo"]
if masterdict['anim_tempo'] in anim_speed:
    masterdict['anim_tempo'] = anim_speed[masterdict['anim_tempo']]
masterdict["vocal_tonic_note"] = masterdict["Vocal Tonic Note"]
masterdict["song_scroll_speed"] = masterdict["Vocal Track Scroll Duration Ms"]
masterdict["tuning_offset_cents"] = masterdict["Global Tuning Offset"]
masterdict["drum_diff"] = songdict["drum"]
masterdict["guitar_diff"] = songdict["guitar"]
masterdict["bass_diff"] = songdict["bass"]
masterdict["vocals_diff"] = songdict["vocals"]
masterdict["band_diff"] = songdict["band"]
masterdict["album_art"] = 1
masterdict["year_released"] = masterdict["original_year"]
masterdict["year_recorded"] = masterdict["album_year"]
masterdict["rating"] = 4
masterdict['guide_pitch_volume'] = -3.00
masterdict['encoding'] = 'latin1'

for x in ["pans", "vols"]:
    temp = masterdict[x].split(' ')
    for z, y in enumerate(temp):
        temp[z] = str(round(float(y), 2))
        if len(temp[z]) != 4:
            temp[z] = " "+temp[z]
    temp = " ".join(temp)
    masterdict[x] = temp

if "other" in subgenres[masterdict["genre"]]:
    masterdict["sub_genre"] = "subgenre_other"
else:
    masterdict["sub_genre"] = "subgenre" + masterdict["genre"]

# RB3 default values
masterdict['version'] = 30
masterdict['format'] = 10

# for key in masterdict:
#    print(key, masterdict[key])

# Create Songs.dta
sp = lambda a: "   " * a  # Define spaces for tabs to make it all look nice and shit

openb = lambda a: sp(a) + "("
closeb = lambda a: sp(a) + ")"

"""f.write(f"{sp(2)}(\n")
f.write(f"{sp(3)}\'yyy\'\n")
f.write(f"{sp(3)}\"{masterdict['yyy']}\"\n")
f.write(f"{sp(2)})\n")"""

# os.mkdir(f'{song}\\{packageName}')
packageName = "RB3pkg"
try:
    os.mkdir(f"{os.path.dirname(sys.argv[0])}\\{packageName}")
except:
    pass
try:
    os.mkdir(f"{os.path.dirname(sys.argv[0])}\\{packageName}\\{filename}")
except:
    pass
try:
    os.mkdir(f"{os.path.dirname(sys.argv[0])}\\{packageName}\\{filename}\\gen")
except:
    pass
try:
    os.mkdir(f"{os.path.dirname(sys.argv[0])}\\{packageName}\\{filename}\\lipsync")
except:
    pass
# Create songs.dta file
with open(f"{os.path.dirname(sys.argv[0])}\\{packageName}\\songs.dta", "w") as f:
    f.write(f"(\n")

    f.write(f'{sp(1)}\'{masterdict["shortname"]}\'\n')

    f.write(f"{sp(1)}(\n")
    f.write(f"{sp(2)}\'name\'\n")
    f.write(f"{sp(2)}\"{masterdict['name']}\"\n")
    f.write(f"{sp(1)})\n")

    f.write(f"{sp(1)}(\n")
    f.write(f"{sp(2)}\'artist\'\n")
    f.write(f"{sp(2)}\"{masterdict['artist']}\"\n")
    f.write(f"{sp(1)})\n")

    f.write(f"{sp(1)}(\'master\' {1 if masterdict['cover'] == 0 else 0})\n")

    f.write(f"{sp(1)}(\n")
    f.write(f"{sp(2)}\'song\'\n")
    f.write(f"{sp(2)}(\n")
    f.write(f"{sp(3)}\'name\'\n")
    f.write(f"{sp(3)}\"songs/{masterdict['shortname']}/{masterdict['shortname']}\"\n")
    f.write(f"{sp(2)})\n")
    f.write(f"{sp(2)}(\n")
    f.write(f"{sp(3)}\'tracks_count\'\n")
    f.write(
        f"{sp(3)}({len(masterdict['drum'].split(' '))} {len(masterdict['bass'].split(' '))} {len(masterdict['guitar'].split(' '))} {len(masterdict['vocals'].split(' '))} 0 {len(masterdict['fake'].split(' '))}{'' if masterdict['crowd'] == '' else ' ' + str(len(masterdict['crowd'].split(' ')))})\n")
    f.write(f"{sp(2)})\n")

    f.write(f"{sp(2)}(\n")
    f.write(f"{sp(3)}\'tracks\'\n")
    f.write(f"{sp(3)}(\n")

    for x in ['drum', 'bass', 'guitar', 'vocals']:
        if len(masterdict[x].split(' ')) != 0:
            f.write(f"{openb(4)}\n")
            f.write(f"{sp(5)}\'{x}\'\n")
            f.write(f"{sp(5)}({masterdict[x]})\n")
            f.write(f"{closeb(4)}\n")

    f.write(f"{closeb(3)}\n")
    f.write(f"{closeb(2)}\n")

    f.write(f"{sp(2)}(\n")
    f.write(f"{sp(3)}\'pans\'\n")
    f.write(f"{sp(3)}({masterdict['pans']})\n")
    f.write(f"{sp(2)})\n")

    f.write(f"{sp(2)}(\n")
    f.write(f"{sp(3)}\'vols\'\n")
    f.write(f"{sp(3)}({masterdict['vols']})\n")
    f.write(f"{sp(2)})\n")

    maximum = 0
    for x in ['drum', 'bass', 'guitar', 'vocals', 'fake', 'crowd']:
        if masterdict[x]:
            for y in masterdict[x].split(' '):
                if int(y) > maximum:
                    maximum = int(y)
    cores = []
    for x in range(0, maximum + 1):
        if str(x) in masterdict['guitar']:
            cores.append(str(1))
        else:
            cores.append(str(-1))
    f.write(f"{sp(2)}(\n")
    f.write(f"{sp(3)}\'cores\'\n")
    f.write(f"{sp(3)}({' '.join(cores)})\n")
    f.write(f"{sp(2)})\n")

    f.write(f"{sp(2)}(\'vocal_parts\' {masterdict['vocal_parts']})\n")
    if masterdict['crowd']:
        f.write(f"{sp(2)}(crowd_channels {masterdict['crowd']})\n")

    f.write(f"{sp(2)}(\n")
    f.write(f"{sp(3)}\'drum_solo\'\n")
    f.write(f"{sp(3)}(\n")
    f.write(f"{sp(4)}\'seqs\'\n")
    f.write(f"{sp(4)}('kick.cue' 'snare.cue' 'tom1.cue' 'tom2.cue' 'crash.cue')\n")
    f.write(f"{sp(3)})\n")
    f.write(f"{sp(2)})\n")

    f.write(f"{sp(2)}(\n")
    f.write(f"{sp(3)}\'drum_freestyle\'\n")
    f.write(f"{sp(3)}(\n")
    f.write(f"{sp(4)}\'seqs\'\n")
    f.write(f"{sp(4)}('kick.cue' 'snare.cue' 'hat.cue' 'ride.cue' 'crash.cue')\n")
    f.write(f"{sp(3)})\n")
    f.write(f"{sp(2)})\n")

    f.write(f"{sp(2)}(\'mute_volume\' -96)\n")
    f.write(f"{sp(2)}(\'mute_volume_vocals\' -12)\n")
    f.write(f"{sp(2)}(\'hopo_threshold\' 170)\n")
    f.write(f"{sp(1)})\n")

    f.write(f"{sp(1)}(\'song_scroll_speed\' {masterdict['song_scroll_speed']})\n")

    f.write(f"{sp(1)}(\n")
    f.write(f"{sp(2)}\'bank\'\n")
    for x in ['tambourine', 'cowbell', 'handclap']:
        if x in masterdict['Vocal Percussion Patch']:
            f.write(f"{sp(2)}\"sfx/{x}_bank.milo\"\n")
    f.write(f"{sp(1)})\n")

    for x in range(1, 6):
        if str(x) in masterdict['Drum Kit Patch']:
            f.write(f"{sp(1)}(drum_bank sfx/kit0{x}_bank.milo)\n")

    for x in ['anim_tempo', 'song_length']:
        f.write(f"{sp(1)}(\'{x}\' {masterdict[x]})\n")
    f.write(f"{sp(1)}(\'preview\' {masterdict['preview_start']} {masterdict['preview_end']})\n")

    f.write(f"{sp(1)}(\n")
    f.write(f"{sp(2)}\'rank\'\n")
    for x in ['drum', 'guitar', 'bass', 'vocals', 'keys', 'real_keys', 'band']:
        if "keys" in x:
            f.write(f"{sp(2)}(\'{x}\' 0)\n")
        else:
            xdiff = x + "_diff"
            f.write(f"{sp(2)}(\'{x}\' {masterdict[xdiff]})\n")
    f.write(f"{sp(1)})\n")

    for x in ['genre', 'vocal_gender', 'version', 'format', 'album_art', 'year_recorded', 'year_released', 'rating',
              'sub_genre', 'song_id', 'tuning_offset_cents', 'guide_pitch_volume', 'game_origin', 'encoding',
              'album_track_number']:
        if x in ['year_recorded', 'year_released']:
            if x == 'year_recorded':
                if masterdict['year_recorded'] != masterdict['year_released']:
                    f.write(f"{sp(1)}(\'{x}\' {masterdict[x]})\n")
            else:
                f.write(f"{sp(1)}(\'{x}\' {masterdict[x]})\n")
        elif x == "vocal_gender":
            f.write(f"{sp(1)}({x} {'male' if masterdict['vocal_gender'] == 1 else 'female'})\n")
        elif x == "album_art":
            f.write(f"{sp(1)}({x} TRUE)\n")
        else:
            if type(masterdict[x]) == int or type(masterdict[x]) == float:
                f.write(f"{sp(1)}(\'{x}\' {masterdict[x]})\n")
            else:
                f.write(f"{sp(1)}(\'{x}\' \'{masterdict[x]}\')\n")

    f.write(f"{sp(1)}(\n")
    f.write(f"{sp(2)}\'album_name\'\n")
    f.write(f"{sp(2)}\"{masterdict['album_name']}\"\n")
    f.write(f"{sp(1)})\n")

    f.write(f"{sp(1)}(vocal_tonic_note {masterdict['vocal_tonic_note']})\n")
    f.write(f"{sp(1)};(song_tonality 0) - Only set this for pro guitar upgrades and if you know what you are doing\n")

    f.write(f")")

# Convert MIDI and merge with venue (and singalong events)

saveMid = f"{os.path.dirname(sys.argv[0])}\\{packageName}\\{filename}\\{filename}.mid"
forgetool = 'forgetool'
while True:
    try:
        subprocess.run([forgetool, 'rbmid2mid', f'{song}\\{filename}.rbmid_ps4',
                        saveMid])
        subprocess.run([forgetool, 'tex2png', f'{song}\\{filename}.png_ps4',
                        f"{os.path.dirname(sys.argv[0])}\\{packageName}\\{filename}\\{filename}.png"])
        break
    except:
        print(
            "Forgetool not found! You can specify where it's stored this time, but it's recommended to add Forgetool to your PATH\n")
        forgetool = input(
            "Please drag your Forgetool command line program into the window now (or leave blank to exit): ")
        if forgetool == "":
            exit()

singalongPart = False
#Add converting lipsync!
try:
    lipParts, lipsyncVals, singalong = lipsync_conv.main_lipsync_new(f"{song}\\{filename}.lipsync_ps4")
    instruments = {"drum": 0,
    "guitar": 0,
    "bass": 0,
    "mic": 0}
    singalongPart = True
    #print(lipParts)
    for x in lipParts:
        for key in instruments:
            if key in x.lower():
                instruments[key] += 1
    for y, x in enumerate(lipParts):
        with open(f"{os.path.dirname(sys.argv[0])}\\{packageName}\\{filename}\\lipsync\\{y}-Part_{x}.lipsync", "wb") as g:
            g.write(lipsyncVals[y])
    # singalong.save(filename=f"{os.path.dirname(sys.argv[0])}\\{packageName}\\{filename}\\lipsync\\Singalongs.mid")
    #print(instruments)
    #print(len(lipsyncVals[0]),len(lipsyncVals[1]),len(lipsyncVals[2]),len(lipsyncVals[3]))
except:
    try:
        lipdataSep = lipsync_conv.main_rbsong(f"{song}\\{filename}.rbsong")

        for x in range(0, len(lipdataSep)):
            if x == 0:
                saveName = "song"
            else:
                saveName = f"part{x + 1}"
            lipSave = f"{saveName}.lipsync"
            with open(f"{os.path.dirname(sys.argv[0])}\\{packageName}\\{filename}\\lipsync\\{lipSave}", "wb") as lipFile:
                lipFile.write(lipdataSep[x])
    except Exception as e:
        print(e)

try:
    with open(f"{song}\\{filename}.rbsong", "rb") as f:
        anim = f.read()
    mid = mergeVenue(anim, mido.MidiFile(saveMid))
    newMid = mido.MidiFile()
    newMid.add_track()
    fogtrack = 0
    venue = 0
    toMerge = []
    for y, x in enumerate(mid.tracks):
        if y == 0:
            newMid.tracks[-1] = x
        if x.name in allowed_tracks:
            if x.name == "VENUE":
                toMerge.append(x.copy())
            else:
                newMid.add_track()
                newMid.tracks[-1] = x
        elif x.name == "stagekit_fog":
            toMerge.append(x.copy())
    if singalongPart == True:
        ##############################
        # Merge Singalong data with Venue track
        songMap = fns.midiProcessing(mid)
        songTime, songSeconds, songTempo, songAvgTempo = fns.songArray(songMap)
        secondsArray = np.array(songSeconds)
        timeStart = 0
        singalongTrack = mido.MidiTrack()
        for x in singalong:
            mapLower = secondsArray[secondsArray <= x.time].max()
            # print(x.time)
            arrIndex = songSeconds.index(mapLower)
            timeFromChange = x.time - songSeconds[arrIndex]
            ticksFromChange = fns.s2t(timeFromChange, fns.tpb, songTempo[arrIndex])
            timeVal = songTime[arrIndex] + round(ticksFromChange) - timeStart
            if x.type == "note_on":
                singalongTrack.append(fns.Message("note_on", note=x.note, velocity=100, time=timeVal))
            if x.type == "note_off":
                singalongTrack.append(fns.Message("note_off", note=x.note, velocity=0, time=timeVal))
        toMerge.append(singalongTrack)
        ##############################
    newTrack = mido.merge_tracks(toMerge)
    try:
        newTrack.remove(MetaMessage('track_name', name='stagekit_fog'))
    except:
        pass
    newMid.add_track()
    newMid.tracks[-1] = newTrack.copy()
    os.remove(saveMid)
    newMid.save(filename=saveMid)
except Exception as e:
   print(e)

try:
    shutil.rmtree(f'{song}\\{packageName}')
except Exception as e:
   pass

shutil.move(f"{os.path.dirname(sys.argv[0])}\\{packageName}", f'{song}')

shutil.copy(f"{song}\\{filename}.mogg", f'{song}\\{packageName}\\{filename}\\{filename}.mogg')
