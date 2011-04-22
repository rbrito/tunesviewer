#Common functions for tunesviewer
import glib
import re

##
# Given milliseconds, returns time in mm:ss format.
def timeFind(ms):
	try:
		seconds = int(ms)/1000
	except ValueError:
		#print "Invalid number '%s'" % ms
		return ms
	min = str(seconds/60)
	if len(min) == 1:
		min = "0"+min
	sec = str(seconds%60)
	if len(sec) == 1:
		sec = "0"+sec
	return min + ":" + sec

def htmlentitydecode(s):
	if s: # based on http://wiki.python.org/moin/EscapingHtml
		from htmlentitydefs import name2codepoint
		return (re.sub('&(%s);' % '|'.join(name2codepoint), 
				lambda m: unichr(name2codepoint[m.group(1)]), s)).replace("&apos;","'")
	else:
		return ""

def safeFilename(name):
	#Turning string into a valid file name for dos/fat filesystem.
	# see: http://stackoverflow.com/questions/295135/turn-a-string-into-a-valid-filename-in-python
	#http://msdn.microsoft.com/en-us/library/ms810456.aspx
	name = ''.join(c for c in name if c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 $%`-_@{}~!#().")
	if len(name) > 250: # Get the first part of filename, with extension:
		name = name[:240] + typeof(name)
	return name
	

##
# Opens file/url in the system default opener.
def openDefault(filename):
	start("xdg-open",filename)

def markup(text,isheading):
	"""Gives markup for name - for liststore"""
	if isheading:
		return "<u><i>%s</i></u>" % (glib.markup_escape_text(text))
	else:
		return glib.markup_escape_text(text)

def HTmarkup(text,isheading):
	"""Gives html markup for name - for webkit view."""
	if isheading:
		return "<u><i>%s</i></u><br>" % (text)
	else:
		return text+"<br>"

##
# Describes length in kb or mb, given a number of bytes.
def desc(length):
	kb= 1024.0
	mb= 1048576.0
	if (length>=mb):
		return str(round(length/mb,1)) + " MB"
	elif (len>=kb):
		return str(round(length/kb,1)) + " KB"
	else:
		return str(length) + " B"
		

##
# Runs a program in the background.
def start(program, arg):
	import subprocess
	try:
		#Using Popen for security. (os.system(program+something) could have dangerous commands added to end.)
		print program,arg
		# program may be something like program -a -b, so split spaces to args:
		subprocess.Popen(program.split(" ")+[arg])
		print "completed"
	except Exception, e:
		print e
		msg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE,
				"Error starting %s\n%s" % (program,e))
		msg.run()
		msg.destroy()

##
# Gets the file type of the url. (.mp3,.pdf, etc)
def typeof(filename):
	out = filename[filename.rfind("."):]
	if (out.find("?")>-1):
		out = out[:out.find("?")]
	if (out.find("%")>-1):
		out = out[:out.find("%")]
	return out