# RB-Tools
Various Tools to work with Rock Band files. Written using Python 3.9. Dependencies, if any, are listed in each section.


## Lipsync Converter

Takes an RB4 "rbsong" file, grabs all lipsync data and outputs up to 4 .lipsync files to be used in RB2 or 3.

Usage: Drag an "rbsong" file onto the script, or use it in a batch to convert multiple files in a folder. The files will have the same name as the input file with a number indicating the part and ending in .lipsync.

Should not need any dependencies.

https://user-images.githubusercontent.com/74471839/141537849-582c1ba7-dfc4-4dfe-9715-0bd5794880af.mp4

## Lipsync Visualizer

Dependencies: matplotlib, progress

Takes an RB2/3 or converted RB4 lipsync file and produces a bar chart for each frame in the file. Produced bar charts can be stitched together at 30fps to sync perfectly with the audio.

This is just for fun. Images do take a while to generate. Depending on length, most songs are between 6,000-8,000 frames. I want to try and implement multiprocessing to speed up generation, but can't figure it out at this point. Something for the future to implement.

https://user-images.githubusercontent.com/74471839/142361856-d61dd4b9-d81a-4f78-810f-d6a318b25b5f.mp4

## Lipsync2Midi

Dependencies: mido, numpy

Takes a lipsync file and inserts all viseme events into a MIDI file that is compatible with Onyx's *Lipsync* tab found in Other Tools. Useful for viewing official viseme data, or splicing MIDI tracks together and have Onyx make a combined lipsync for you.

Usage: Run the script with a lipsync file as its variable. The program will look for all lipsync files in the folder and outputs a 120bpm MIDI that has the visemes synced to the song.

Optionally, if you have a MIDI file in the same folder as the lipsync files, it will add the LIPSYNC# tracks to that MIDI. If you use this functionality, make sure to only have one MIDI file in the folder. Multiple MIDI files will result in duplicate tracks for some reason I haven't been able to debug. But only having one will not cause duplicates.

Link to Onyx: https://github.com/mtolly/onyxite-customs

## Milo2Midi

Dependencies: mido, numpy

Takes a song's anim file (found in the milo of a song) and converts all data to a MIDI track. Think of this as a reverse Milo Mod tool.

For now, you must extract the anim file yourself from a song's milo file (Onyx can do this).

Usage: Run the script with the .anim file as an argument. Optionally, you can also add a MIDI file as an argument. It will read through the anim file and give you a midi file containing all events found in the anim file separated into multiple tracks.

If you opt to add a MIDI file, the events will get added to that MIDI. This is the most accurate solution.

If a MIDI file is not present, it uses a default MIDI file with a BPM of 120bpm. This will work fine to quickly check, but it's not as accurate as using a MIDI file.

The name of the output will be a MIDI file and use the name and folder location of your first argument with "merged" added to it.

Optional: add "separate" to your arguments to get separated venue tracks (lights, camera cuts and post procs)

**This does not yet work with with song .anim files from TBRB**

## RBsong2Midi

Dependencies: mido

Similar to Milo2Midi, but this works with RB4's rbsong file. Takes in an rbsong file as an argument, and outputs a MIDI file with the venue events from the rbsong file.

MIDI file with the same name as the rbsong is **required** for this script to work.

Optional: add "separate" to your arguments to get separated venue tracks (lights, camera cuts, and post procs)

## Voc2Lipsync

Dependencies: mido

Converts a voc lipsync file from GH2 and (potentially) KR to the lipsync format used by RB2 and above. This only converts the mouth movements and blink events. Using the Audrey script to add some eyebrow movements could make these lipsync files really pop.

Usage: Run the script with a voc file as its variable. Optionally, you can have a third argument to exaggerate the mouth movements. Enter this number as a decimal up to 1.5 (150%).

Example in Windows command line: Voc2lipsync.py freebird.voc 1.2

This will convert the Free Bird voc file to RB2 lipsync while exaggerating the animations by 20%.

## Acknowledgements

No code outside of my own was used. However, I would like to extend special thanks to Maxton and PikminGuts92 for having 010 templates available to figure these scripts out
