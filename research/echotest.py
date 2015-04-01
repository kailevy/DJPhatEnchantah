from pyechonest import config
from pyechonest import song
config.ECHO_NEST_API_KEY="UYVJNO5B993SMMV33"
ss_results = song.search(artist='the national', title='slow show', buckets=['id:7digital-US', 'tracks'], limit=True)
slow_show = ss_results[0]
ss_tracks = slow_show.get_tracks('7digital-US')
print ss_tracks[0].get('preview_url')
print ss_tracks[0]
