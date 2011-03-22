#!/usr/bin/env python
#Initial setup - set up browser.
#This needs to be run as user, not root.

import gtk, os

class Run:
	def __init__(self):
		os.system("whoami")
		msg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO,
				"Do you want to enable opening university media directly from the web browser?")
		r = msg.run()
		if r == gtk.RESPONSE_YES:
			print "Setting default..."
			msg.destroy()
			self.setdefault(None)
		else:
			msg.destroy()
		return

	# code from main program file:

	##
	# Sets this as the default protocol opener.
	def setdefault(self,obj):
		try:
			file("/usr/bin/tunesviewer")
		except IOError:
			msg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE,
				"The link /usr/bin/tunesviewer does not exist.")
			msg.run()
			msg.destroy()
			return
		# Try setting the protocol defaults:
		err = 0
		err += self.setdefaultprotocol("itms","/usr/bin/tunesviewer %s")
		err += self.setdefaultprotocol("itmss","/usr/bin/tunesviewer %s")
		err += self.setdefaultprotocol("itpc","/usr/bin/tunesviewer %s")
		if (err):
			msg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE,
				"Unable to set defaults.")
			msg.run()
			msg.destroy()
		else:
			msg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_INFO, gtk.BUTTONS_CLOSE,
				"Default set. Now you should be able to open itunesU from a web browser.")
			msg.run()
			msg.destroy()

	##
	# Tries to set program as default protocol handler, returns True if there was an error.
	def setdefaultprotocol(self,protocol,program):
		err = os.system("gconftool-2 -s /desktop/gnome/url-handlers/"+protocol+"/enabled --type Boolean true")
		err2 = os.system("gconftool-2 -s /desktop/gnome/url-handlers/"+protocol+"/command '"+program+"' --type String")
		return (err or err2)

if __name__ == '__main__': Run()
