import sys
import os

def parseMoggDTA(moggdta):
    information = {
        "drum": "",
        "bass": "",
        "guitar": "",
        "vocals": "",
        "fake": "",
        "crowd": "",
        "pans": "",
        "vols": ""
    }

    level = 0
    name = ""
    dtadata = 0
    currTrack = ""
    for line in moggdta:
        iscomment = 0
        for y in line:
            # print(y)
            if iscomment == 1:
                break
            else:
                currData = ' '.join(name.strip().split())#.replace(" ", ",")
                if y == "(":
                    if currData in information.keys():
                        currTrack = currData
                        dtadata = 1
                    name = ""
                    level += 1
                elif y == ")":
                    if dtadata == 1:
                        information[currTrack] = currData
                    level -= 1
                elif y == ";":
                    iscomment = 1
                else:
                    name += y

    return information

if __name__ == "__main__":
    with open(sys.argv[1], "r") as f:
        moggdta = f.readlines()
    parsedData = parseMoggDTA(moggdta)
    with open(os.path.splitext(sys.argv[1])[0] + "_parsed.dta", "w") as g:
        for key in parsedData:
            g.write(f'(\'{key}\' ({parsedData[key]}))\n')