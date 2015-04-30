"""
Attempting to implement mySQL database
"""

import MySQLdb as mdb
from pyechonest import *
import sys, os
from tune import Tune
from playlist import Playlist
import id3reader

con = mdb.connect('localhost', 'phatuser', 'phat623', 'djdb')
song_dir = os.listdir('./song_test')    
cur = con.cursor(mdb.cursors.DictCursor)
cur.execute("DROP TABLE IF EXISTS Songs")
cur.execute("CREATE TABLE Songs(Id INT PRIMARY KEY AUTO_INCREMENT, \
    File_Path VARCHAR(50),\
    Artist VARCHAR(20),\
    Title VARCHAR(20),\
    Tempo Float(4,1),\
    Danceability FLOAT(6,6),\
    Liveness FLOAT(6,6),\
    Energy FLOAT(6,6))")

for filename in song_dir:
    print filename
    path = 'song_test/' + filename
    id3r = id3reader.Reader(path)
    artist = id3r.getValue('performer')
    song_name = id3r.getValue('title')
    echo_song = song.search(title=song_name, artist=artist, results=1)
    if echo_song:
        tempo = echo_song[0].audio_summary['tempo']
        danceability = echo_song[0].audio_summary['danceability']
        liveness = echo_song[0].audio_summary['liveness']
        energy = echo_song[0].audio_summary['energy']
        cur.execute("INSERT INTO Songs(File_Path, Artist, Title, Tempo, Danceability, Liveness, Energy) \
            Value('%s', '%s', '%s', '%d', '%d', '%d', '%d')" % 
            (path, artist, song_name, tempo, danceability, liveness, energy))
    
cur.execute("SELECT * FROM Songs")
rows = cur.fetchall()
print rows