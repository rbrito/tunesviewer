"""
Module for holding constants (and some variables with "fixed" values) used
all over the program.
"""

import os.path

import glib

# Path of the program (bad assumption)
TV_PATH = "/usr/bin/tunesviewer"
TV_VERSION = "1.5" #also needs changing in debian conf file somewhere

# Directory under which we write configuration files
USER_PREFS_DIR = glib.get_user_config_dir()
PREFS_DIR = os.path.join(USER_PREFS_DIR, "tunesviewer")
PREFS_FILE = os.path.join(PREFS_DIR, "tunesviewer.conf")

# Directory under which we write state data
USER_DATA_DIR = glib.get_user_data_dir()
DATA_DIR = os.path.join(USER_DATA_DIR, "tunesviewer")
DATA_FILE = os.path.join(DATA_DIR, "state") # Holds current downloads, in case of crash, resumes.
DATA_SOCKET = os.path.join(DATA_DIR, "tunesviewerLOCK") # Holds socket, so second app calls first instance with url.

# Directory under which we write downloaded files
DOWNLOADS_DIR = os.path.expanduser("~")

# User agent and connection programs
USER_AGENT = 'iTunes/10.5.3'
DEFAULT_OPENER = "/usr/bin/vlc --http-user-agent=%s --http-caching=10000" % (USER_AGENT, )

# URLs
HOME_URL = "http://itunes.apple.com/WebObjects/MZStore.woa/wa/viewGrouping?id=27753"

SEARCH_U = "http://ax.search.itunes.apple.com/WebObjects/MZSearch.woa/wa/search?submit=media&restrict=true&term=%s&media=cobalt"
SEARCH_P = "http://ax.search.itunes.apple.com/WebObjects/MZSearch.woa/wa/search?submit=media&term=%s&media=podcast"
SEARCH_URL1 = "http://phobos.apple.com/WebObjects/MZSearch.woa/wa/advancedSearch?media=iTunesU&searchButton=submit&allTitle=%s&descriptionTerm=%s&institutionTerm=%s"
SEARCH_URL2 = "http://ax.search.itunes.apple.com/WebObjects/MZSearch.woa/wa/advancedSearch?media=podcast&titleTerm=%s&authorTerm=%s&descriptionTerm=%s&genreIndex=&languageTerm="

#Project Urls
HELP_URL = "http://sourceforge.net/apps/trac/tunesviewer/wiki/help"
BUG_URL = "http://sourceforge.net/tracker/?func=add&group_id=305696&atid=1288143"
