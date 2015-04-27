from pyechonest import *
import os 
from tune import Tune
import id3reader

dirs = os.listdir('./song_test')
song_list = []
tempos = []


# Converting filenames to actual song names
for filename in dirs:
    path = 'song_test/'+filename
    id3r = id3reader.Reader(path)
    artist = id3r.getValue('performer')
    song_name = id3r.getValue('title')
    searched = song.search(title=song_name, artist=artist, results=1)

    if len(searched) == 1:
        song_list.append(searched[0])
        artist = searched[0].artist_name
        songname = searched[0].title
        # print artist, songname, path
        tempos.append(searched[0].audio_summary['tempo'])
        
#Judge songs based on danceability, liveness and energy?

