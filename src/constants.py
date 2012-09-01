#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module for holding constants (and some variables with "fixed" values) used
all over the program.

 Copyright (C) 2009 - 2012 Luke Bryan
               2011 - 2012 Rogério Theodoro de Brito
               and other contributors.

 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.
"""

import os.path

import glib

# Path of the program (bad assumption)
TV_PATH = "/usr/bin/tunesviewer"
TV_VERSION = "1.4.99.0" #also needs changing in debian conf file somewhere

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
USER_AGENT = 'iTunes/10.6.3.25'
DEFAULT_OPENER = "vlc --http-user-agent=%s" % (USER_AGENT, )

# URLs
HOME_URL = "http://itunes.apple.com/WebObjects/MZStore.woa/wa/viewGenre?id=40000000"

SEARCH_U = "http://ax.search.itunes.apple.com/WebObjects/MZSearch.woa/wa/search?submit=media&restrict=true&term=%s&media=iTunesU"
SEARCH_P = "http://ax.search.itunes.apple.com/WebObjects/MZSearch.woa/wa/search?submit=media&term=%s&media=podcast"
SEARCH_URL1 = "http://phobos.apple.com/WebObjects/MZSearch.woa/wa/advancedSearch?media=iTunesU&searchButton=submit&allTitle=%s&descriptionTerm=%s&institutionTerm=%s"
SEARCH_URL2 = "http://ax.search.itunes.apple.com/WebObjects/MZSearch.woa/wa/advancedSearch?media=podcast&titleTerm=%s&authorTerm=%s&descriptionTerm=%s&genreIndex=&languageTerm="

#Project Urls
HELP_URL = "http://tunesviewer.sourceforge.net/help/"
BUG_URL = "https://github.com/rbrito/tunesviewer/issues/new"
