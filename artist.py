from pyechonest import *
import os 
import operator 
from tune import Tune
import id3reader

folder_name = 'Songs_Downloads'
dirs = os.listdir('./' + folder_name)
list_of_songs = []
song_class = []
compared_list = []
tempos = []

start = 'http://developer.echonest.com/api/v4/artist/hotttnesss?'

# Converting filenames to actual song names
for filename in dirs:
    id3r = id3reader.Reader(folder_name+'/'+filename)

    print id3r.getValue('performer')
    # song_name = str.replace(filename, '.mp3', '')
    # list_of_songs.append(song_name)
    # searched = song.identify(title=song_name, filename=folder_name+'/'+filename)
    # if len(searched) == 1:
    #     print searched['metadata']
    #     compared_list.append(searched[0])
    #     artist = searched[0].artist_name
    #     songname = searched[0].title
    #     path = folder_name+'/'+filename
    #     print artist, songname, path
    #     try:
    #         a = Tune(folder_name+'/'+filename, songname, artist)
    #         tempos.append(a.bpm)
    #     except RuntimeError:
    #         pass
        

tempos = [i//2 if i > 161 else i for i in tempos]

first_run = dict(zip(compared_list, tempos))
second_run = sorted(first_run.items(), key=operator.itemgetter(1))
final_list = []

print second_run


# for tup in second_run:
# 	final_list.append(tup[0])
# print final_list

# for element in final_list:
# 	print element.audio_summary['tempo']

