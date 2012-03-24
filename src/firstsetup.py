#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Initial setup - sets up browser integration.

This is also called by configbox.

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

import os
import logging

import gtk

from constants import TV_PATH

def run():
	"""Runs the basic configuration procedure."""
	# This should be run as user, not root.
	if os.geteuid() == 0:
		logging.error("Run this as user, not root.")
		return


	msg = gtk.MessageDialog(None,
				gtk.DIALOG_MODAL,
				gtk.MESSAGE_QUESTION,
				gtk.BUTTONS_YES_NO,
				"Do you want to enable opening "
				"university media directly from the "
				"web browser?")
	r = msg.run()
	msg.destroy()

	if r == gtk.RESPONSE_YES:
		logging.info("Setting default...")
		setdefault()


def setdefault():
	"""Sets this as the default protocol opener."""
	try:
		file(TV_PATH)
	except IOError:
		msg = gtk.MessageDialog(None,
					gtk.DIALOG_MODAL,
					gtk.MESSAGE_ERROR,
					gtk.BUTTONS_CLOSE,
					"The link %s does not exist." % TV_PATH)
		msg.run()
		msg.destroy()
		return

	tv_args = "%s"
	tv_call = "%s %s" % (TV_PATH, tv_args)

	# Try setting the protocol defaults:
	err = 0
	err += setdefaultprotocol("itms", tv_call)
	err += setdefaultprotocol("itmss", tv_call)
	err += setdefaultprotocol("itpc", tv_call)

	if err:
		message_type = gtk.MESSAGE_ERROR
		message = "Unable to set defaults."
	else:
		message_type = gtk.MESSAGE_INFO
		message = ("Default set. Now you should be able to "
			   "open iTunesU from a web browser.")


	msg = gtk.MessageDialog(None,
				gtk.DIALOG_MODAL,
				message_type,
				gtk.BUTTONS_CLOSE,
				message)
	msg.run()
	msg.destroy()


def setdefaultprotocol(protocol, program):
	"""
	Tries to set program as default protocol handler, returns True if
	there was an error.
	"""

	base_cmd = "gconftool-2 -s /desktop/gnome/url-handlers/"

	err = os.system(base_cmd + protocol +
			"/enabled --type Boolean true")
	err += os.system(base_cmd + protocol + "/command '" +
			 program + "' --type String")

	return err >= 1

if __name__ == '__main__':
	run()
