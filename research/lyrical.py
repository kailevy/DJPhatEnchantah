"""
Trying out lyrics stuff
http://test.lyricfind.com/api_service/lyric.do?apikey=87c94e1a862dcd6ccb9fe4f4c5675007&lrckey=338e17628d2c45501a8ef6168a3dc115&territory=US&reqtype=default&trackid=amg:2033&format=lrc
"""

import sys
import urllib2
import os
import json
from pyechonest import song

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
    for i in a:
        if a.count(i) > 1 and i not in repeated: repeated.append(i)
    return repeated


if __name__ == '__main__':
    a = split_pars(harvest_lyrics(get_json(make_lrc_url('Red Hot Chili Peppers','Otherside'))))

    print find_repeats(a)
    # print most_similar(autocorr(parse_lyrics(harvest_lyrics(get_json(make_lrc_url('Michael Jackson','Beat it'))))))
    # print harvest_lyrics(get_json(make_lrc_url('Half Moon Run','Full Circle')))