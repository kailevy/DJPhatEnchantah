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

def reset_db(con):
    """Resets the database, dropping Songs and making it again with ID, File_Path, Artist, Title, Usability, Tempo,
    Danceability, Liveness, Energy, and Pickle_Path"""
    cur = con.cursor(mdb.cursors.DictCursor)
    cur.execute("DROP TABLE IF EXISTS Songs")
    cur.execute("CREATE TABLE Songs(Id INT PRIMARY KEY AUTO_INCREMENT, \
        File_Path VARCHAR(50) NOT NULL UNIQUE,\
        Artist VARCHAR(20) NOT NULL,\
        Title VARCHAR(20) NOT NULL,\
        Usable TINYINT(1),\
        Tempo FLOAT(4,1),\
        Danceability Float(6,6),\
        Liveness Float(6,6),\
        Energy DOUBLE(6,6),\
        Pickle_Path VARCHAR(50))")

def populate_db(con, song_dir):
    """For every file in the datase, it first looks in the echonest api for it. If it can't find it, it enters the 
    info with Usable as 0. If it can, it then instantiates a tune object. If the tune can create a song map, it pickles
    the map and stores the pickle filename and all the echonest data. Otherwise, it stores the data but with usability 
    as 0"""
    cur = con.cursor(mdb.cursors.DictCursor)
    for filename in song_dir:
        print filename
        path = SONG_FOLDER + '/' + filename
        id3r = id3reader.Reader(path)
        artist = id3r.getValue('performer')
        song_name = id3r.getValue('title')
        echo_song = song.search(title=song_name, artist=artist, results=1)
        if not echo_song:
            usable = False
            cur.execute("INSERT IGNORE INTO Songs(File_Path, Artist, Title, Usable, Tempo, Danceability, Liveness, Energy, Pickle_Path) \
                Value('%s', '%s', '%s', '%d', NULL, NULL, NULL, NULL, NULL)" % 
                (path, artist, song_name, usable))
        elif echo_song:
            tempo = echo_song[0].audio_summary['tempo']
            danceability = echo_song[0].audio_summary['danceability']
            liveness = echo_song[0].audio_summary['liveness']
            energy = echo_song[0].audio_summary['energy']
            tune_obj = Tune(path,artist,song_name)
            usable = bool(tune_obj.song_map)
            pickle_path = None
            if usable:
                pickle_path = PICKLE_FOLDER + '/' + artist + '_' + song_name + '.txt'
                output = open(pickle_path,'wb')
                pickle.dump(tune_obj.song_map, output)
                cur.execute("INSERT IGNORE INTO Songs(File_Path, Artist, Title, Usable, Tempo, Danceability, Liveness, Energy, Pickle_Path) \
                    Value('%s', '%s', '%s', '%d', '%f', '%f', '%f', '%f', '%s')" % 
                    (path, artist, song_name, usable, tempo, danceability, liveness, energy, pickle_path))
            else: 
                pickle_path = PICKLE_FOLDER + '/' + artist + '_' + song_name + '.txt'
                output = open(pickle_path,'wb')
                pickle.dump(tune_obj.song_map, output)
                cur.execute("INSERT IGNORE INTO Songs(File_Path, Artist, Title, Usable, Tempo, Danceability, Liveness, Energy, Pickle_Path) \
                    Value('%s', '%s', '%s', '%d', '%f', '%f', '%f', '%f', NULL)" % 
                    (path, artist, song_name, usable, tempo, danceability, liveness, energy))

    
def get_entry(con,filepath):
    cur = con.cursor(mdb.cursors.DictCursor)
    cur.execute("SELECT * FROM Songs WHERE Songs.File_Path LIKE " + "'" + SONG_FOLDER + '/' + filepath + "'")
    result = cur.fetchone()
    usable = result['Usable']
    artist = result['Artist']
    title = result['Title']
    tempo = result['Tempo']
    danceability = result['Danceability']
    liveness = result['Liveness']
    energy = result['Energy']
    pickle_path = result['Pickle_Path']
    return (usable,filepath,artist,title,tempo,danceability,liveness,energy,pickle_path)

def print_db(con):
    cur = con.cursor(mdb.cursors.DictCursor)
    cur.execute("SELECT * FROM Songs")
    rows = cur.fetchall()
    print rows

if __name__ == '__main__':
    con = mdb.connect('localhost', 'phatuser', 'phat623', 'djdb')
    song_dir = os.listdir('./' + SONG_FOLDER)
    with con:
        # reset_db(con)
        # populate_db(con,song_dir)
        print get_entry(con, '03 True Affection.mp3')
        # print_db(con)