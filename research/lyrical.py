"""
Trying out lyrics stuff
"""

import sys
import urllib2
import os
import json
import math
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
    """takes the lyrics part of the json"""
    return json['track']['lyrics']

def harvest_lrc(json):
    """takes the lrc part of the json"""
    return json['track']['lrc']

def split_pars(string):
    """splits paragraphs by double line break"""
    return string.split('\r\n\r\n')

def split_words(string):
    """splits words by blank space"""
    return string.split()

# attempted to imitate method described here: http://bpchesney.org/?p=715
# since abandoned
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
    """Finds exactly repeated paragraphs"""
    repeated = []
    for i in a:
        if a.count(i) > 1 and i not in repeated: repeated.append(i)
    return repeated

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
    a = split_pars(harvest_lyrics(get_json(make_lrc_url('cut copy','We are explorers'))))

    print find_chorus_freq(a)
    # print find_repeats(a)
    # print most_similar(autocorr(parse_lyrics(harvest_lyrics(get_json(make_lrc_url('Michael Jackson','Beat it'))))))
    # print harvest_lyrics(get_json(make_lrc_url('The Killers','Mr. Brightside')))