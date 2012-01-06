#!/usr/bin/env python
#Initial setup - sets up browser integration.
#This is also called by configbox.

import gtk, os

class FirstSetup:
	def run(self):
		if os.popen("whoami").read() != "root\n":
			# This should be run as user, not root.
			msg = gtk.MessageDialog(None,
						gtk.DIALOG_MODAL,
						gtk.MESSAGE_QUESTION,
						gtk.BUTTONS_YES_NO,
					"Do you want to enable opening university media directly from the web browser?")
			r = msg.run()
			if r == gtk.RESPONSE_YES:
				print("Setting default...")
				self.setdefault(None)
			msg.destroy()
			return
		else:
			print("Run this as user, not root.")

	# code from main program file:

	def setdefault(self,obj):
		""" Sets this as the default protocol opener. """
		try:
			file("/usr/bin/tunesviewer")
		except IOError:
			msg = gtk.MessageDialog(None,
						gtk.DIALOG_MODAL,
						gtk.MESSAGE_ERROR,
						gtk.BUTTONS_CLOSE,
				"The link /usr/bin/tunesviewer does not exist.")
			msg.run()
			msg.destroy()
			return
		# Try setting the protocol defaults:
		err = 0
		err += self.setdefaultprotocol("itms", "/usr/bin/tunesviewer %s")
		err += self.setdefaultprotocol("itmss", "/usr/bin/tunesviewer %s")
		err += self.setdefaultprotocol("itpc"," /usr/bin/tunesviewer %s")
		if (err):
			msg = gtk.MessageDialog(None,
						gtk.DIALOG_MODAL,
						gtk.MESSAGE_ERROR,
						gtk.BUTTONS_CLOSE,
				"Unable to set defaults.")
			msg.run()
			msg.destroy()
		else:
			msg = gtk.MessageDialog(None,
						gtk.DIALOG_MODAL,
						gtk.MESSAGE_INFO,
						gtk.BUTTONS_CLOSE,
				"Default set. Now you should be able to open iTunesU from a web browser.")
			msg.run()
			msg.destroy()

	def setdefaultprotocol(self, protocol, program):
		""" Tries to set program as default protocol handler, returns True if there was an error. """
		err = os.system("gconftool-2 -s /desktop/gnome/url-handlers/" + protocol + "/enabled --type Boolean true")
		err2 = os.system("gconftool-2 -s /desktop/gnome/url-handlers/" + protocol + "/command '" + program + "' --type String")
		return (err or err2)

if __name__ == '__main__':
	FirstSetup().run()
