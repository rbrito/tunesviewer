#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 Item details window for Tunesviewer
 
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

import logging
from threading import Thread

import gtk

from common import *


class ItemDetails:
	def __init__(self, mainwin, selection):
		if selection is None:
			logging.debug("No selection.")
		else:
			self.mainwin = mainwin
			self.selection = selection
			self.window = gtk.Dialog()
			self.window.set_title("Item Information: %s" % selection[1])
			self.window.set_size_request(300, 300)
			self.sw = gtk.ScrolledWindow()
			self.sw.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
			self.viewer = gtk.TextView()
			self.viewer.set_wrap_mode(gtk.WRAP_WORD)
			self.viewer.set_editable(False)
			self.window.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
			self.window.connect("response", self.leave)
			mainhbox = gtk.HBox()
			self.sw.add(self.viewer)
			mainhbox.pack_start(self.sw, True, True, 0)
			self.window.get_content_area().pack_start(mainhbox, True, True, 0)
			self.updateText(self.selection, "")
			self.window.show_all()
			logging.debug("starting item thread")
			#Start thread:
			t = Thread(target=self.update, args=())
			t.start()

	def updateText(self, selection, filesize):
		if selection:
			self.window.set_icon(selection[0])
			self.text = htmlentitydecode(selection[1]) + "\n" + selection[2] + "\n"
			if selection[3]:
				self.text += "Length: " + selection[3] + "\n"
			if selection[4]:
				self.text += "This is a " + selection[4] + " file.\n"
			if filesize:
				self.text += "File size: " + filesize + "\n"
			if selection[5]:
				self.text += "Comment:\n" + selection[5] + "\n"
			if selection[6]:
				self.text += "Released:\n" + selection[6] + "\n"
			if selection[7]:
				self.text += "Modified:\n" + selection[7] + "\n"
			if selection[8]:
				self.text += "This links to:\n" + selection[8] + "\n\n"
			if selection[9]:
				self.text += "This file is at:\n" +selection[9] + "\n\n"
			if selection[10]:
				self.text += "Price:\n" + selection[10] + "\n\n"
			if selection[11]:
				self.text += "id:" + selection[11]
			gtk.gdk.threads_enter()
			self.viewer.get_buffer().set_text(self.text)
			gtk.gdk.threads_leave()


	def update(self):
		try:
			op = self.mainwin.opener.open(self.selection[9])
			self.updateText(self.selection, desc(int(op.info()['Content-Length'])))
			op.close()
		except Exception as e:
			logging.debug(e)


	def leave(self, obj, obj2):
		self.window.destroy()
