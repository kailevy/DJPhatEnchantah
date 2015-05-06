"""
Attempting to implement mySQL database
"""
import MySQLdb as mdb

import sys, os, pickle, time

from pyechonest import *

from tune import Tune
import id3reader

SONG_FOLDER = 'song_test'
PICKLE_FOLDER = 'tune_pickle'


class SongDatabase():
    def __init__(self, song_folder, pickle_folder):
        self.con = mdb.connect('localhost', 'phatuser', 'phat623', 'djdb')
        self.song_dir = song_folder
        self.pickle_dir = pickle_folder

    def reset_db(self):
        """Resets the database, dropping Songs and making it again with ID, File_Path, Artist, Title, Usability, Tempo,
        Danceability, Liveness, Energy, and Pickle_Path"""
        with self.con:
            cur = self.con.cursor(mdb.cursors.DictCursor)
            cur.execute("DROP TABLE IF EXISTS Songs")
            cur.execute("CREATE TABLE Songs(Id INT PRIMARY KEY AUTO_INCREMENT, \
                File_Path VARCHAR(200) NOT NULL UNIQUE,\
                Artist VARCHAR(50) NOT NULL,\
                Title VARCHAR(50) NOT NULL,\
                Usable TINYINT(1),\
                Tempo FLOAT(4,1),\
                Danceability Float(6,6),\
                Liveness Float(6,6),\
                Energy DOUBLE(6,6),\
                Pickle_Path VARCHAR(200))")

    def populate_db(self):
        """For every file in the datase, it first looks in the echonest api for it. If it can't find it, it enters the 
        info with Usable as 0. If it can, it then instantiates a tune object. If the tune can create a song map, it pickles
        the map and stores the pickle filename and all the echonest data. Otherwise, it stores the data but with usability 
        as 0"""
        with self.con:
            cur = self.con.cursor(mdb.cursors.DictCursor)
            for subdir, dirs, files in os.walk(self.song_dir):
                for song_file in files:
                    try:
                        path = os.path.join(subdir,song_file)
                        path_db = self.escape(path)
                        print path
                        if not self.get_entry(path):
                            id3r = id3reader.Reader(path)
                            artist = id3r.getValue('performer')
                            song_name = id3r.getValue('title')
                            if not artist or not song_name:
                                usable = False
                                insert = "INSERT IGNORE INTO Songs(File_Path, Artist, Title, Usable, Tempo, Danceability, Liveness, Energy, Pickle_Path) \
                                    VALUES (%s, %s, %s, %s, NULL, NULL, NULL, NULL, NULL)"
                                cur.execute(insert,(path_db,'unknown','unknown', usable))
                            else:
                                artist_db = self.escape(artist)
                                song_name_db = self.escape(song_name)
                                echo_song = song.search(title=song_name, artist=artist, results=1)
                                if not echo_song:
                                    usable = False
                                    insert = "INSERT IGNORE INTO Songs(File_Path, Artist, Title, Usable, Tempo, Danceability, Liveness, Energy, Pickle_Path) \
                                        VALUES (%s, %s, %s, %s, NULL, NULL, NULL, NULL, NULL)"
                                    cur.execute(insert,(path_db, artist_db, song_name_db, usable))
                                elif echo_song:
                                    tempo = echo_song[0].audio_summary['tempo']
                                    danceability = echo_song[0].audio_summary['danceability']
                                    liveness = echo_song[0].audio_summary['liveness']
                                    energy = echo_song[0].audio_summary['energy']
                                    usable = False
                                    try: 
                                        tune_obj = Tune(path,artist,song_name)
                                        usable = bool(tune_obj.song_map)
                                        pickle_path = None
                                    except:
                                        pass                                
                                    if usable:
                                        pickle_path = self.pickle_dir + '/' + song_file.replace(".mp3","") + '.txt'
                                        output = open(pickle_path,'wb')
                                        pickle.dump(tune_obj.song_map, output)
                                        insert = "INSERT IGNORE INTO Songs(File_Path, Artist, Title, Usable, Tempo, Danceability, Liveness, Energy, Pickle_Path) \
                                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                                        cur.execute(insert,(path_db, artist_db, song_name_db, usable, tempo, danceability, liveness, energy, pickle_path))
                                    else: 
                                        insert = "INSERT IGNORE INTO Songs(File_Path, Artist, Title, Usable, Tempo, Danceability, Liveness, Energy, Pickle_Path) \
                                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NULL)"
                                        cur.execute(insert,(path_db, artist_db, song_name_db, usable, tempo, danceability, liveness, energy))
                    except util.EchoNestAPIError:
                        time.sleep(60)
        
    def get_entry(self,filepath):
        """gets entry of database based off of file path"""
        with self.con:
            cur = self.con.cursor(mdb.cursors.DictCursor)
            cur.execute("SELECT * FROM Songs WHERE Songs.File_Path LIKE " + "'" + self.escape(filepath) + "'")
            return cur.fetchone()

    def usable_songs(self):
        """returns list of dictionaries corresponding to usable songs"""
        with self.con:
            cur = self.con.cursor(mdb.cursors.DictCursor)
            cur.execute("SELECT * FROM Songs WHERE Songs.Usable LIKE 1")
            res = cur.fetchall()
            for d in res:
                d['File_Path'] = self.unescape(d['File_Path'])
                d['Artist'] = self.unescape(d['Artist'])
                d['Title'] = self.unescape(d['Title'])
            return [d for d in res]

    def get_pickle(self,p_path):
        """opens pickle file"""
        output =  open(p_path,'rb')
        return pickle.load(output)

    def print_db(self):
        """prints full database"""
        with self.con:
            cur = self.con.cursor(mdb.cursors.DictCursor)
            cur.execute("SELECT * FROM Songs")
            rows = cur.fetchall()
            print rows

    def escape(self, string):
        """escapes the given string for database storage"""
        return self.con.escape_string(string)

    def unescape(self, string):
        """unescapes the given string for usage"""
        return string.decode('string_escape')