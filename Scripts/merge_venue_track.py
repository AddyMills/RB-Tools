import math
import os
import struct
import sys

import common.classes as cls
import common.functions as fns
from mido import Message, MetaMessage, MidiFile, MidiTrack
from mido import merge_tracks
from pathlib import Path

# TODO: take the crowd and stagekit_fog events that are pulled from an rbsong, and merge them into the EVENTS and VENUE tracks respectively

# TODO: ALSO - find any events named "idle_mellow", and replace them with just "idle"
# TODO: ALSO ALSO - remove [preview] from EVENTS, and remove [none] from VENUE

# print(sys.argv[1])


events_merge = []
venue_merge = []
tracks_to_merge = []
new_mid_tracks = []
beat_track = []


# use pathlib and get Path version of sys.argv[1] to get filename
cwd = Path().absolute()

# print(cwd)
mid_path = cwd.joinpath(sys.argv[1])
mid = MidiFile(mid_path)
mid_merged = MidiFile()

# print(mid_path.stem)
shortname = mid_path.stem.replace("_venue","")
# print(shortname)

for track in mid.tracks:
    # if "PART" in track.name or tempomapname in track.name or "HARM" in track.name
    if shortname in track.name or "PART" in track.name or "HARM" in track.name:
        new_mid_tracks.append(track)
    elif track.name == "EVENTS" or "crowd" in track.name:
        events_merge.append(track)
    elif "BEAT" in track.name:
        beat_track.append(track)
    elif "VENUE" in track.name or "stage" in track.name:
        venue_merge.append(track)

new_mid_tracks.append(merge_tracks(events_merge))
new_mid_tracks[-1].remove(MetaMessage('track_name', name='crowd'))
new_mid_tracks.append(beat_track[0])
new_mid_tracks.append(merge_tracks(venue_merge))
new_mid_tracks[-1].remove(MetaMessage('track_name', name='stagekit_fog'))

for track in new_mid_tracks:
    # print(track.name)
    mid_merged.tracks.append(track)

# print(mid_path.parents[0])
mid_merged.save(f"{mid_path.parents[0]}/{shortname}_merged_venue.mid")