# RB-Tools
Various Tools to work with Rock Band files. Written using Python 3.9. Dependencies are listed in each section.


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

## Milo2Midi

Dependencies: mido

Takes a song's anim file (found in the milo of a song) and converts all data to a MIDI track. Think of this as a reverse Milo Mod too.

For now, you must extract the anim file yourself from a song's milo file (Onyx can do this).

Usage: Run the script with the .anim file as an argument. Optionally, you can also add a MIDI file as an argument. It will read through the anim file and give you a midi file containing all events found in the anim file separated into multiple tracks.

If you opt to add a MIDI file, the events will get added to that MIDI. This is the most accurate solution.

If a MIDI file is not present, it uses a default MIDI file with a BPM of 120bpm. This will work fine to quickly check, but it's not as accurate as using a MIDI file.

The name of the output will be a MIDI file and use the name and folder location of your first argument with "merged" added to it.

### More to come
