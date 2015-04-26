from pyechonest import *
import os 
import operator 
from tune import Tune
import id3reader

folder_name = 'song_test'
dirs = os.listdir('./' + folder_name)
list_of_songs = []
song_class = []
compared_list = []
tempos = []
othertempos = []


# Converting filenames to actual song names
for filename in dirs:
    path = folder_name+'/'+filename
    id3r = id3reader.Reader(path)
    artist = id3r.getValue('performer')
    song_name = id3r.getValue('title')

    searched = song.search(title=song_name, artist=artist, results=1)
    if len(searched) == 1:
        compared_list.append(searched[0])
        artist = searched[0].artist_name
        songname = searched[0].title
        print artist, songname, path
        try:
            a = track.track_from_filename(path)
            # a = Tune(folder_name+'/'+filename, songname, artist)
            tempos.append(a.tempo)
        except RuntimeError:
            pass
        
print compared_list
print tempos


tempos = [i//2 if i > 161 else i for i in tempos]

first_run = dict(zip(compared_list, tempos))
second_run = sorted(first_run.items(), key=operator.itemgetter(1))
final_list = []

# print second_run
