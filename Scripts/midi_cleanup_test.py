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

# creating a new, merged and cleaned-up EVENTS track

# merging original EVENTS with crowd
new_events_track = merge_tracks(events_merge)
new_events_track.remove(MetaMessage('track_name', name='crowd'))
# removing [preview] from EVENTS
event_msgs = [msg.dict() for msg in new_events_track]
for i in range(len(event_msgs)):
    if "text" in event_msgs[i] and "preview" in event_msgs[i]["text"]:
        event_msgs[i+1]["time"] += event_msgs[i]["time"]
        event_msgs.pop(i)
        break
new_events_track = MidiTrack()
for msg in event_msgs:
    new_events_track.append(MetaMessage.from_dict(msg))
new_mid_tracks.append(new_events_track)

new_mid_tracks.append(beat_track[0])

# merging VENUE track with stagekit_fog
new_venue_track = merge_tracks(venue_merge)
new_venue_track.remove(MetaMessage('track_name', name='stagekit_fog'))

# removing [none] from VENUE
venue_msgs = [msg.dict() for msg in new_venue_track]

time_has_passed = False
none_removed = False
indices_to_remove = []
for i in range(len(venue_msgs)):
    print(venue_msgs[i])
    if venue_msgs[i]["time"] > 0 and time_has_passed == False:
        time_has_passed = True
    if venue_msgs[i]["type"] == "note_off" and time_has_passed == False:
        print(f"    removing {venue_msgs[i]}")
        indices_to_remove.append(i)
        venue_msgs[i]["remove_this"] = True
    if "text" in venue_msgs[i] and "none" in venue_msgs[i]["text"]:
        venue_msgs[i+1]["time"] += venue_msgs[i]["time"]
        venue_msgs[i]["remove_this"] = True
        none_removed = True
    if none_removed and time_has_passed:
        break

venue_msgs = [x for x in venue_msgs if "remove_this" not in x]

new_venue_track = MidiTrack()
for msg in venue_msgs:
    # print(f"appending msg {msg}")
    if "note" in msg["type"]:
        new_venue_track.append(Message.from_dict(msg))
    else:
        new_venue_track.append(MetaMessage.from_dict(msg))
new_mid_tracks.append(new_venue_track)

for track in new_mid_tracks:
    # print(track.name)
    mid_merged.tracks.append(track)
        
# print(mid_path.parents[0])
mid_merged.save(f"{mid_path.parents[0]}/{shortname}_merged_venue.mid")