import math
import os
import sys
import dirac
from echonest.remix import audio, modify
from echonest.remix.action import render, Crossfade, Crossmatch
import numpy 
import soundtouch
from pyechonest import config

config.ECHO_NEST_API_KEY = "SKUP2XKX0MRWEOBIE"

playlist1 = ['shakeitoff.mp3','Blank Space.mp3','Everything Has Changed.mp3']

def remix():
        track = audio.LocalAudioFile('Blank Space.mp3')
        bars = track.analysis.bars
        bars = bars[154:188]
        render(bars, 'chorusbs.mp3', True)
        track2 = audio.LocalAudioFile('Red.mp3')
        bar2  = track2.analysis.bars
        bar2 = bar2[18:29]
        start1 = bar2[-1].start - bar2[0].start
        start2 = bars[0].duration
        print start1, start2
        render(bar2, 'chorusred.mp3', True)

        transition = make_crossfade('chorusred.mp3','chorusbs.mp3',start1, start2, 6)

        final = bar2[:-1] + transition + bars[2:]

        render(final, 'output.mp3', True)

def make_crossfade(track1,track2,start1,start2,fade_amt):
    """crossfades two tracks at desired times
        inputs:
            2 tracks(str-path)
            2 times to start(int)
            amount to fade by(int/float)
            what to turn the cross faded song into(str)

        outputs: a short track transition

    """
    song1 = audio.LocalAudioFile(track1)
    song2 = audio.LocalAudioFile(track2)
    crossed_song = Crossfade( (song1, song2), (start1, start2), fade_amt)
    print 1 
    #render([crossed_song], 'cross1.mp3', True)
    return [crossed_song]
# transition = make_crossfade('chorusred.mp3','chorusbs.mp3',21.6, 0.0, 5)
# render(transition, 'transition.mp3', True)
#make_crossfade('Red.mp3','Blank Space.mp3',36.93728,232.88604,25,'cross1.mp3')

# remix()
# def adjust_tempo(input_filename, output_filename):
#     # This takes your input track, sends it to the analyzer, and returns the results.  
#     audiofile = audio.LocalAudioFile(input_filename)

#     tempo = audiofile.analysis.tempo 
#     beats = audiofile.analysis.beats

#     ratio = 0.9

#     audiofile2 = modify.Modify()
#     collect = []
#     for beat in beats:

#         audiofile2.shiftTempo(audiofile[beat], ratio)
#         collect.append(new)

#     out = audio.assemble(collect)
#     out.encode(output_filename)



def adjust_tempo(input_filename, output_filename,ratio):
    # This takes your input track, sends it to the analyzer, and returns the results.  
    audiofile = audio.LocalAudioFile(input_filename)

    # This gets a list of every bar in the track.  
    bars = audiofile.analysis.bars
    # The output array
    collect = []

    # This loop streches each beat by a varying ratio, and then re-assmbles them.
    for bar in bars:
        # Caculate a stretch ratio that repeats every four bars.
        # bar_ratio = (bars.index(bar) % 4) / 2.
        # Get the beats in the bar
        beats = bar.children()
        for beat in beats:
            # Find out where in the bar the beat is.
            beat_index = beat.local_context()[0]
            # Calculate a stretch ratio based on where in the bar the beat is
            # ratio = beat_index / 2.0 + 0.5
            # Note that dirac can't compress by less than 0.5!
            # ratio = ratio + bar_ratio 
            # print bar_ratio
            # print 'a'
            # print ratio
            # if ratio < 0.5
            # Get the raw audio data from the beat and scale it by the ratio
            # dirac only works on raw data, and only takes floating-point ratios
            beat_audio = beat.render()
            scaled_beat = dirac.timeScale(beat_audio.data, ratio)
            # Create a new AudioData object from the scaled data
            ts = audio.AudioData(ndarray=scaled_beat, shape=scaled_beat.shape, 
                            sampleRate=audiofile.sampleRate, numChannels=scaled_beat.shape[1])
            # Append the new data to the output list!
            collect.append(ts)

    # Assemble and write the output data
    out = audio.assemble(collect, numChannels=2)
    out.encode(output_filename)

def balance_tempo(song1,song2):
    audiofile = audio.LocalAudioFile(song1)
    tempo1 = audiofile.analysis.tempo
    print tempo1
    audiofile2 = audio.LocalAudioFile(song2)
    tempo2 = audiofile2.analysis.tempo
    print tempo2
    if tempo1['value'] > tempo2['value']:
        ratio = tempo1['value']/tempo2['value']        
        adjust_tempo(song1,'tempo_'+song1,ratio)
    else:
        ratio = tempo2['value']/tempo1['value']
        adjust_tempo(song2,'tempo_'+song2,ratio)
    print ratio



balance_tempo('Burn.mp3','Love Me Like You Do.mp3')
# adjust_tempo('Blank Space.mp3','tempo_adj_BS.mp3')    
# audiofile = audio.LocalAudioFile('tempo_adj_BS.mp3')
# print audiofile.analysis.tempo

# adjust_tempo('shakeitoff2\.mp3','shakecycle.mp3')

		