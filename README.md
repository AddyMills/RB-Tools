# RB-Lipsync-Tools
 Various Tools to work with Rock Band Lipsync Files


## Lipsync Converter

Takes an RB4 "rbsong" file, grabs all lipsync data and outputs up to 4 .lipsync files to be used in RB2 or 3.

Usage: Drag an "rbsong" file onto the script, or use it in a batch to convert multiple files in a folder. The files will have the same name as the input file with a number indicating the part and ending in .lipsync.

Made for Python 3.9. Should not need any dependencies.

https://user-images.githubusercontent.com/74471839/141537849-582c1ba7-dfc4-4dfe-9715-0bd5794880af.mp4

## Lipsync Visualizer

Dependencies: matplotlib, progress

Takes an RB2/3 or converted RB4 lipsync file and produces a bar chart for each frame in the file. Produced bar charts can be stitched together at 30fps to sync perfectly with the audio.

This is just for fun. Images do take a while to generate. Depending on length, most songs are between 6,000-8,000 frames. I want to try and implement multiprocessing to speed up generation, but can't figure it out at this point. Something for the future to implement.

https://user-images.githubusercontent.com/74471839/142361856-d61dd4b9-d81a-4f78-810f-d6a318b25b5f.mp4


### More to come
