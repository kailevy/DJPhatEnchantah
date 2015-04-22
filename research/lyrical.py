"""
Trying out lyrics stuff
"""

import sys
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

def split_words(string):
    """Splits words by blanks spaces"""
    return string.split()

# outdated attempt at this: http://bpchesney.org/?p=715
# def autocorr(arr):
#     n = len(arr)
#     Rxy = [0.0] * n
#     for i in xrange(n):
#         for j in xrange(i, min(i+n,n)):
#             Rxy[i] += int(arr[j]==arr[j-i])
#         for j in xrange(i):
#             Rxy[i] += int(arr[j]==arr[j-i+n])
#         Rxy[i] /= float(n)
#     return Rxy

# def most_similar(arr):
#     m = max(arr[1:])
#     return (m,[i for i, j in enumerate(arr[1:]) if j == m])

def find_repeats(arr):
    """finds exact repeated paragraphs"""
    repeated = []
    for i in arr:
        if arr.count(i) > 1 and i not in repeated: repeated.append(i)
    return repeated


def get_timestamp(timed_chorus, worded_chorus):
    first_line = worded_chorus[0]
    last_line = worded_chorus[-1]
    print 'first:' + first_line
    print 'last:' + last_line
    i=0
    for line in timed_chorus:
        if line['line'] == first_line:
            print line
            start_time = line['milliseconds']
            break
    for line in timed_chorus:
        i += 1
        if line['line'] == last_line:
            end_time = line['milliseconds']
            if end_time > start_time: break

    assert end_time > start_time

    start_time = float(start_time)/1000.0

    end_time = float(end_time)/1000.0

    return start_time, end_time

def find_times(bars, start_time, end_time, fade):
    start_candidates = []
    end_candidates = []
    for i, bar in enumerate(bars):
        score = abs(bar.start - fade - start_time)
        start_candidates.append((score, i))
        score = abs(bar.start - fade - end_time)
        end_candidates.append((score,i))

    return min(start_candidates), min(end_candidates)

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
    chorus_freqs = []
    chorus = []
    for par in split_pars:
        par_freqs.append(get_words(par))

    for i in range(len(split_pars)):
        for j in range(i+1,len(split_pars)):
            if compute_similarity(par_freqs[j],par_freqs[i]) > 0.9 and split_pars[i] not in chorus:
                chorus.append(split_pars[i])

    for par in chorus:
        chorus_freqs.append(get_words(par))

    for i in range(len(chorus)):
        for j in range(i+1,len(chorus)):
            if compute_similarity(chorus_freqs[j],chorus_freqs[i]) > 0.85:
                chorus.pop(i)

    return chorus

if __name__ == '__main__':
    artist = 'Taylor Swift'
    song = 'Blank Space'
    timestamped_chorus = harvest_lrc(get_json(make_lrc_url(artist, song)))
    b = split_pars(harvest_lyrics(get_json(make_lrc_url(artist, song))))

    a = find_chorus_freq(b)

    chorus = '\n'.join(a)

    print chorus

    chorus_split = chorus.split('\r\n')

    start, end = get_timestamp(timestamped_chorus, chorus_split)

    print start, end

    track = audio.LocalAudioFile(song+'.mp3')
    a = pyechonest.track.track_from_filename(song+'.mp3')
    fade = getattr(track.analysis, 'end_of_fade_in')
    bars = getattr(track.analysis, 'bars')

    index_start, index_end = find_times(bars, start, end, fade)

    print index_start[1], index_end[1]

    render(bars[index_start[1]:index_end[1]+5], 'chorus.mp3', True)