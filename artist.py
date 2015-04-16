from pyechonest import *

#p = playlist.static(type='artist-radio', artist=['ida maria', 'florence + the machine'])
s = song.search(title ='everything at once', results = 1)
music = s[0]
print type(music.title)
