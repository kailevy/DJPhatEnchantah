import urllib2, urllib, os, json, math, pyechonest, sys, argparse

import echonest.remix.audio as audio
from echonest.remix.action import render, Crossfade
from copy import deepcopy

DISPLAY_KEY = os.environ.get('LYRICFIND_DISPLAY_API_KEY')
LRC_KEY = os.environ.get('LYRICFIND_LRC_API_KEY')
SEARCH_KEY = os.environ.get('LYRICFIND_SEARCH_API_KEY')
METADATA_KEY = os.environ.get('LYRICFIND_METADATA_API_KEY')

LYRICFIND_DISPLAY_URL = 'http://test.lyricfind.com/api_service/lyric.do?'

def get_words(aString):
    """ Returns a dictionary of word counts, given a string"""
    freq = {}
    for word in aString.lower().split():
        freq[word] = freq.get(word,0) + 1
    return freq

def compute_similarity(d1, d2):
    """ Computes cosine similarity of the two dictionaries of words. This method was adapted from:
    http://stackoverflow.com/questions/15173225/how-to-calculate-cosine-similarity-given-2-sentence-strings-python"""
    intersection = set(d1.keys()) & set(d2.keys())
    numerator = sum([d1[w] * d2[w] for w in intersection])
    sum1 = sum([d1[w] ** 2 for w in d1.keys()])
    sum2 = sum([d2[w] ** 2 for w in d2.keys()])
    denominator = math.sqrt(sum1) * math.sqrt(sum2)

    if not denominator:
        return 0.0
    else:
        return float(numerator) / denominator

