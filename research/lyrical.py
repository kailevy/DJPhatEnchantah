"""
Trying out lyrics stuff
"""

import sys, getopt, argparse
import urllib2
import os
import json
from pyechonest import song
import math

import echonest.remix.audio as audio
from echonest.remix.action import render, Crossfade
from pyechonest import config
from binheap import BinHeap
from copy import deepcopy
import pyechonest
import numpy as np
import matplotlib.pyplot as plt

config.ECHO_NEST_API_KEY = "SKUP2XKX0MRWEOBIE"

DISPLAY_KEY = os.environ.get('LYRICFIND_DISPLAY_API_KEY')
LRC_KEY = os.environ.get('LYRICFIND_LRC_API_KEY')
SEARCH_KEY = os.environ.get('LYRICFIND_SEARCH_API_KEY')
METADATA_KEY = os.environ.get('LYRICFIND_METADATA_API_KEY')

LYRICFIND_DISPLAY_URL = 'http://test.lyricfind.com/api_service/lyric.do'

def get_json(url):
    """
    Given a properly formatted URL for a JSON web API request, return
    a Python JSON object containing the response to that request.
    """
    f = urllib2.urlopen(url)
    response_text = f.read()
    response_data = json.loads(response_text)
    return response_data    

def make_lrc_url(artist,title):
    """
    Given an artist and title, formats the lyricfind api url for json format
    """
    url = 'http://test.lyricfind.com/api_service/lyric.do?apikey=%s&lrckey=%s&territory=US&reqtype=default\
&trackid=artistname:%s,trackname:%s&format=lrc&output=json' %(DISPLAY_KEY,LRC_KEY,
        artist.replace(' ','+'),title.replace(' ','+'))

    return url

def harvest_lyrics(json):
    """Gets lyrics from json"""
    return json['track']['lyrics']

def harvest_lrc(json):
    """Gets lrc from json"""
    return json['track']['lrc']

def split_pars(string):
    """Splits lyrics by double linebreak"""
    return string.split('\r\n\r\n')

def get_lines(paragraph):
    return paragraph.split('\r\n')

def split_words(string):
    """Splits words by blanks spaces"""
    return string.split()

def find_repeats(arr):
    """finds exact repeated paragraphs"""
    repeated = []
    for i in arr:
        if arr.count(i) > 1 and i not in repeated: repeated.append(i)
    return repeated


def get_timestamp(timed_chorus, worded_chorus):
    """Retieves the time stamp of the first chorus in the song. Could modify
    this to be the second (since that is usually the more colorful one."""
    first_line = worded_chorus[0]
    last_line = worded_chorus[-1]
    # print len(worded_chorus)
    # print '\n'
    #for i in timed_chorus: print i['line']
    candidates = []

    # Saves all the possible start points of the chorus and their indices:
    for i, line in enumerate(timed_chorus):
        if line['line'].strip() == first_line.strip() or \
            first_line.strip() in line['line'].strip() or \
            line['line'].strip() in first_line.strip():
            candidates.append([i, line])

        if line['line'].strip() == last_line.strip() or \
            last_line.strip() in line['line'].strip() or \
            line['line'].strip() in last_line.strip():
            final_line, final_index = line, i

    # For each start, compute number of lines it takes to get to the last line
    # of the chorus. Take the start that is the minimum distance
    for j in candidates:
        distance = final_index - j[0]
        if distance > 3:
            j += [final_index - j[0]]
        else:
            j += [1000]

    # for i in candidates: print i, '\n'

    # Right start of chorus is the one with minimum distance to 
    right_one = min(candidates, key=lambda x: x[2])

    start_time = right_one[1]['milliseconds']
    end_time = final_line['milliseconds']

    print start_time, end_time

    # returns times in seconds
    return float(start_time)/1000.0, float(end_time)/1000.0

def find_times(bars, start_time, end_time, fade):
    """Finds and returns the indices of the bars that start and end of the 
    chorus. This function works by, keeping track of the scores of the current
    and previous bars. If the current score becomes higher, it means that the
    loop has passed over the right bar, and we save the previous bar's index"""

    startScore, endScore = 10000000, 10000000
    first_bar = 0
    last_bar = len(bars)-1
    found_first = False

    for i, bar in enumerate(bars):
        if not found_first:
            prevStartScore, startScore = startScore, abs(bar.start - fade - start_time)
            if startScore > prevStartScore: 
                first_bar = i-1
                found_first = True

        prevEndScore, endScore = endScore, abs(bar.start - fade - end_time)
        if endScore > prevEndScore: 
            last_bar = i-1
            break

    return first_bar, last_bar

