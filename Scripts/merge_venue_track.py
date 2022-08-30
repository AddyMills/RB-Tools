import math
import os
import struct
import sys

import common.classes as cls
import common.functions as fns
from mido import Message, MetaMessage, MidiFile, MidiTrack
from mido import merge_tracks

# TODO: take the crowd and stagekit_fog events that are pulled from an rbsong, and merge them into the EVENTS and VENUE tracks respectively

# TODO: ALSO - find any events named "idle_mellow", and replace them with just "idle"
# TODO: ALSO ALSO - remove [preview] from EVENTS, and remove [none] from VENUE
