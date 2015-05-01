"""
Attempting to implement mySQL database
"""
import MySQLdb as mdb

import sys, os, pickle

from pyechonest import *

from tune import Tune
import id3reader

SONG_FOLDER = 'song_test'
PICKLE_FOLDER = 'tune_pickle'


class SongDatabase():
    def __init__(self, song_folder, pickle_folder):
        self.con = mdb.connect('localhost', 'phatuser', 'phat623', 'djdb')
        self.song_dir = os.listdir('./' + song_folder)
        self.pickle_dir = pickle_folder

    def reset_db(self):
        """Resets the database, dropping Songs and making it again with ID, File_Path, Artist, Title, Usability, Tempo,
        Danceability, Liveness, Energy, and Pickle_Path"""
        with self.con:
            cur = self.con.cursor(mdb.cursors.DictCursor)
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

    def populate_db(self):
        """For every file in the datase, it first looks in the echonest api for it. If it can't find it, it enters the 
        info with Usable as 0. If it can, it then instantiates a tune object. If the tune can create a song map, it pickles
        the map and stores the pickle filename and all the echonest data. Otherwise, it stores the data but with usability 
        as 0"""
        with self.con:
            cur = self.con.cursor(mdb.cursors.DictCursor)
            for filename in self.song_dir:
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
                        pickle_path = self.pickle_dir + '/' + artist + '_' + song_name + '.txt'
                        output = open(pickle_path,'wb')
                        pickle.dump(tune_obj.song_map, output)
                        cur.execute("INSERT IGNORE INTO Songs(File_Path, Artist, Title, Usable, Tempo, Danceability, Liveness, Energy, Pickle_Path) \
                            Value('%s', '%s', '%s', '%d', '%f', '%f', '%f', '%f', '%s')" % 
                            (path, artist, song_name, usable, tempo, danceability, liveness, energy, pickle_path))
                    else: 
                        pickle_path = self.pickle_dir + '/' + artist + '_' + song_name + '.txt'
                        output = open(pickle_path,'wb')
                        pickle.dump(tune_obj.song_map, output)
                        cur.execute("INSERT IGNORE INTO Songs(File_Path, Artist, Title, Usable, Tempo, Danceability, Liveness, Energy, Pickle_Path) \
                            Value('%s', '%s', '%s', '%d', '%f', '%f', '%f', '%f', NULL)" % 
                            (path, artist, song_name, usable, tempo, danceability, liveness, energy))
        
    def get_entry(self,filepath):
        with self.con:
            cur = self.con.cursor(mdb.cursors.DictCursor)
            cur.execute("SELECT * FROM Songs WHERE Songs.File_Path LIKE " + "'" + SONG_FOLDER + '/' + filepath + "'")
            return cur.fetchone()

    def usable_songs(self):
        with self.con:
            cur = self.con.cursor(mdb.cursors.DictCursor)
            cur.execute("SELECT * FROM Songs WHERE Songs.Usable LIKE 1")
            res = cur.fetchall()
            return res

    def get_pickle(self,p_path):
        output =  open(p_path,'rb')
        return pickle.load(output)

    def print_db(self):
        with self.con:
            cur = self.con.cursor(mdb.cursors.DictCursor)
            cur.execute("SELECT * FROM Songs")
            rows = cur.fetchall()
            print rows

# if __name__ == '__main__':
    # db = SongDatabase(SONG_FOLDER, PICKLE_FOLDER)
    # db.reset_db()
    # db.populate_db()
    # db.print_db()
    # print db.usable_songs()
    # print db.get_entry('03 No Diggity.mp3')