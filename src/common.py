"""
Common functions for Tunesviewer.
"""
import os.path
import re
import urllib2

import glib
import gtk

def time_convert(ms):
	"""
	Given time in milliseconds, returns it as a string:

	* In mm:ss format if the time is less than 1 hour.
	* In the hh:mm:ss for if the time is at least 1 hour.

	This is done for consistency with the rest of the iTunes Store.
	"""
	try:
		seconds = int(ms)/1000
	except (ValueError, TypeError):
		return ms

	hour = seconds / 3600
	seconds = seconds % 3600

	mins = seconds / 60
	secs = seconds % 60

	if (hour):
		return "%d:%02d:%02d" % (hour, mins, secs)

	return "%d:%02d" % (mins, secs)


def htmlentitydecode(s):
	if s:
		# This unescape function is an internal function of
		# HTMLParser but let's use it, as it does a better job than
		# what we have so far.
		#
		# See: hg.python.org/cpython/file/2.7/Lib/HTMLParser.py
		import HTMLParser
		return HTMLParser.HTMLParser().unescape(s).replace("&apos;", "'")
	else:
		return ""


def safeFilename(name, dos):
	"""
	Given a string called name, return a 'filtered' version of name
	(with special characters removed) that is suitable to be used as a
	file name for a DOS/FAT filesystem, when DOS=true.

	This function doesn't take care of corner cases like reserved names
	(NUL, CON etc.), nor it takes care of filenames that can be empty.

	The resulting filename is truncated to be at most 255 characters
	long.

	For further information, see:
	http://stackoverflow.com/questions/295135/turn-a-string-into-a-valid-filename-in-python
	http://msdn.microsoft.com/en-us/library/ms810456.aspx
	"""
	if dos:
		unsafe_fat_chars = r'[^-a-zA-Z0-9 $%`_@{}~!#().]'

		name = os.path.basename(name)
		name = re.sub(unsafe_fat_chars, '', name)
		(root, ext) = os.path.splitext(name)

	if len(name) > 255 and dos:
		name = root[:255-len(ext)] + ext
	elif len(name) == 0:
		name = "(unknown)"
	return name


def openDefault(filename):
	"""
	Opens file/url in the system default opener.
	"""
	start("xdg-open", filename)


def markup(text, isheading):
	"""
	Gives markup for name - for liststore.
	"""
	if isheading:
		return "<u><i>%s</i></u>" % (glib.markup_escape_text(text))
	else:
		return glib.markup_escape_text(text)


def HTmarkup(text, isheading):
	"""
	Gives html markup for name - for webkit view.
	"""
	if isheading:
		return "<u><i>%s</i></u><br>" % (text)
	else:
		return text + "<br>"


def desc(length):
	"""
	Describes length in kb or mb, given a number of bytes.
	"""
	kb = 1024.0
	mb = 1048576.0
	if (length >= mb):
		return str(round(length/mb, 1)) + " MB"
	elif (len >= kb):
		return str(round(length/kb, 1)) + " KB"
	else:
		return str(length) + " B"


def start(program, arg):
	"""
	Runs a program in the background.
	"""
	import subprocess
	try:
		# We use Popen for security, as a call to
		# os.system(program + something) can have dangerous commands
		# added to end.
		print(program, arg)
		# program may be something like program -a -b, so split spaces to args:
		subprocess.Popen(program.split(" ") + [arg])
		print("completed")
	except Exception as e:
		print(e)
		msg = gtk.MessageDialog(None, gtk.DIALOG_MODAL,
					gtk.MESSAGE_ERROR,
					gtk.BUTTONS_CLOSE,
					"Error starting %s\n%s" % (program, e))
		msg.run()
		msg.destroy()


def super_unquote(s):
	# Some silly strings seem to be URL-quoted multiple times!
	old_s = ''
	new_s = s

	while old_s != new_s:
		old_s = new_s
		new_s = urllib2.unquote(old_s)

	return new_s


def type_of(name):
	return super_unquote(os.path.splitext(name)[1])
