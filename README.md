# DJPhatEnchantah
**Hannah Fowler, Kai Levy, Hieu Nguyen, Wilson Tang**

**Software Design, Spring '15**

# Dependencies
This project uses licenses for both the EchoNest API and the LyricFind API. If you get keys for these, it is recommended that you put them into your .bashrc file to be exported.

Other dependencies include:
* id3reader (file included on this repository, but originally from [here](http://nedbatchelder.com/code/modules/id3reader.html))
* MySQLdb
* EchoNest Remix
* pyechonest
* urllib2, urllib
* en-ffmpeg
* pydub
* any other dependencies of these dependencies

#Usage
1. Install dependencies and acquire API keys
2. Create mySQL database with the same arguments as seen in database.py and make a user with permissions. Our version makes "djdb" and user "phatuser" with access by "phat623"
3. Run populate.py, being sure to have the same folder names for your music and your pickled files. Our version uses "song_test" for the songs and "tune_pickle" for the pickle files.
4. Run playlist.py, specifying the song folder, the extension for the base song, the number of songs to be mixed, and the name of the output file. You can optionally add -eff for vocal additions
5. Enjoy your mix! 