from pyechonest import *
import os 
from tune import Tune
import id3reader

class Playlist():
    def __init__(self, folder, baseSong, numberOfsongs):
        self.length = numberOfsongs # length in terms of #songs, not duration
        self.dirs = os.listdir('./'+folder)
        self.playlist = self.build_playlist(folder+'/'+baseSong, self.length)
        
    def build_playlist(self, path_to_song, numberOfSongs):
        id3r = id3reader.Reader(path_to_song)
        basesong_name = id3r.getValue('title')
        baseartist = id3r.getValue('performer')
        original = song.search(title=basesong_name, artist=baseartist, results=1)

        if original:
            self.baseSong = Tune(path_to_song, original[0].title, original[0].artist_name, original[0].audio_summary['tempo'])
            playlist = [self.baseSong]
            i = 0
            while len(playlist) < numberOfSongs:
                try: path = 'song_test/' + self.dirs[i]
                except IndexError: 
                    print 'Songs exhausted before length of playlist satisfied. Returning current result.'
                    return playlist
                id3r = id3reader.Reader(path)
                artist = id3r.getValue('performer')
                song_name = id3r.getValue('title')
                if song_name == basesong_name and artist == baseartist: 
                    new_song = 0
                else:
                    new_song = song.search(title=song_name, artist=artist, results=1)
                if new_song:
                    print new_song[0].title
                    if self.score_songs(original[0], new_song[0]) <= 0:
                        print "Adding %s to playlist" %new_song[0].title
                        playlist.append(Tune(path, new_song[0].title, new_song[0].artist_name, new_song[0].audio_summary['tempo']))
                i += 1
        else:
            print 'Try another song.'
        return playlist
        
    def score_songs(self, baseSong, candidateSong):
        score = 0
        # based on danceability, liveness, energy and tempoo
        for i in ['danceability', 'liveness', 'energy', 'tempo']:
            score += abs(baseSong.audio_summary[i] - candidateSong.audio_summary[i])
        return score

a = Playlist('song_test', '01 Radioactive.mp3', 3)