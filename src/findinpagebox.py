#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
A find-in-page dialog for Tunesviewer, with callback to main window.

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

import gobject
import gtk

class FindInPageBox(gtk.Dialog):

	__gsignals__ = {'find': (gobject.SIGNAL_RUN_FIRST,
				 gobject.TYPE_NONE,
				 (gobject.TYPE_STRING,))}

	def __init__(self):
		gtk.Dialog.__init__(self, "Find in Current Page", None,
				    gtk.DIALOG_DESTROY_WITH_PARENT,
				    (gtk.STOCK_FIND, 1, gtk.STOCK_CLOSE, 0))
		self.currentFound = -1
		self.set_size_request(250, -1) # change width
		self.set_default_response(1)
		self.set_icon(self.render_icon(gtk.STOCK_FIND, gtk.ICON_SIZE_BUTTON))
		self.connect("response", self.response) # Ok/Cancel
		vbox = self.get_content_area()
		vbox.pack_start(gtk.Label("Find Text:"))
		self.findText = gtk.Entry()
		self.findText.set_activates_default(True)
		vbox.pack_start(self.findText)
		self.connect("delete_event", self.delete_event)

	def delete_event(self, widget, event, data=None):
		self.hide()
		return True # Hide, don't close.

	def response(self, obj, value):
		if value == 0:
			self.hide()
		else:
			text = self.findText.get_text().lower()
			self.emit('find', text)
