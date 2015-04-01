# Beat tracking example
import librosa

# 1. Get the file path to the included audio example
filename = librosa.util.example_audio_file()

# 2. Load the audio as a waveform `y`
#    Store the sampling rate as `sr`
y, sr = librosa.load(filename)

# 3. Run the default beat tracker, using a hop length of 64 frames
#    (64 frames at sr=22.050KHz ~= 2.9ms)
hop_length = 64
tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, hop_length=hop_length)

print 'Estimated tempo: %0.2f beats per minute' % tempo

# 4. Convert the frame indices of beat events into timestamps
beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=hop_length)

print 'Saving output to beat_times.csv'
librosa.output.times_csv('beat_times.csv', beat_times)