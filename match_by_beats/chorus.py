import echonest.remix.audio as audio
from echonest.remix.action import render, Crossfade
from pyechonest import config
from binheap import BinHeap
from copy import deepcopy

config.ECHO_NEST_API_KEY = "SKUP2XKX0MRWEOBIE"

def compare_segments(a, b):
    """Look at two segments a, b. Compare pitches, timbre, duration and
    loudness_max. Return a score"""
    pitch_score, timbre_score, duration_score, loudness_score = 0, 0, 0, 0

    #calculates score for timbre and pitches first
    for i in range(12): #12 values of segment.timbre and segment.pitches
        #timbre_score += abs(a.timbre[i] - b.timbre[i])
        pitch_score = abs(a.pitches[i] - b.pitches[i])/(12**0.5)

    #duration_score = abs(a.duration - b.duration)
    #loudness_score = abs(a.loudness_max - b.loudness_max)

    return pitch_score# + timbre_score + loudness_score + duration_score


def comb_segment(segments, start=0, other_start=1, prev_match=False, chain=0):
    """Recursively goes through and compares the first beat to all the other
    segments in the song. Returns the longest chain of similar segments."""
    THRESHOLD = 0.2
    #if segments match
    if start > len(segments) or other_start > len(segments):
        return 0, 0, []
    else:
        score = compare_segments(segments[start], segments[other_start])
        #print score
        if score <= THRESHOLD:
            start += 1
            other_start += 1
            chain += 1
            if other_start >= len(segments)-1:
                return chain+1, start, segments[start+1:]
            else:
                return comb_segment(segments, start, other_start, True, chain)
        #if segments don't match but a chain has been going 
        elif score > THRESHOLD and prev_match == True:
            return chain, start, segments[start+1:] #returns how long the chain is, end of the chain, and remaining segments
        #if segments don't match and no chain:
        else:
            #if have not finished comparing start note to all other notes
            if other_start < len(segments)-1:
                return comb_segment(segments, start, other_start+1)
            elif other_start == len(segments)-1:
                return 0, start+1, segments[start+1:]


def find_chorus(path_to_song):
    track = audio.LocalAudioFile(path_to_song)
    track_segments = getattr(track.analysis, 'segments')
    tmp_segments = deepcopy(track_segments)
    chains = []
    ends_of_chains = []
    start = 0
    other_start = 1

    while tmp_segments:
        chain, start, tmp_segments = comb_segment(tmp_segments, start, other_start)
        other_start = start + 1
        chains.append(chain)
        ends_of_chains.append(start)

    #print chains

    max_chain = max(chains)
    index = chains.index(max_chain)
    end_index = ends_of_chains[index]
    start_index = end_index - max_chain
    print max_chain, start_index, end_index


    render(track_segments[start_index:end_index+1], 'findchorus.mp3', True)



find_chorus('turndownforwhat.mp3')
