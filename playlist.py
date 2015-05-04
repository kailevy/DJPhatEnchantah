from pyechonest import *
import os 
from tune import Tune
import id3reader
import time
from echonest.remix.action import render
from tempo_adj import make_crossmatch
from database import SongDatabase

TEMPO_THRESHOLD = 2
SCORE_THRESHOLD = 0.60

class Playlist():
    def __init__(self, folder, baseSong, numberOfsongs):
        self.length = numberOfsongs # length in terms of #songs, not duration
        self.dirs = os.listdir('./'+folder)
        #calling from database        
        self.db = SongDatabase(folder,'tune_pickle')
        self.usable_songs = self.db.usable_songs()
        self.build_playlist(folder+'/'+baseSong, self.length)
        
    def build_playlist(self, path_to_song, numberOfSongs):
        base_song = self.db.get_entry(path_to_song)
        print base_song
        print 'Adding %s to playlist' % base_song['Title']

        if base_song['Usable']:
            self.baseSong = Tune(path_to_song, base_song['Artist'], base_song['Title'], base_song['Tempo'], 
                            self.db.get_pickle(base_song['Pickle_Path']))
            self.playlist = [self.baseSong]
            self.added = [base_song['File_Path']]
            score_board = {} # Store songs that are compatible but at the time outside the tempo range
            not_compatible = {} # Store rejected songs
            i = 0 # index of item in song folder/directory
            k = 0 # keeps track of no. of times program has gone through the entire directory. Goes through twice just in case.

            while len(self.playlist) < numberOfSongs and k < 2:
                try:
                    self.max_tempo = max([tune.bpm for tune in self.playlist])
                    self.min_tempo = min([tune.bpm for tune in self.playlist])
                    try: new_song = self.usable_songs[i]
                    except IndexError:
                        i = 0
                        k += 1

                    # If current song is the original song (in that same folder), skip
                    if new_song['File_Path'] == base_song['File_Path']: 
                        i += 1
                    # Else searches the memoized scoreboard to see if it is there. If so
                    # check if it is within the tempo range, if so add it to the playlist.
                    elif new_song['File_Path'] in score_board:                    
                        if abs(self.max_tempo - score_board[new_song['File_Path']]) <= TEMPO_THRESHOLD \
                        or abs(self.min_tempo - score_board[new_song['File_Path']]) <= TEMPO_THRESHOLD:
                            self.add(new_song)
                            score_board.pop(new_song['File_Path'])
                            i = 0
                        else:
                            i += 1
                    elif new_song['File_Path'] in not_compatible:
                        i += 1
                    elif new_song:
                        score, withinTempoRange = self.compare_songs(base_song, new_song) 
                        if score <= SCORE_THRESHOLD and withinTempoRange \
                            and new_song['File_Path'] not in self.added:
                            self.add(new_song)
                            i = 0
                        # Else memoize it in the scoreboard if it is not there already    
                        elif score <= SCORE_THRESHOLD \
                            and new_song['File_Path'] not in score_board \
                            and new_song['File_Path'] not in self.added:
                            score_board[new_song['File_Path']] = new_song['Tempo']
                        else:
                            not_compatible[new_song['File_Path']] = 0
                except util.EchoNestAPIError:
                    print '\nAPI rate limit has been exceeded. The program will resume in 60 seconds.\n'
                    time.sleep(60)
        else:
            print 'Try another song.'

    def add(self, new_song):
        tune = Tune(new_song['File_Path'], new_song['Title'], new_song['Artist'], new_song['Tempo'], self.db.get_pickle(new_song['Pickle_Path']))
        self.playlist.append(tune)
        self.added.append(new_song['File_Path'])
        print "Adding %s to playlist" %new_song['Title']

    def sort_playlist(self):
        new = []
        for i in range(len(self.playlist)):
            item = min(self.playlist, key=lambda x: x.bpm)
            new.append(item)
            self.playlist.remove(item)

        self.playlist = new
        
    def compare_songs(self, baseSong, otherSong):
        score = 0
        # based on danceability, liveness, energy and tempo
        for i in ['Danceability', 'Liveness', 'Energy']:
            score += abs(baseSong[i] - otherSong[i])

        # checks if candidate song is within tempo range of the last song in the playlist
        if abs(self.max_tempo - otherSong['Tempo']) <= TEMPO_THRESHOLD \
            or abs(self.min_tempo - otherSong['Tempo']) <= TEMPO_THRESHOLD:
            return score, True
        else:
            return score, False

def main():
    # Initiate playlist with a base song and length
    START = time.time()
    a = Playlist('song_test', "Future Islands/Singles/01 Seasons (Waiting On You).mp3", 3)
    a.sort_playlist()

    ordering = ['start'] + ['middle']*(len(a.playlist)-2) + ['end']

    # Create real_playlist
    rp = [0] * len(a.playlist)

    # Comes out to be like [[Tune, 'start'], [Tune, 'middle'], ..., [Tune, 'end']]
    for i in range(len(a.playlist)):
        rp[i] = [a.playlist[i], ordering[i], 0, 0]


    # Print playlist
    print ''
    for i in rp:
        print i[0].songName, i[0].bpm, i[1]
    print ''

    # Start the processing
    output_song = []
    # Add starting and ending indices of bars of each song in real_playlist
    for i in rp:
        print "Mixing %s" %i[0].songName
        i[2], i[3] = i[0].choose_jump_point2(position=i[1])
        # i[2], i[3] = i[0].choose_jump_point()

    # print rp: [[<tune.Tune instance at 0x7f848b1149e0>, 'start', 0, 66], 
    # [<tune.Tune instance at 0x7f8489d7cfc8>, 'middle', 14, 64], 
    # [<tune.Tune instance at 0x7f8489f35ea8>, 'middle', 37, 51], 
    # [<tune.Tune instance at 0x7f8489b340e0>, 'end', 36, 146]]

    def make_transition(l1, l2):
        # l1, l2 are lists of order [Tune instance, self.position, start_bar_index, end_bar_index]

        # Start cutting at the final two bars of the first song
        final_bar = l1[0].bars[l1[3]-1: l1[3]+1]

        # Cut into the first two bars of the second song
        first_bar = l2[0].bars[l2[2]: l2[2]+2]

        # Return iterable crossmatched object
        return make_crossmatch(l1[0].tune, l2[0].tune, final_bar, first_bar)

    for i in range(len(rp)):
        if rp[i][1] == 'start':
            output_song += rp[i][0].bars[: rp[i][3]-1]
        if rp[i][1] == 'middle':
            output_song += rp[i][0].bars[rp[i][2]+2 : rp[i][3]-1]
        if rp[i][1] == 'end':
            output_song += rp[i][0].bars[rp[i][2]+2 :]
        try: output_song += make_transition(rp[i], rp[i+1])
        except IndexError: pass

    render(output_song, 'fullMix.mp3', True)
    print '\nTook %f seconds to compile and render playlist' %round(time.time()-START, 1)

main()