def get_words(s):
    """ Returns a dictionary of word counts, given a string"""
    d = {}
    s = s.lower()
    for word in s.split():
        d[word] = d.get(word,0) + 1
    return d

def compute_similarity(d1,d2):
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

def find_chorus_freq(split_pars):
    """finds chorus based off of similar word frequencies"""
    par_freqs = []
    chorus = []
    for par in split_pars:
        par_freqs.append(get_words(par))
    print split_pars
    for i in range(len(split_pars)):
        for j in range(i+1,len(split_pars)):
            if compute_similarity(par_freqs[j],par_freqs[i]) > 0.7 and split_pars[i]:
                chorus.append(split_pars[i])

    return chorus

def filter_chorus(chorus):
    filter_chorus = [i for i in chorus]
    chorus_freqs = []

    for par in chorus:
        chorus_freqs.append(get_words(par))

    if len(chorus) > 1:
        for i in range(len(chorus)):
            for j in range(i+1,len(chorus)):
                if compute_similarity(chorus_freqs[j],chorus_freqs[i]) > 0.8:
                    filter_chorus[j] = ''

    return [i for i in filter_chorus if i]

def get_word_map(lyrics, choruses):
    voiced = []
    voiced_chorus = []
    section = []
    chorus_lines = []
    for i in choruses:
        chorus_lines += get_lines(i)
    chor = []
    i = 0
    verses_choruses = [] # (start, end)

    while i < len(lyrics):
        if lyrics[i]['line']:
            if lyrics[i]['line'].strip() in chorus_lines:
                chor.append(lyrics[i]['milliseconds'])
            else:
                section.append(lyrics[i]['milliseconds'])
        else:
            if int(lyrics[i+1]['milliseconds']) - int(lyrics[i-1]['milliseconds']) < 7:
                pass
            else:
                if section:
                    verses_choruses.append((int(section[0]), int(section[-1]), 'verse'))
                    # for j in range(int(section[0]), int(section[-1])+1):
                    #     if round(j/1000.0, 1) not in voiced:
                    #         voiced.append(round(j/1000.0, 1))
                    section = []
                if chor:
                    verses_choruses.append((int(chor[0]), int(chor[-1]), 'chorus'))
                    # for k in range(int(chor[0]), int(chor[-1])+1):
                    #     if round(k/1000.0, 1) not in voiced_chorus:
                    #         voiced_chorus.append(round(k/1000.0, 1))
                    chor = []
        i += 1

    # plots verses and choruses
    
    """for time in voiced:
        plt.plot([time], [1], 'ro')
    for time in voiced_chorus:
        plt.plot([time], [2], 'ro')

    for verse in verses_choruses:
        if verse[2] == 'verse':
            plt.plot([verse[0]/1000.0], [3], 'bo')
            plt.plot([verse[1]/1000.0], [3], 'bo')
        if verse[2] == 'chorus':
            plt.plot([verse[0]/1000.0], [4], 'bo')
            plt.plot([verse[1]/1000.0], [4], 'bo')

    plt.show()"""    
    return verses_choruses    


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('artist', help='Enter the artist(s) of your song')
    parser.add_argument('songName', help='Enter the name of your song')
    parser.add_argument('fileName', help='Enter the file name of your song')
    args = parser.parse_args()
    
    artist = args.artist
    song = args.songName
    try:
        timestamped_chorus = harvest_lrc(get_json(make_lrc_url(artist, song)))
    except KeyError:
        print '\nYour song could not be processed.\n'
        sys.exit()

    # Remove blank spaces between paragraphs from the timestamped chorus
    #timestamped_chorus = [i for i in timestamped_chorus if i['line']]

    # Retrieve the lyrics as a list of separate paragraphs
    b = split_pars(harvest_lyrics(get_json(make_lrc_url(artist, song))))

    # Retrieve the chorus as a list of lines and process it
    a = find_chorus_freq(b)
    c = filter_chorus(a)
    print a 

    print get_word_map(timestamped_chorus, a)

    """chorus = '\n'.join(a)
    chorus_split = chorus.split('\r\n')

    # Get the start and end times of the song based on the chorus given
    start, end = get_timestamp(timestamped_chorus, chorus_split)

    # Locate the track and get necessary attributes
    track = audio.LocalAudioFile(args.fileName)
    fade = getattr(track.analysis, 'end_of_fade_in')
    bars = getattr(track.analysis, 'bars')

    # Get starting and ending indices of the bars for the chorus
    index_start, index_end = find_times(bars, start, end, fade)


    # Outputs the chorus and a little more
    render(bars[index_start-1:index_end+2], 'chorus.mp3', True)"""
