import os
import sys

import common.classes as cls
import common.functions as fns
import matplotlib.pyplot as plt
# from multiprocessing import Process
from progress.bar import IncrementalBar as progressBar

# pool_size = 5

def getLipData(rbsong, lipstart, lipdata):
    visemeCount = []
    for x in range(0, lipdata.visemeCount):
        visemeCount.append(rbsong[lipstart])
        lipstart += 1
    if lipdata.endian == "little":
        visemeCount.reverse()
    visemeNum = bytearray(visemeCount)  # Use bytearray.append(x) to combine bytearray strings
    visemeCount = int.from_bytes(visemeNum, byteorder="big",
                                 signed=False)  # Get an int from the 32-bit array to make the counter for the visemes
    visemes = []

    for x in range(0, visemeCount):
        visemeName = []
        visemeNameCount = []
        for y in range(0, lipdata.visemeItem):
            visemeNameCount.append(rbsong[lipstart])
            lipstart += 1

        if lipdata.endian == "little":
            visemeNameCount.reverse()

        visemeNameLen = int.from_bytes(bytearray(visemeNameCount), byteorder="big", signed=False)

        for y in range(0, visemeNameLen):
            visemeName.append(chr(rbsong[lipstart]))
            lipstart += 1
        visemes.append(''.join(visemeName).capitalize())

    visemeElements = []
    frameCount = []
    for x in range(0, lipdata.visemeItem):
        frameCount.append(rbsong[lipstart])
        lipstart += 1
    if lipdata.endian == "little":
        frameCount.reverse()
    frameByteTemp = bytearray(frameCount)  # Number of frames in song. Divide by 30 to get total in seconds.
    frameCount = int.from_bytes(frameByteTemp, byteorder="big", signed=False)

    for x in range(0, lipdata.visemeItem):
        visemeElements.append(rbsong[lipstart])
        lipstart += 1
    if lipdata.endian == "little":
        visemeElements.reverse()

    visemeStart = lipstart  # Create copy of viseme starting point

    lipstart = visemeStart  # Return to viseme data

    visemeData, frameDataNum, frameDataName = fns.genFrameData(rbsong, frameCount, visemes, lipstart)

    return frameDataNum, visemes


def main(filename):

    with open(filename, "rb") as f:
        s = f.read()

    RB = cls.RBlipData(2)

    startPos = fns.getStart(s)+17

    lipsyncData, visemes = getLipData(s, startPos, RB)

    for x in range(0, len(visemes)):  # Lower every 2nd x-axis label
        if x % 4 != 0:
            visemes[x] = "\n"*(x % 4) + visemes[x]

    visemeFrame = []

    for x in range(0, len(visemes)):
        visemeFrame.append(0)

    visemeState = []

    for x, lips in enumerate(lipsyncData):
        if lips == 0:
            pass
        else:
            visemeEdit = -1
            for y in range(0, lips[0] * 2):
                if y % 2 == 0:
                    visemeEdit = lips[1][y]
                else:
                    visemeFrame[visemeEdit] = lips[1][y]
        visemeState.append(visemeFrame.copy())

    print("Starting image saving.")

    fig, ax = plt.subplots(figsize=(19.2, 10.8))
    ax.set_title(filename)
    ax.set_xlabel('Visemes', fontsize=20)
    ax.set_ylabel('Strength', fontsize=20)
    ax.set_ylim((0, 255))
    y = len(visemeState)
    progress = progressBar('Generating Images', max=y)
    colours = ["#800000", "#000099"]

    for x, item in enumerate(visemeState):
        pc = ax.bar(visemes, item, color=colours)  # Each image seems to get a different colour if undefined, so I'm defining an alternating pattern for each image.
        for y, ticklabel in enumerate(plt.gca().get_xticklabels()):
            ticklabel.set_color(colours[y % 2])
        fig.savefig('visualizer_output/{0}.png'.format(x))
        pc.remove()
        progress.next()


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("No file found. Please use a \".lipsync\" file as an argument when running the script.")
        exit()

    filename = sys.argv[1]

    if os.path.splitext(filename)[1] != ".lipsync":
        print("Invalid file found. Please use an \".lipsync\" file as an argument when running the script.")
        exit()

    main(filename)
