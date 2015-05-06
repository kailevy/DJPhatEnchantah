from pyechonest import *
import os, argparse, time, random
import id3reader
from echonest.remix.action import render
from tempo_adj import make_crossmatch
from database import SongDatabase
from tune import Tune
# from pydub import AudioSegment

TEMPO_THRESHOLD = 2
SCORE_THRESHOLD = 0.30
TRAN_BARS = 3 #Number of bars to transition for

class Playlist():
    def __init__(self, folder, baseSong, numberOfsongs):
        self.length = numberOfsongs
        self.dirs = os.listdir('./'+folder)
        self.db = SongDatabase(folder,'tune_pickle')
        self.usable_songs = self.db.usable_songs()
        random.shuffle(self.usable_songs)
        self.build_playlist(folder+'/'+baseSong, self.length)
        
    def build_playlist(self, path_to_song, numberOfSongs):
        """Using the base song, build a playlist of songs with scores and tempo
        compatible with the base song"""

        base_song = self.db.get_entry(path_to_song)
        print '\nAdding %s to playlist' % base_song['Title']

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
        """Add a song to the playlist"""
        tune = Tune(new_song['File_Path'], new_song['Artist'], new_song['Title'], new_song['Tempo'], self.db.get_pickle(new_song['Pickle_Path']))
        self.playlist.append(tune)
        self.added.append(new_song['File_Path'])
        print "Adding %s to playlist" %new_song['Title']

    def sort_playlist(self):
        """Sort playlist in order of bpm from lowest to highest"""
        new = []
        for i in range(len(self.playlist)):
            item = min(self.playlist, key=lambda x: x.bpm)
            new.append(item)
            self.playlist.remove(item)

        self.playlist = new
        
    def compare_songs(self, baseSong, otherSong):
        """Computes compatibility score between baseSong and otherSong"""
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

    def splice_songs(self):
        """Add the following information to each song in the playlist: its 
        position in the playlist (start, middle, end), its starting bar and its
        ending bar"""
        ordering = ['start'] + ['middle']*(len(self.playlist)-2) + ['end']

        rp = [0] * len(self.playlist)

        for i in range(len(self.playlist)):
            rp[i] = [self.playlist[i], ordering[i], 0, 0]

        for i in rp:
            i[2], i[3] = i[0].choose_jump_point(position=i[1])

        self.playlist = rp

    def mix_songs(self):
        """Splice the bars lists of the songs in the playlist according to the
        results returned by choose_jump_point() for each song, and add the
        transition between each two songs."""
        output_song = []
        p = self.playlist
        switch_durations = []

        # Complicated for loop to put the output song together
        for i in range(len(p)):
            if p[i][1] == 'start':
                add = p[i][0].bars[: p[i][3]-(TRAN_BARS-1)] #from 0 to end-2
                output_song += add
                switch_durations.append(sum([j.duration for j in add]))
            if p[i][1] == 'middle':
                add = p[i][0].bars[p[i][2]+TRAN_BARS : p[i][3]-(TRAN_BARS-1)] #from start+3 to end-2
                output_song += add
                switch_durations.append(sum([j.duration for j in add]))
            if p[i][1] == 'end':
                add = p[i][0].bars[p[i][2]+TRAN_BARS :] #from start+3
                output_song += add
                switch_durations.append(sum([j.duration for j in add]))
            try: 
                trans = make_transition(p[i], p[i+1])
                output_song += trans[0]
                switch_durations.append(trans[1])
            except IndexError: pass

        self.mix = output_song
        return switch_durations

    def show(self):
        """Nicely display playlist"""
        j = 1
        print '\n===== PLAYLIST ORDER =====\n'
        for i in self.playlist:
            print "%d. %s by %s" %(j, i[0].songName, i[0].artist)
            j += 1
        print ''


def make_transition(l1, l2):
    """Create beat matching transition between song1 (l1) and song2 (l2)"""
    # l1, l2 are lists of order [Tune instance, self.position, start_bar_index, end_bar_index]

    final_bar = l1[0].bars[l1[3]-(TRAN_BARS-1): l1[3]+1] #from end-2 to end+1
    first_bar = l2[0].bars[l2[2]: l2[2]+TRAN_BARS]

    return make_crossmatch(l1[0].tune, l2[0].tune, final_bar, first_bar)


def add_effects(switch_durations):
    """Kai can you write this docstring?"""
    effect_dir = 'hype'
    mix = AudioSegment.from_mp3(output_file + '.mp3') - 3
    effect_list = []

    #load effects except for end
    for files in os.listdir(effect_dir):
        if not files == 'end.wav':
            effect_list.append(AudioSegment.from_wav(effect_dir + '/' + files) + 2)
    mix_sections = []
    hype_sections = []
    time_pointer = 0
    switch_times = [0]

    #makes cumulative switch-timestamps, give or take 5 seconds
    for i in switch_durations:
        if i < 20:
            switch_times.append((time_pointer + random.randint(-5,5)) * 1000)
        else: time_pointer += i

    #creates sections out of those timestamps, separating 5 second 'effect' intervals
    for i in range(len(switch_times)-1):
        mix_sections.append(mix[switch_times[i]:switch_times[i+1]-5000])
        hype_sections.append(mix[switch_times[i+1]-5000:switch_times[i+1]])
    hype_sections[0] = hype_sections[0] - 4
    hype_sections[0] = hype_sections[0].overlay(random.choice(effect_list), position=0)
    #puts in the first section and effect section
    full_mix = mix_sections[0] + hype_sections[0]

    #puts in following sections and effect sections
    for i in range(1,len(hype_sections)):
        full_mix += mix_sections[i]
        hype_sections[i] = hype_sections[i] - 4
        hype_sections[i] = hype_sections[i].overlay(random.choice(effect_list), position=0)
        full_mix += hype_sections[i]

    #adds last full section and effect
    full_mix += mix[switch_times[-1]:] + AudioSegment.from_wav(effect_dir + '/end.wav')
    full_mix.export(output_file+'.mp3',format='mp3')


def main(song_directory,file_path,num_songs, output_file, effects=False):
    START = time.time()

    a = Playlist(song_directory, file_path, int(num_songs))
    a.sort_playlist()
    a.splice_songs()
    switch_durations = a.mix_songs()

    render(a.mix, output_file + '.mp3', verbose=False)

    if effects:
        add_effects(switch_durations, output_file)

    a.show()
    print '\nTook %f seconds to compile and render playlist\n' %round(time.time()-START, 1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('song_directory', help='Enter the base directory where your target music is (must only have music files and folder)')
    parser.add_argument('file_path', help='Enter the file path of your song, excluding the base directory')
    parser.add_argument('songs_number', help='Enter the number of songs to be mixed')
    parser.add_argument('output_file', help='Enter the name of the output file')
    parser.add_argument('--eff', action='store_true', help='Enter for whether you want effects')
    args = parser.parse_args()

    main(args.song_directory,args.file_path,args.songs_number,args.output_file,args.eff)

