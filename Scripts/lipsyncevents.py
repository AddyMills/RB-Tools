import mido

import common.classes as cls
import common.functions as fns

mid = fns.MidiFile("Singalongs.mid")

#85 = part3, 86 = part4, 87 = part2
singalongs = []

time = 0
for x in mid:
    time += x.time
    if x.type == "note_on" or x.type == "note_off":
        singalongs.append(cls.midiEvent(x.note, time, x.type))


for x in singalongs:
    print(x.note, x.event, x.time)