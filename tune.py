import echonest.remix.audio as audio
import pyechonest import track

class Tune():
    """
    Class for one song in the playlist, called Tune 
    """
    def __init__(self,path_to_song):
        self.tune = audio.LocalAudioFile(path_to_song)
        self.track = pyechonest.track.track_from_filename(path_to_song)
        self.bpm = getattr(self.track,'tempo')
        self.segments = getattr(self.tune.analysis, 'segments')
        self.beats = getattr(self.tune.analysis, 'beats')