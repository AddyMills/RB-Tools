import os
import struct
import sys

tracks = []
pans = []
vols = []
which_arr = 0

mogg_dict = {}

with open(sys.argv[1], "r") as f:
    while True:
        line = f.readline().replace("\n","")
        if not line:
            break
        else:
#            print(line)
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
        

print(tracks)
print(pans)
print(vols)

pan_values = [float(x) for x in pans[1][4:-1].split(" ")]
vol_values = [float(x) for x in vols[1][4:-1].split(" ")]
print(pan_values)
print(vol_values)

tracks = tracks[2:-2]
mogg_dict["drum"] = ""
for x in range(len(tracks)):
    line = tracks[x]
    print(line)
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

print(mogg_dict)
