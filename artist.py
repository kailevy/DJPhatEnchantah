from pyechonest import *
import os 
import operator 

folder_name = 'Songs_Downloads'
dirs = os.listdir('./' + folder_name)
list_of_songs = []
for filename in dirs:
	song_name = str.replace(filename, '.mp3', '')
	list_of_songs.append(song_name)
compared_list = []
for s in list_of_songs:
	searched = song.search(title = s, results = 1)
	if len(searched) == 1:
		compared_list.append(searched[0])
tempos = []
for element in compared_list:
	bpm = element.audio_summary['tempo']
	tempos.append(bpm)
first_run = dict(zip(compared_list, tempos))
second_run = sorted(first_run.items(), key=operator.itemgetter(1))
final_list = []
for tup in second_run:
	final_list.append(tup[0])
	
#p = playlist.static(type='artist-radio', artist=['ida maria', 'florence + the machine'])
# my_playlist = 
# s = song.search(title ='everything at once', results = 1)
# music = s[0]
# print type(music.title)
