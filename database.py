"""
Attempting to implement mySQL database
"""
import MySQLdb as mdb

import sys, os, pickle

from pyechonest import *

from tune import Tune
from playlist import Playlist
import id3reader

SONG_FOLDER = 'song_test'
PICKLE_FOLDER = 'tune_pickle'

con = mdb.connect('localhost', 'phatuser', 'phat623', 'djdb')
song_dir = os.listdir('./' + SONG_FOLDER)
cur = con.cursor(mdb.cursors.DictCursor)
cur.execute("DROP TABLE IF EXISTS Songs")
cur.execute("CREATE TABLE Songs(Id INT PRIMARY KEY AUTO_INCREMENT, \
    File_Path VARCHAR(50),\
    Artist VARCHAR(20),\
    Title VARCHAR(20),\
    Usable TINYINT(1),\
    Tempo FLOAT(4,1),\
    Danceability Float(6,6),\
    Liveness Float(6,6),\
    Energy DOUBLE(6,6),\
    Pickle_Path VARCHAR(50))")

for filename in song_dir:
    print filename
    path = SONG_FOLDER + '/' + filename
    id3r = id3reader.Reader(path)
    artist = id3r.getValue('performer')
    song_name = id3r.getValue('title')
    echo_song = song.search(title=song_name, artist=artist, results=1)
    if not echo_song:
        usable = False
        cur.execute("INSERT INTO Songs(File_Path, Artist, Title, Usable, Tempo, Danceability, Liveness, Energy, Pickle_Path) \
            Value('%s', '%s', '%s', '%d', '0', '0', '0', '0', '-')" % 
            (path, artist, song_name, usable))
    elif echo_song:
        tempo = echo_song[0].audio_summary['tempo']
        danceability = echo_song[0].audio_summary['danceability']
        liveness = echo_song[0].audio_summary['liveness']
        energy = echo_song[0].audio_summary['energy']
        tune_obj = Tune(path,song_name,artist)
        usable = bool(tune_obj.song_map)
        pickle_path = '-'
        if usable:
            pickle_path = PICKLE_FOLDER + '/' + artist + '_' + song_name + '.txt'
            output = open(pickle_path,'wb')
            pickle.dump(tune_obj.song_map, output)
        cur.execute("INSERT INTO Songs(File_Path, Artist, Title, Usable, Tempo, Danceability, Liveness, Energy, Pickle_Path) \
            Value('%s', '%s', '%s', '%d', '%f', '%f', '%f', '%f', '%s')" % 
            (path, artist, song_name, usable, tempo, danceability, liveness, energy, pickle_path))
    
cur.execute("SELECT * FROM Songs")
rows = cur.fetchall()
print rows