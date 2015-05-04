from echonest.remix.action import render, Crossfade, Crossmatch
from pyechonest import config

config.ECHO_NEST_API_KEY = "SKUP2XKX0MRWEOBIE"


def make_crossmatch(song1, song2, bars1, bars2, fade_amt):
    crossed_song = Crossmatch( (song1, song2), (to_tuples(bars1), to_tuples(bars2)))
    return [crossed_song]


def to_tuples(alist):
        return [(t.start, t.duration) for t in alist]