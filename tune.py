import urllib2, urllib, os, json, math, pyechonest, sys, argparse

import echonest.remix.audio as audio
from echonest.remix.action import render, Crossfade

pyechonest.config.ECHO_NEST_API_KEY = "SKUP2XKX0MRWEOBIE"

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

    def __init__(self,path_to_song, name, artist):
        # Set all necessary attributes to allow for fruitful analysis
        self.tune = audio.LocalAudioFile(path_to_song)
        self.track = pyechonest.track.track_from_filename(path_to_song)
        self.bpm = getattr(self.track,'tempo')
        self.segments = getattr(self.tune.analysis, 'segments')
        self.bars = getattr(self.tune.analysis, 'bars')
        self.beats = getattr(self.tune.analysis, 'beats')
        self.fade = getattr(self.tune.analysis, 'end_of_fade_in')
        self.songName = name
        self.artist = artist

        # Set further attributes through class methods
        self.find_lyrics()
        self.get_song_map()

    def find_lyrics(self):
        """Retrieves lyrics and timestamped lyrics for the tune"""
        try: 
            json_response = self.get_json()
            self.lyrics = json_response['track']['lyrics'] # Get lyrics alone
            self.lrc = json_response['track']['lrc'] # Get lyrics with timestamps
        except KeyError:
            raise RuntimeError 
            # print 'Song could not be processed.'
            # sys.exit()

    def get_json(self):
        """Makes API request to retrieve song's lyrics"""
        artist = self.artist.replace(' ', '+')
        song_name = self.songName.replace(' ', '+')
        end = urllib.urlencode({'apikey': DISPLAY_KEY, 'lrckey': LRC_KEY, 
                                'territory': 'US', 'reqtype': 'default',
                                'format': 'lrc', 'output': 'json',
                                'trackid': 'artistname:' + artist + ',trackname:' + song_name})
        url = LYRICFIND_DISPLAY_URL + end
        f = urllib2.urlopen(url)
        return json.loads(f.read())

    def get_song_map(self):
        """Returns a list of tuples in the form (start, end, 'verse'/'chorus')
        that linearly maps out the lyrics of the song"""

        # Get all the choruses in the lrc
        choruses = self.find_chorus_freq(self.lyrics.split('\r\n\r\n'))

        # Add each line to chorus_lines
        chorus_lines = []
        for i in choruses:
            chorus_lines += i.split('\r\n')

        verse, chorus, self.song_map = [], [], []
        i = 0

        # Goes through self.lrc line by line. Saves each line in the verse or
        # chorus list, then if blank line (new paragraph) is found empties out
        # the list and save the data in the song_map as a [starttime, endtime, 'chorus'/'verse'] list
        while i < len(self.lrc):
            if self.lrc[i]['line']:
                if self.lrc[i]['line'].strip() in chorus_lines:
                    chorus.append(self.lrc[i]['milliseconds'])
                else:
                    verse.append(self.lrc[i]['milliseconds'])
            if not self.lrc[i]['line'] or i==len(self.lrc)-1:
                if verse:
                    self.song_map.append([int(verse[0]), int(verse[-1]), 'verse'])
                    verse = []
                if chorus:
                    self.song_map.append([int(chorus[0]), int(chorus[-1]), 'chorus'])
                    chorus = []
            i += 1

        return self.song_map   

    def find_chorus_freq(self, split_pars):
        """Finds chorus based off of similar word frequencies"""
        par_freqs = []
        chorus = []

        for par in split_pars:
            if 'chorus' in par.split('\r\n')[0].lower():
                if len(par.split('\r\n')) > 2:
                    chorus += par.split('\r\n')[1:]
            par_freqs.append(get_words(par))

        for i in range(len(split_pars)):
            for j in range(i+1,len(split_pars)):
                if compute_similarity(par_freqs[j],par_freqs[i]) > 0.6 and split_pars[i]:
                    chorus.append(split_pars[i])

        return chorus

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

        # print choruses
        # print all_chorus

        for j in range(len(all_chorus)):
            all_chorus[j] = self.get_bars(all_chorus[j][0], all_chorus[j][1])

        # Returns only choruses that are longer than four bars (other results
        # are anomalies)
        return [i for i in all_chorus if i[1] - i[0] > 4]

    def get_bars(self, start_time, end_time):
        """Finds and returns the indices of the bars that start and end of the 
        chorus. This function works by, keeping track of the scores of the current
        and previous bars. If the current score becomes higher, it means that the
        loop has passed over the right bar, and we save the previous bar's index"""

        startScore, endScore = 10000000, 10000000
        first_bar = 0
        last_bar = 1
        found_first = False

        for i, bar in enumerate(self.bars):
            if not found_first:
                prevStartScore, startScore = startScore, abs(bar.start - self.fade - start_time)
                if startScore > prevStartScore: 
                    first_bar = i-1
                    found_first = True

            prevEndScore, endScore = endScore, abs(bar.start - self.fade - end_time)
            if endScore > prevEndScore: 
                last_bar = i-1
                break

        return first_bar, last_bar

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('artist', help='Enter the artist(s) of your song')
    parser.add_argument('songName', help='Enter the name of your song')
    parser.add_argument('fileName', help='Enter the file name of your song')
    args = parser.parse_args()

    bs = Tune(args.fileName, args.songName, args.artist)
    bars = bs.find_chorus_bars()

    for i in range(len(bars)):
        render(bs.bars[max(0,bars[i][0]-1):bars[i][1]+2], str(i+1)+'chorus.mp3', True)


