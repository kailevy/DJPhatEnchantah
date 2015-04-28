from pyechonest import *
import os 
from tune import Tune
import id3reader
import time

class Playlist():
    def __init__(self, folder, baseSong, numberOfsongs):
        self.length = numberOfsongs # length in terms of #songs, not duration
        self.dirs = os.listdir('./'+folder)
        self.build_playlist(folder+'/'+baseSong, self.length)
        
    def build_playlist(self, path_to_song, numberOfSongs):
        id3r = id3reader.Reader(path_to_song)
        basesong_name = id3r.getValue('title')
        baseartist = id3r.getValue('performer')
        original = song.search(title=basesong_name, artist=baseartist, results=1)

        if original:
            self.baseSong = Tune(path_to_song, original[0].title, original[0].artist_name, original[0].audio_summary['tempo'])
            self.playlist = [self.baseSong]
            score_board = {} # Store songs that are compatible but at the time outside the tempo range
            not_compatible = {} # Store rejected songs
            i = 0 # index of item in song folder/directory
            k = 0 # keeps track of no. of times program has gone through the entire directory. Goes through twice just in case.

            while len(self.playlist) < numberOfSongs and k < 2:
                try:
                    self.max_tempo, self.min_tempo = max([tune.bpm for tune in self.playlist]), min([tune.bpm for tune in self.playlist])
                    added = [j.songName for j in self.playlist]
                    new_song = False
                    try: path = 'song_test/' + self.dirs[i]
                    except IndexError:
                        i = 0
                        k += 1 
                        # print 'Songs exhausted before length of playlist satisfied. Returning current result.'
                        # for i in self.playlist:
                        #     print i.songName, i.bpm
                        # return self.playlist

                    # Set search values for current song
                    id3r = id3reader.Reader(path)
                    artist = id3r.getValue('performer')
                    song_name = id3r.getValue('title')

                    # If current song is the original song (in that same folder), skip
                    if song_name == basesong_name and artist == baseartist: 
                        i += 1

                    # Else searches the memoized scoreboard to see if it is there. If so
                    # check if it is within the tempo range, if so add it to the playlist.
                    elif song_name in score_board:                    
                        if abs(self.max_tempo - score_board[song_name]) <= 10 \
                            or abs(self.min_tempo - score_board[song_name]) <= 10:
                            try:
                                tune = Tune(path, song_name, artist, score_board[song_name])
                                self.playlist.append(tune)
                                print "Adding %s to playlist" %song_name
                                score_board.pop(song_name, None)
                                i = 0
                            except RuntimeError:
                                pass
                        else:
                            i += 1

                    elif song_name in not_compatible:
                        i += 1

                    # If song is completely new then it initiates an ECHONEST search        
                    else:
                        new_song = song.search(title=song_name, artist=artist, results=1)
                        i += 1

                    # If a result is returned, and the score and tempo are compatible, then add it to the playlist
                    if new_song:
                        # print new_song[0].title, new_song[0].audio_summary['tempo']
                        score, withinTempoRange = self.compare_songs(original[0], new_song[0]) 
                        if score <= 0.60 and withinTempoRange \
                            and new_song[0].title not in not_compatible \
                            and new_song[0].title not in added:
                            try:
                                self.playlist.append(Tune(path, new_song[0].title, 
                                    new_song[0].artist_name, new_song[0].audio_summary['tempo']))
                                print "Adding %s to playlist" %new_song[0].title
                                i = 0
                            except RuntimeError:
                                pass

                        # Else memoize it in the scoreboard if it is not there already    
                        elif score <= 0.60 \
                            and new_song[0].title not in score_board \
                            and new_song[0].title not in added:
                            score_board[new_song[0].title] = new_song[0].audio_summary['tempo']

                        else:
                            not_compatible[new_song[0].title] = 0
                except util.EchoNestAPIError:
                    time.sleep(60)
        else:
            print 'Try another song.'

    def sort_playlist(self):
        new = []
        for i in range(len(self.playlist)):
            item = min(self.playlist, key=lambda x: x.bpm)
            new.append(item)
            self.playlist.remove(item)

        self.playlist = new
        
    def compare_songs(self, baseSong, candidateSong):
        score = 0
        # based on danceability, liveness, energy and tempo
        for i in ['danceability', 'liveness', 'energy']:
            score += abs(baseSong.audio_summary[i] - candidateSong.audio_summary[i])

        # checks if candidate song is within tempo range of the last song in the playlist
        if abs(self.max_tempo - candidateSong.audio_summary['tempo']) <= 10 \
            or abs(self.min_tempo - candidateSong.audio_summary['tempo']) <= 10:
            return score, True
        else:
            return score, False

a = Playlist('song_test', 'Little Things - One Direction.mp3', 10)
a.sort_playlist()
for i in a.playlist:
    print i.songName, i.artist, i.bpm