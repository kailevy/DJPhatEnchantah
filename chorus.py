import echonest.remix.audio as audio
from echonest.remix.action import render, Crossfade
from copy import deepcopy
from pyechonest import config
import math
import random
from binheap import BinHeap

config.ECHO_NEST_API_KEY = "SKUP2XKX0MRWEOBIE"

def choose_beat(first_song, second_song, possible_places):
    """Takes a list of tuples of indices in the form (index of end of song1, 
    index of start of song2). Then compare each end of song1 and start of 
    song2 to how far away they are from end of a section and start of a section
    respectively for each song. Returns the closest match"""
    beats1 = getattr(first_song.analysis, 'beats')
    beats2 = getattr(second_song.analysis, 'beats')

    sections1 = getattr(first_song.analysis, 'sections')
    sections2 = getattr(second_song.analysis, 'sections')

    ret = []

    for pair in possible_places:
        end = beats1[pair[1]].end
        start = beats2[pair[2]].start
        score1 = 1000
        score2 = 1000
        a = min([abs(section.end-end) for section in sections1])
        b = min([abs(section.start-start) for section in sections2])
        
        pair += (a+b,)
        ret.append(pair)

    return min(ret, key=lambda x: x[3])

def match_by_beats(song1, song2):
    first_song = audio.LocalAudioFile(song1)
    second_song = audio.LocalAudioFile(song2)

    beats1 = getattr(first_song.analysis, 'beats')
    beats2 = getattr(second_song.analysis, 'beats')

    places = BinHeap()
    possible_places = []

    start = 0
    while start < len(beats1):
        for i in range(len(beats2)):
            score = (abs(beats1[start].duration**2 - beats2[i].duration**2))**0.5
            places.insert((score, start, i))
        start += 1

    for i in range(10):
        possible_places.append(places.delMin())

    choice = choose_beat(first_song, second_song, possible_places)
    new_end = choice[1]
    new_start = choice[2]

    FADE_TIME = 3

    """out = Crossfade((first_song, second_song), (new_end, new_start), FADE_TIME)
            
                a = out.render()
                render(getattr(a.analysis, 'beats'), 'crossfadetest.mp3', True)"""

    new_end = choice[1]
    new_start = choice[2]

    added = 0.001

    for i in range(10):
        beats1[new_end-(10-i)].duration += i*added
        beats2[new_start+i].duration += i*added

    new_song = beats1[:new_end+1] + beats2[new_start:]

    render(new_song, 'beatmatching1.mp3', True)


match_by_beats('Blank Space.mp3', 'Burn.mp3')

