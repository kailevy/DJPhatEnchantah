from pyechonest import *
import os 
from tune import Tune
import id3reader
import time
from echonest.remix.action import render
from tempo_adj import make_crossfade

TEMPO_THRESHOLD = 2
SCORE_THRESHOLD = 0.60

class Playlist():
    def __init__(self, folder, baseSong, numberOfsongs):
        self.length = numberOfsongs # length in terms of #songs, not duration
        self.dirs = os.listdir('./'+folder)
        self.build_playlist(folder+'/'+baseSong, self.length)
        
    def build_playlist(self, path_to_song, numberOfSongs):
        id3r = id3reader.Reader(path_to_song)
        basesong_name = id3r.getValue('title')
        baseartist = id3r.getValue('performer')
        print 'Adding %s to playlist' % basesong_name
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
                    self.max_tempo = max([tune.bpm for tune in self.playlist])
                    self.min_tempo = min([tune.bpm for tune in self.playlist])
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
                        if abs(self.max_tempo - score_board[song_name]) <= TEMPO_THRESHOLD \
                            or abs(self.min_tempo - score_board[song_name]) <= TEMPO_THRESHOLD:
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
                        if score <= SCORE_THRESHOLD and withinTempoRange \
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
                        elif score <= SCORE_THRESHOLD \
                            and new_song[0].title not in score_board \
                            and new_song[0].title not in added:
                            score_board[new_song[0].title] = new_song[0].audio_summary['tempo']

                        else:
                            not_compatible[new_song[0].title] = 0
                except util.EchoNestAPIError:
                    print '\nAPI rate limit has been exceeded. The program will resume in 60 seconds.\n'
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
        if abs(self.max_tempo - candidateSong.audio_summary['tempo']) <= TEMPO_THRESHOLD \
            or abs(self.min_tempo - candidateSong.audio_summary['tempo']) <= TEMPO_THRESHOLD:
            return score, True
        else:
            return score, False

def main():
    # Initiate playlist with a base song and length
    START = time.time()
    a = Playlist('song_test', "Love Story - Taylor Swift.mp3", 10)
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
        i[2], i[3] = i[0].choose_jump_point(position=i[1])

    # print rp: [[<tune.Tune instance at 0x7f848b1149e0>, 'start', 0, 66], 
    # [<tune.Tune instance at 0x7f8489d7cfc8>, 'middle', 14, 64], 
    # [<tune.Tune instance at 0x7f8489f35ea8>, 'middle', 37, 51], 
    # [<tune.Tune instance at 0x7f8489b340e0>, 'end', 36, 146]]

    def make_transition(l1, l2):
        # l1, l2 are lists of order [self.tune, self.position, start_bar_index, end_bar_index]

        # Start cutting at the final_bar of the first song
        final_bar = l1[0].bars[l1[3]-1: l1[3]+1]

        # Cut into the first two bars of the second song
        first_bar = l2[0].bars[l2[2]: l2[2]+2]

        # Duration is length of the first two bars of the second song because
        # it has to line up with the [i+2: end] bars.
        duration = sum([i.duration for i in first_bar])

        # Return iterable cross faded object
        return make_crossfade(l1[0].tune, l2[0].tune, final_bar[0].start, first_bar[0].start, duration)

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