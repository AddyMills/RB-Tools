from common.dicts import charTypes

class consoleType:
    def __init__(self, console):
        if console == '360':
            self.endian = 'big'
            self.pack = '>f'
        else:
            self.endian = 'little'
            self.pack = '<f'

class RB2lipsyncHeader:
    def __init__(self):
        self.version = bytearray([0, 0, 0, 0x01])
        self.revision = bytearray([0, 0, 0, 0x02])
        self.dtaImport = bytearray([0, 0, 0, 0])
        self.embedDTB = bytearray([0, 0, 0, 0])
        self.unknown1 = bytearray([0])
        self.propAnim = bytearray([0, 0, 0, 0])

class RBlipData:
    def __init__(self, RB):
        if RB == 4:
            self.endian = "little"
        else:
            self.endian = "big"
        if self.endian == "little":
            self.opEndian = "big"
        else:
            self.opEndian = "little"
        self.visemeCount = charTypes["32bit"]  # Bit value for number of visemes
        self.visemeItem = charTypes["32bit"]  # Bit value for viseme entries

class tempoMapItem:
    def __init__(self, time, tempo, avgTempo):
        self.time = time
        self.tempo = tempo
        self.avgTempo = avgTempo  # Avg Tempo up to that point

class venueItem:
    def __init__(self, time, event):
        self.time = time
        self.event = event