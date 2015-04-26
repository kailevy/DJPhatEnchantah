import echonest.remix.audio as audio
from echonest.remix.action import render
from binheap import BinHeap

"""IDEA: Find the chorus based on largest change in timbre between
any two segments in a song"""

def find_delta_segment(a, b):
    """Looks at two segments a, b. Compares timbre and loudness"""
    timbre_score, loudness_score = 0, 0

    #calculates score for timbre first
    for i in range(12): #12 values of segment.timbre
        timbre_score += abs(a.timbre[i] - b.timbre[i])

    #returns negative score because find_split uses a minimum binary heap
    #so min value is actually largest difference
    return -timbre_score


def find_split(segments):
    """Finds an appropriate pair of segments that differ enough in timbre but
    also don't lie two near the beginning or the end."""

    #initiate minimum binary heap instance
    deltas = BinHeap()

    #compares delta for each pair of segments (1,2), (2,3), etc... and save the values in deltas
    for i in range(len(segments)-2):
        deltas.insert((find_delta_segment(segments[i], segments[i+1]), i))

    #take the largest difference
    a = deltas.delMin()
    #makes sure that a is not too near the beginning (before 1/6 of song) or
    #the end (after 5/6 of song)
    while a[1] < len(segments)//4 or a[1] > (3*len(segments))//4:
        a = deltas.delMin()

    return a


def find_chorus_delta(path_to_song):
    """Attempts to find the chorus (or a suitable position in the song to cut
    into/play from) for a given song."""
    #loads data
    track = audio.LocalAudioFile(path_to_song)
    track_segments = getattr(track.analysis, 'segments')

    #a is where the track will split
    a = find_split(track_segments)

    #calculate loudness either side of the split to decide which is chorus
    split_index = a[1]
    left_loud, right_loud = 0, 0

    for i in range(1,31):
        left_loud += track_segments[split_index-i].loudness_max
        right_loud += track_segments[split_index+i].loudness_max

    print left_loud, right_loud

    #if chorus lies on the left, find another split within that segment so
    #output does not start from beginning of song
    if left_loud > right_loud:
        print 'left' 
        print split_index
        left_segments = track_segments[:split_index]
        b = find_split(left_segments)
        print b
        render(track_segments[b[1]:split_index], 'chorusof'+path_to_song, True)

    #if chorus lies on the right of split, simply play from split_index
    else: 
        print 'right'
        render(track_segments[split_index:], 'chorusof'+path_to_song, True)

find_chorus_delta('03 We Are Explorers.mp3')