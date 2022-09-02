import os
import struct
import sys

songDtaTypes = {
    "songdta_type": "uint",
    "song_id": "uint",
    "version": "short",
    "game_origin": 18,
    "preview_start": "float",
    "preview_end": "float",
    "name": 256,
    "artist": 256,
    "album_name": 256,
    "album_track_number": "short",
    "album_year": "int",
    "original_year": "int",
    "genre": 64,
    "song_length": "float",
    "guitar": "float",
    "bass": "float",
    "vocals": "float",
    "drum": "float",
    "band": "float",
    "keys": "float",
    "real_keys": "float",
    "tutorial": "byte",
    "album_art": "byte",
    "cover": "byte",
    "vocal_gender": "enum",
    "anim_tempo": 16,
    "has_markup": "byte",
    "vocal_parts": "int",
    "solos": "int",
    "fake": "byte",
    "shortname": 256
}

dataTypes = {
    "uint": 4,
    "short": 2,
    "float": 4,
    "int": 4,
    "byte": 1,
    "enum": 1

}

steps = ["songdta_type", "song_id", "version", "game_origin", "preview_start", "preview_end", "name", "artist",
         "album_name", "album_track_number", 2, "album_year", "original_year", "genre", "song_length", "guitar",
         "bass", "vocals", "drum", "band", "keys", "real_keys", "tutorial", "album_art", "cover", "vocal_gender",
         "anim_tempo", "has_markup", 3, "vocal_parts", "solos", "fake",
         "shortname"
         ]

def grabSongData(songdta):

    start = 0

    songsFile = {}

    for x in steps:
        if type(x) is int:
            start += x
        else:
            if type(songDtaTypes[x]) is int:
                a = []
                #print(x, songDtaTypes[x])
                for y in range(0, songDtaTypes[x]):
                    if songdta[y+start] == 0:
                        break
                    a.append(songdta[y+start])
                start += songDtaTypes[x]
                a = bytearray(a).decode('utf-8')
                songsFile[x] = a
                # print(x, a)
            else:
                a = []
                for y in range(0, dataTypes[songDtaTypes[x]]):
                    a.append(songdta[y + start])
                a = bytearray(a)
                if songDtaTypes[x] == "float":
                    a = int(round(struct.unpack('<f',a)[0],0))
                else:
                    a = int.from_bytes(a, 'little')
                    if x == "solos":
                        toBin = lambda number: format(number, 'b').zfill(8)
                        a = toBin(a)
                        solos = ""
                        if a[7] == "1":
                            solos += "drum "
                        if a[6] == "1":
                            solos += "guitar "
                        if a[5] == "1":
                            solos += "bass"
                        a = solos
                songsFile[x] = a
                start += dataTypes[songDtaTypes[x]]
                # print(x, a)
    return songsFile

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print(
            "No file found. Please run this script with a \".songdta_ps4\" file")
        input("Press any key to exit")
        exit()
    if sys.argv[1].endswith(".songdta_ps4"):
        with open(sys.argv[1], "rb") as f:
            songdta = f.read()
    else:
        print("No rbsong file found.")
        input("Press any key to exit")
        exit()
    songsFile = grabSongData(songdta)
    if songsFile["vocal_gender"] == 1:
        songsFile["vocal_gender"] = "male"
    else:
        songsFile["vocal_gender"] = "female"
    with open(os.path.splitext(sys.argv[1])[0] + "_songs.dta", "w") as g:
        for key in songsFile:
            if type(songsFile[key]) is not int:
                g.write(f'(\'{key}\' \'{songsFile[key]}\')\n')
            else:
                g.write(f'(\'{key}\' {songsFile[key]})\n')
