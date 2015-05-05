"""To populate the database"""
from database import SongDatabase

db = SongDatabase("song_test","tune_pickle")
db.reset_db()
db.populate_db()
db.print_db()