class Tune():
    """Class for one song in the playlist"""

    def __init__(self,path_to_song, artist, name, tempo=None, song_map=None):
        # Set all necessary attributes to allow for fruitful analysis
        self.tune = audio.LocalAudioFile(path_to_song, verbose=False)
        if not tempo:
            self.track = pyechonest.track.track_from_filename(path_to_song)
            self.bpm = getattr(self.track,'tempo')
        else:
            self.bpm = tempo
        self.segments = getattr(self.tune.analysis, 'segments')
        self.bars = getattr(self.tune.analysis, 'bars')
        self.beats = getattr(self.tune.analysis, 'beats')
        self.fade = getattr(self.tune.analysis, 'end_of_fade_in')
        if not self.fade:
            self.fade = 0
        self.songName = name
        self.artist = artist
        if song_map:
            self.song_map = song_map
        else:
            self.song_map = []
            lyrics, lrc = self.find_lyrics()
            if lyrics and lrc:
                self.get_song_map(lyrics,lrc) 
        self.chorus_count = len([i for i in self.song_map if i[2] == 'chorus'])

    def find_lyrics(self):
        """Retrieves lyrics and timestamped lyrics for the tune"""
        try: 
            json_response = self.get_json()
            lyrics = json_response['track']['lyrics'] # Get lyrics alone
            lrc = json_response['track']['lrc'] # Get lyrics with timestamps
        except KeyError:
            lyrics = None
            lrc = None
        return (lyrics, lrc)

    def get_json(self):
        """Makes API request to retrieve song's lyrics"""
        artist = self.artist.replace(' ', '+').encode('ascii', 'ignore')
        song_name = self.songName.replace(' ', '+').encode('ascii', 'ignore')
        end = urllib.urlencode({'apikey': DISPLAY_KEY, 'lrckey': LRC_KEY, 
                                'territory': 'US', 'reqtype': 'default',
                                'format': 'lrc', 'output': 'json',
                                'trackid': 'artistname:' + artist + ',trackname:' + song_name})
        url = LYRICFIND_DISPLAY_URL + end
        f = urllib2.urlopen(url)
        return json.loads(f.read())

    def get_song_map(self, lyrics, lrc):
        """Returns a list of tuples in the form (start, end, 'verse'/'chorus')
        that linearly maps out the lyrics of the song"""

        # Get all the choruses in the lrc
        choruses = self.find_chorus_freq(lyrics.split('\n'))

        # Add each line to chorus_lines
        chorus_lines = []
        for i in choruses:
            if i not in chorus_lines:
                chorus_lines += [j.strip() for j in i.split('\n')]

        verse, chorus = [], []
        i = 0

        # Goes through lrc line by line. Saves each line in the verse or
        # chorus list, then if blank line (new paragraph) is found empties out
        # the list and save the data in the song_map as a [starttime, endtime, 'chorus'/'verse'] list
        while i < len(lrc):
            if lrc[i]['line']:
                if lrc[i]['line'].strip() in chorus_lines:
                    chorus.append(lrc[i]['milliseconds'])
                else:
                    verse.append(lrc[i]['milliseconds'])
            if not lrc[i]['line'] or i==len(lrc)-1:
                if verse:
                    self.song_map.append([int(verse[0]), int(verse[-1]), 'verse'])
                    verse = []
                if chorus:
                    self.song_map.append([int(chorus[0]), int(chorus[-1]), 'chorus'])
                    chorus = []
            i += 1

        print 'original', self.song_map
        self.song_map = self.group_map(sorted([i for i in self.song_map if i[0] != i[1]], key=lambda x:x[0]))

        return self.song_map

    def find_chorus_freq(self, split_pars):
        """Finds chorus based off of similar word frequencies"""
        par_freqs = []
        chorus = []

        for par in split_pars:
            par_freqs.append(get_words(par))

        for i in range(len(split_pars)):
            for j in range(i+1,len(split_pars)):
                if compute_similarity(par_freqs[j],par_freqs[i]) > 0.6 and split_pars[i]:
                    chorus.append(split_pars[i])

        return chorus

    def choose_jump_point(self, position='start'):
        """Attempts to choose the bars of the track by taking the start of one song, and 
        setting the end to be after the 2nd + chorus as long as there is no vocals immediately
        after"""
        self.position = position

        if self.position == 'start':
            return self.find_tail()
        elif self.position == 'end':
            return self.find_start()
        elif self.position == 'middle':
            a = self.find_start()
            b = self.find_tail()
            return a[0], b[1]

    def find_start(self):
        """Finds the part to cut INTO the song from another song.
        Has to be before the verse before the second chorus, because find_tail 
        finds anything after the second chorus.""" 
        chor_count = 0
        i = 0
        if self.chorus_count == 1:
            CHORUS_THRESHOLD = self.chorus_count - 1
        else:
            CHORUS_THRESHOLD = self.chorus_count//2.0 + 1

        # Filter out self.song_map so that the only parts available are before
        # the second chorus
        available = []
        while chor_count < CHORUS_THRESHOLD and i < len(self.song_map):
            if self.song_map[i][2] == 'chorus':
                chor_count += 1
            if chor_count > CHORUS_THRESHOLD:
                pass
            else:
                available.append(self.song_map[i])
            i += 1

        verse_index = [i for i,j in enumerate(available) if j[2] == 'verse']

        # Find 6 second gap into a verse
        if len(verse_index) <= 1:
            return self.get_bars(self.song_map[0][0], None)
        else:
            for i in verse_index:
                start_verse = available[i][0]
                end_last_section = available[i-1][1]
                if abs(start_verse - end_last_section) >= 4:
                    return self.get_bars(available[i][0], None)


    def find_tail(self):
        """Finds the part of the song to cut OUT OF. Has to be after the second
        chorus."""
        i = 0
        chor_count = 0
        available = deepcopy(self.song_map)

        if self.chorus_count == 1:
            CHORUS_THRESHOLD = self.chorus_count - 1
        else:
            CHORUS_THRESHOLD = self.chorus_count//2.0 + 1

        # Remove sections from the available list up to but not including the 
        # second chorus. Uncomment print statements to see which option the 
        # program went for
        while chor_count < CHORUS_THRESHOLD:
            if available[0][2] == 'chorus':
                chor_count += 1
            if chor_count < CHORUS_THRESHOLD:
                available.pop(0)

        chorus_index = [i for i,j in enumerate(available) if j[2] == 'chorus']

        if len(chorus_index) == 1:
            return self.get_bars(0, available[chorus_index[0]][1])
        else:
            for i in chorus_index:
                end_chorus = available[i][1]
                try: 
                    start_next_section = available[i+1][0]
                    if abs(start_next_section - end_chorus) >= 2:
                        return self.get_bars(0, (available[i][1]+start_next_section)/2.0)
                except IndexError: pass 

        final_chorus = chorus_index[-1]
        return self.get_bars(0, available[final_chorus][1])

    def group_map(self, oldmap):
        newmap = []
        i = 0

        while i < len(oldmap):
            start = oldmap[i][0]/1000.0
            current_section = oldmap[i][2]
            try:
                while oldmap[i+1][2] == current_section:
                    i += 1
            except IndexError: pass
            end = oldmap[i][1]/1000.0
            assert(oldmap[i][2] == current_section)
            newmap.append([start, end, current_section])
            i += 1

        return newmap

    def find_chorus_bars(self):
        """Finds and returns the start and end bars of each chorus found in the
        song map"""
        all_chorus = []
        choruses = [i for i in self.song_map if i[2] == 'chorus']
        i = 0

        # Complicated while loop to record start and end times of full choruses
        # taking into account the fact that one chorus may be split into two 
        # paragraphs
        while i < len(choruses)-1:
            start = choruses[i][0]
            end = choruses[i][1]
            next_start = choruses[i+1][0]
            while next_start-end<=5000 and i+1<len(choruses):
                i += 1
                try: end, next_start = choruses[i][1], choruses[i+1][0]
                except IndexError: 
                    all_chorus.append([start/1000.0, choruses[i][1]/1000.0])
                    break
            else:
                all_chorus.append([start/1000.0, end/1000.0])
                if next_start and i == len(choruses)-2:
                    all_chorus.append([next_start/1000.0, choruses[i+1][1]/1000.0])
            i += 1

        for j in range(len(all_chorus)):
            all_chorus[j] = self.get_bars(all_chorus[j][0], all_chorus[j][1])

        # Returns only choruses that are longer than four bars (other results
        # are anomalies)
        return [i for i in all_chorus if i[1] - i[0] > 4]

    def get_bars(self, start_time, end_time=None):
        """Finds and returns the indices of the bars that start and end of the 
        chorus. This function works by, keeping track of the scores of the current
        and previous bars. If the current score becomes higher, it means that the
        loop has passed over the right bar, and we save the previous bar's index"""

        startScore, endScore = 10000000, 10000000
        first_bar = 0
        last_bar = len(self.bars)-1
        found_first = False

        # print self.fade


        for i, bar in enumerate(self.bars):
            if not found_first:
                prevStartScore, startScore = startScore, abs(bar.start - start_time)
                if startScore > prevStartScore: 
                    first_bar = i-1
                    found_first = True

            if end_time:
                prevEndScore, endScore = endScore, abs(bar.start - end_time)
                if endScore > prevEndScore: 
                    last_bar = i-1
                    break

            # prevEndScore, endScore = endScore, abs(bar.start - self.fade - end_time)
            # if endScore > prevEndScore: 
            #     last_bar = i-1
            #     break
        if end_time:
            return max(0, first_bar-2), last_bar
        else:
            return max(0, first_bar-2),len(self.bars)-1

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('artist', help='Enter the artist(s) of your song')
    parser.add_argument('songName', help='Enter the name of your song')
    parser.add_argument('fileName', help='Enter the file name of your song')
    args = parser.parse_args()

    bs = Tune(args.fileName, args.artist, args.songName)
    bars = bs.choose_jump_point(position='middle')
    print len(bs.bars)
    print bars
    for i in bars: print bs.bars[i].start
    print bs.song_map
    # render(bs.bars[bars[0]:bars[1]+4], 'play.mp3', True)

