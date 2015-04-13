import echonest.remix.audio as audio
from echonest.remix.action import render
from copy import deepcopy
from pyechonest import config
import math
import random

config.ECHO_NEST_API_KEY = "SKUP2XKX0MRWEOBIE"

"""def compute_score(listOne, listTwo, streak=0, start=0):
    pass

def find_chorus(path_to_song):
    track = audio.LocalAudioFile(path_to_song)

    segments = getattr(track.analysis, 'segments')
    tmp_segments = deepcopy(segments)
    tmp_segments = tmp_segments[1:] + tmp_segments[0:1]

    match = False
    start = 1
    score = 100000000

    for i in range(len(segments)):
        a = compute_score(segments, tmp_segments)
        if a < score:
            score = (a, i) #save score and offset index
        tmp_segments = tmp_segments[1:] + tmp_segments[0:1]

    print getattr(track.analysis, 'tempo')"""

def match_by_beats(song1, song2):
    first_song = audio.LocalAudioFile(song1)
    second_song = audio.LocalAudioFile(song2)

    beats1 = getattr(first_song.analysis, 'beats')
    beats2 = getattr(second_song.analysis, 'beats')

    possible_places = []

    start = 0
    while start < len(beats1):
        for i in range(len(beats2)):
            score = (abs(beats1[start].duration**2 - beats2[i].duration**2))**0.5
            if score < 0.38: possible_places.append((score, start, i))
        start += 1

    random_choice = min(possible_places)

    new_song = beats1[:random_choice[1]+1] + beats2[random_choice[2]:]

    render(new_song, 'beatmatching1.mp3', True)


match_by_beats('Love Me Like You Do.mp3', 'Burn.mp3')

