"""
Trying out lyrics stuff
http://test.lyricfind.com/api_service/lyric.do?apikey=87c94e1a862dcd6ccb9fe4f4c567
5007&lrckey=338e17628d2c45501a8ef6168a3dc115&territory=US&reqtype=default&trackid=amg:2033&format=lrc
"""

import sys
import urllib2
import os
import json
from pyechonest import song

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
    return json['track']['lyrics']

def harvest_lrc(json):
    return json['track']['lrc']

def split_pars(string):
    return string.split('\r\n\r\n')

def split_words(string):
    return string.split()

def autocorr(arr):
    n = len(arr)
    Rxy = [0.0] * n
    for i in xrange(n):
        for j in xrange(i, min(i+n,n)):
            Rxy[i] += int(arr[j]==arr[j-i])
        for j in xrange(i):
            Rxy[i] += int(arr[j]==arr[j-i+n])
        Rxy[i] /= float(n)
    return Rxy

def most_similar(arr):
    m = max(arr[1:])
    return (m,[i for i, j in enumerate(arr[1:]) if j == m])

def find_repeats(arr):
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

if __name__ == '__main__':
    artist = 'Ellie Goulding'
    song = 'Love Me Like You Do'
    timestamped_chorus = harvest_lrc(get_json(make_lrc_url(artist, song)))
    a = find_repeats(split_pars(harvest_lyrics(get_json(make_lrc_url(artist, song)))))
    chorus = ''

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







