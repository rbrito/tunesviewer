#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
A 'find' window class for Tunesviewer.

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

import gtk

import constants

class FindBox:
	"""
	Advanced search based on

	http://deimos.apple.com/rsrc/doc/AppleEducation-iTunesUUsersGuide/UsingiTunesUSearch/chapter_10_section_4.html
	"""
	def __init__(self, mainwin):
		self.mainwin = mainwin
		self.window = gtk.Dialog("Advanced Search",
					 None,
					 gtk.DIALOG_DESTROY_WITH_PARENT,
					 (gtk.STOCK_FIND, 1, gtk.STOCK_CLOSE, 0))
		self.window.set_default_response(1)
		self.window.set_icon(self.window.render_icon(gtk.STOCK_FIND,
							     gtk.ICON_SIZE_BUTTON))
		self.window.connect("response", self.response) # Ok/Cancel
		#set up a table: http://www.pygtk.org/pygtk2tutorial/sec-PackingUsingTables.html
		vbox = self.window.get_content_area()
		self.notebook = gtk.Notebook()

		itable = gtk.Table(3, 2, True)
		#attaching obj,left,right,top,bottom.
		itable.attach(gtk.Label("Title"), 0, 1, 0, 1)
		self.title = gtk.Entry()
		self.title.set_activates_default(True)
		itable.attach(self.title, 1, 2, 0, 1)

		itable.attach(gtk.Label("Academic Institution"), 0, 1, 1, 2)
		self.institution = gtk.Entry()
		self.institution.set_activates_default(True)
		itable.attach(self.institution, 1, 2, 1, 2)

		itable.attach(gtk.Label("Description"), 0, 1, 2, 3)
		self.description = gtk.Entry()
		self.description.set_activates_default(True)
		itable.attach(self.description, 1, 2, 2, 3)

		# -- podcast tab --
		podtable = gtk.Table(3, 2, True)
		podtable.attach(gtk.Label("Title"), 0, 1, 0, 1)
		self.podtitle = gtk.Entry()
		self.podtitle.set_activates_default(True)
		podtable.attach(self.podtitle, 1, 2, 0, 1)

		podtable.attach(gtk.Label("Author"), 0, 1, 1, 2)
		self.podauthor = gtk.Entry()
		self.podauthor.set_activates_default(True)
		podtable.attach(self.podauthor, 1, 2, 1, 2)

		podtable.attach(gtk.Label("Description"), 0, 1, 2, 3)
		self.poddesc = gtk.Entry()
		self.poddesc.set_activates_default(True)
		podtable.attach(self.poddesc, 1, 2, 2, 3)

		self.notebook.append_page(itable, gtk.Label("iTunesU"))
		self.notebook.append_page(podtable, gtk.Label("Podcasts"))
		vbox.pack_start(self.notebook)
		#vbox.pack_start(table)
		self.window.connect("delete_event", self.delete_event)

	##
	# Cancels close, only hides window.
	def delete_event(self, widget, event, data=None):
		self.window.hide()
		return True # Hide, don't close.

	def response(self, obj, value):
		logging.debug(str(obj) + str(value))
		if value == 0:
			self.window.hide()
		elif value == 1:
			#Use the search
			if self.notebook.get_current_page() == 0:
				self.mainwin.gotoURL(constants.SEARCH_URL1 % (self.title.get_text(), self.description.get_text(), self.institution.get_text()), True)
			else:
				self.mainwin.gotoURL(constants.SEARCH_URL2 % (self.podtitle.get_text(), self.podauthor.get_text(), self.poddesc.get_text()), True)
