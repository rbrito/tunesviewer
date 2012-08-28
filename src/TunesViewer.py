#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
TunesViewer
A small, easy-to-use tool to access iTunesU and podcast media.

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

# Import standard Python modules
import cookielib
import gzip
import logging
import os
import socket
import subprocess
import time
import urllib
import urllib2

from StringIO import StringIO
from threading import Thread

# Import third-party modules (GTK and siblings for GUI)
import glib
import gobject
import gtk
import pango

gobject.threads_init()

from lxml import etree

# Import local project modules
from configbox import ConfigBox
from findinpagebox import FindInPageBox
from downloadbox import DownloadBox
from findbox import FindBox
from itemdetails import ItemDetails
from webkitview import WebKitView
from Parser import Parser
from SingleWindowSocket import SingleWindowSocket
from common import *
from constants import TV_VERSION, SEARCH_U, SEARCH_P, USER_AGENT, HELP_URL, BUG_URL

class TunesViewer:
	source = ""  # full html/xml source
	url = ""  # page url
	podcast = ""  # podcast url
	pageType = ""  # text/xml or text/html
	downloading = False  # when true, don't download again, freezing
			     # prog. (Enforces having ONE gotoURL)
	downloadError = ""
	infoboxes = []
	redirectPages = []

	# Lists can be used as stacks: just use list.append(...) and list.pop()
	# Stacks for back and forward buttons:
	backStack = []
	forwardStack = []

	# Initializes the main window
	def __init__(self, dname=None):

		self.downloadbox = DownloadBox(self) # Only one downloadbox is constructed
		self.findbox = FindBox(self)
		self.findInPage = FindInPageBox()
		self.findInPage.connect('find', self.find_in_page_cb)
		# Create a new window, initialize all widgets:
		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.window.set_title("TunesViewer")
		self.window.set_size_request(350, 350) #minimum
		self.window.resize(750, 750) #default
		self.window.connect("delete_event", self.delete_event)
		# set add drag-drop, based on:
		# http://stackoverflow.com/questions/1219863/python-gtk-drag-and-drop-get-url
		self.window.drag_dest_set(0, [], 0)
		self.window.connect('drag_motion', self.motion_cb)
		self.window.connect('drag_drop', self.drop_cb)
		self.window.connect('drag_data_received', self.got_data_cb)

		try:
			icon_app_path = '/usr/share/icons/hicolor/scalable/apps/tunesview.svg'
			pixbuf = gtk.gdk.pixbuf_new_from_file(icon_app_path)
			self.window.set_icon(pixbuf)
		except:
			logging.warn("Couldn't load window icon.")

		# will hold icon, title, artist, time, type, comment, releasedate, datemodified, gotourl, previewurl, price, itemid.
		self.liststore = gtk.ListStore(gtk.gdk.Pixbuf, str, str,
					       str, str, str, str, str, str,
					       str, str, str)

		#Liststore goes in a TreeView inside a Scrolledwindow:
		self.treeview = gtk.TreeView(model=self.liststore)
		self.treeview.set_enable_search(True)
		self.scrolledwindow = gtk.ScrolledWindow()
		self.scrolledwindow.set_policy(gtk.POLICY_AUTOMATIC,
					       gtk.POLICY_AUTOMATIC)
		self.scrolledwindow.add(self.treeview)

		cell = gtk.CellRendererText()
		# Set the cell-renderer to ellipsize ... at end.
		cell.set_property("ellipsize", pango.ELLIPSIZE_END)
		# Set single-paragraph-mode, no huge multiline display rows.
		cell.set_property("single-paragraph-mode", True)

		col = gtk.TreeViewColumn(" ")
		# col.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
		pb = gtk.CellRendererPixbuf()
		col.pack_start(pb)
		col.add_attribute(pb, 'pixbuf', 0)
		self.treeview.append_column(col)

		# Now each column is created and added:
		col = gtk.TreeViewColumn("Name")
		col.pack_start(cell)
		col.add_attribute(cell, 'markup', 1) # because markup, not text, is required in tooltip.
		col.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
		col.set_fixed_width(200)
		col.set_expand(True)
		col.set_resizable(True)
		col.set_reorderable(True)
		# col.set_max_width(100)
		self.treeview.set_search_column(1)
		col.set_sort_column_id(1)
		# col.set_property('resizable', 1)
		self.treeview.append_column(col)
		self.treeview.set_tooltip_column(1) # needs markup, not text

		col = gtk.TreeViewColumn("Author")
		col.pack_start(cell)
		col.add_attribute(cell, 'text', 2)
		col.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
		#col.set_expand(True)
		col.set_fixed_width(150)
		col.set_resizable(True)
		col.set_reorderable(True)
		self.treeview.set_search_column(2)
		col.set_sort_column_id(2)
		self.treeview.append_column(col)

		time_cell = gtk.CellRendererText()
		col = gtk.TreeViewColumn("Time")
		col.pack_start(time_cell)
		time_cell.set_property('xalign', 1.0)
		col.add_attribute(time_cell, 'text', 3)
		col.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
		col.set_resizable(True)
		col.set_reorderable(True)
		self.treeview.set_search_column(3)
		col.set_sort_column_id(3)
		self.treeview.append_column(col)

		col = gtk.TreeViewColumn("Type")
		col.pack_start(cell)
		col.add_attribute(cell, 'text', 4)
		col.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
		col.set_resizable(True)
		col.set_reorderable(True)
		self.treeview.set_search_column(4)
		col.set_sort_column_id(4)
		self.treeview.append_column(col)

		col = gtk.TreeViewColumn("Comment")
		col.pack_start(cell)
		col.add_attribute(cell, 'text', 5)
		col.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
		col.set_expand(True)
		col.set_min_width(100)
		col.set_resizable(True)
		col.set_reorderable(True)
		self.treeview.set_search_column(5)
		col.set_sort_column_id(5)
		self.treeview.append_column(col)
		self.treeview.set_search_column(0)

		col = gtk.TreeViewColumn("Release Date")
		col.pack_start(cell)
		col.add_attribute(cell, 'text', 6)
		col.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
		col.set_resizable(True)
		col.set_reorderable(True)
		self.treeview.set_search_column(6)
		col.set_sort_column_id(6)
		self.treeview.append_column(col)
		self.treeview.set_search_column(0)

		col = gtk.TreeViewColumn("Modified Date")
		col.pack_start(cell)
		col.add_attribute(cell, 'text', 7)
		col.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
		col.set_resizable(True)
		col.set_reorderable(True)
		self.treeview.set_search_column(7)
		col.set_sort_column_id(7)
		self.treeview.append_column(col)
		self.treeview.set_search_column(1)

		self.treeview.connect("row-activated", self.rowSelected)
		self.treeview.get_selection().set_select_function(self.treesel,
								  data=None)

		# Make the locationbar-searchbar:
		locationbox = gtk.HBox()
		self.modecombo = gtk.combo_box_new_text()
		self.modecombo.append_text("Url:")
		self.modecombo.append_text("iTunesU Search:")
		self.modecombo.append_text("Podcast Search:")
		self.modecombo.set_active(1)
		self.modecombo.connect("changed", self.combomodechanged)
		locationbox.pack_start(self.modecombo, False, False, 0)
		self.locationentry = gtk.Entry()
		self.locationentry.connect("activate", self.gobutton)
		locationbox.pack_start(self.locationentry, True, True, 0)
		gobutton = gtk.Button(label="Go", stock=gtk.STOCK_OK)
		# set GO label
		# http://www.harshj.com/2007/11/17/setting-a-custom-label-for-a-button-with-stock-icon-in-pygtk/
		try:
			gobutton.get_children()[0].get_children()[0].get_children()[1].set_label("G_O")
		except:
			pass

		gobutton.connect("clicked", self.gobutton)
		locationbox.pack_start(gobutton, False, False, 0)
		prefheight = self.locationentry.size_request()[1]
		#Default button is very tall, try to make buttons the same height as the text box:
		gobutton.set_size_request(-1, prefheight)

		# Now make menus: http://zetcode.com/tutorials/pygtktutorial/menus/
		agr = gtk.AccelGroup()
		self.window.add_accel_group(agr)
		menubox = gtk.HBox()
		mb = gtk.MenuBar()
		menubox.pack_start(mb, 1, 1, 0)
		self.throbber = gtk.Image()

		throbber_path = '/usr/share/tunesviewer/Throbber.gif'
		try:
			self.throbber.set_from_animation(gtk.gdk.PixbufAnimation(throbber_path))
			menubox.pack_start(self.throbber, expand=False)
		except glib.GError as e:
			logging.error('Could not set the throbber: %s' % str(e))


		### Top level 'File' menu
		filemenu = gtk.Menu()
		filem = gtk.MenuItem("_File")
		filem.set_submenu(filemenu)

		## Advanced search
		aSearch = gtk.ImageMenuItem(gtk.STOCK_FIND)
		aSearch.set_label("Advanced _Search...")
		aSearch.connect("activate", self.advancedSearch)
		key, mod = gtk.accelerator_parse("<Ctrl>K")
		aSearch.add_accelerator("activate", agr, key, mod,
					gtk.ACCEL_VISIBLE)
		filemenu.append(aSearch)

		## Search on current page
		pSearch = gtk.ImageMenuItem(gtk.STOCK_FIND)
		pSearch.set_label("Find on Current Page...")
		pSearch.connect("activate", self.searchCurrent)
		key, mod = gtk.accelerator_parse("<Ctrl>F")
		pSearch.add_accelerator("activate", agr, key, mod,
					gtk.ACCEL_VISIBLE)
		filemenu.append(pSearch)

		filemenu.append(gtk.SeparatorMenuItem())

		## Exit application
		exit = gtk.ImageMenuItem(gtk.STOCK_QUIT)
		exit.set_label("E_xit")
		exit.connect("activate", self.exitclicked)
		key, mod = gtk.accelerator_parse("<Ctrl>Q")
		exit.add_accelerator("activate", agr, key, mod,
				     gtk.ACCEL_VISIBLE)
		filemenu.append(exit)

		### Edit menu
		editmenu = gtk.Menu()
		editm = gtk.MenuItem("_Edit")
		editm.set_submenu(editmenu)

		## Copy podcast URL
		self.copym = gtk.ImageMenuItem(gtk.STOCK_COPY)
		self.copym.set_label("_Copy Normal Podcast Url")
		self.copym.connect("activate", self.copyrss)
		key, mod = gtk.accelerator_parse("<Ctrl><Shift>C")
		self.copym.add_accelerator("activate", agr, key, mod,
					   gtk.ACCEL_VISIBLE)
		editmenu.append(self.copym)

		## Paste URL
		pastem = gtk.ImageMenuItem(gtk.STOCK_PASTE)
		pastem.set_label("Paste and _Goto Url")
		pastem.connect("activate", self.pastego)
		key, mod = gtk.accelerator_parse("<Ctrl><Shift>V")
		pastem.add_accelerator("activate", agr, key, mod,
				       gtk.ACCEL_VISIBLE)
		editmenu.append(pastem)

		editmenu.append(gtk.SeparatorMenuItem())

		## Preferences
		prefs = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)
		prefs.connect("activate", self.openprefs)
		editmenu.append(prefs)

		### View menu
		viewmenu = gtk.Menu()
		viewm = gtk.MenuItem("_View")
		viewm.set_submenu(viewmenu)

		## Request content in HTML mode
		self.htmlmode = gtk.CheckMenuItem("Request _HTML Mode")
		self.htmlmode.set_active(True)
		viewmenu.append(self.htmlmode)

		self.mobilemode = gtk.CheckMenuItem("Mobile Mode")
		viewmenu.append(self.mobilemode)

		viewmenu.append(gtk.SeparatorMenuItem())

		## Show downloads
		viewdownloads = gtk.ImageMenuItem(gtk.STOCK_GO_DOWN)
		viewdownloads.set_label("Show _Downloads")
		key, mod = gtk.accelerator_parse("<Ctrl>j")
		viewdownloads.add_accelerator("activate", agr, key, mod,
					      gtk.ACCEL_VISIBLE)
		viewdownloads.connect("activate", self.viewDownloads)
		viewmenu.append(viewdownloads)

		## Open downloads directory
		viewdir = gtk.ImageMenuItem(gtk.STOCK_DIRECTORY)
		viewdir.set_label("Downloads Directory")
		viewdir.connect("activate", self.openDownloadDir)
		viewmenu.append(viewdir)
		viewmenu.append(gtk.SeparatorMenuItem())

		## Zoom in
		ziItem = gtk.ImageMenuItem(gtk.STOCK_ZOOM_IN)
		key, mod = gtk.accelerator_parse("<Ctrl>plus")
		ziItem.add_accelerator("activate", agr, key, mod,
				       gtk.ACCEL_VISIBLE)
		ziItem.connect("activate", self.webkitZI)
		viewmenu.append(ziItem)

		## Zoom out
		zoItem = gtk.ImageMenuItem(gtk.STOCK_ZOOM_OUT)
		key, mod = gtk.accelerator_parse("<Ctrl>minus")
		zoItem.add_accelerator("activate", agr, key, mod,
				       gtk.ACCEL_VISIBLE)
		zoItem.connect("activate", self.webkitZO)
		viewmenu.append(zoItem)

		## Reset zoom
		znItem = gtk.ImageMenuItem(gtk.STOCK_ZOOM_100)
		key, mod = gtk.accelerator_parse("<Ctrl>0")
		znItem.add_accelerator("activate", agr, key, mod,
				       gtk.ACCEL_VISIBLE)
		znItem.connect("activate", self.webkitZN)
		viewmenu.append(znItem)

		viewmenu.append(gtk.SeparatorMenuItem())

		## View page source
		viewsource = gtk.MenuItem("Page _Source")
		key, mod = gtk.accelerator_parse("<Ctrl>U")
		viewsource.add_accelerator("activate", agr, key, mod,
					   gtk.ACCEL_VISIBLE)
		viewsource.connect("activate", self.viewsource)
		viewmenu.append(viewsource)

		## View cookies
		viewcookie = gtk.MenuItem("_Cookies")
		viewcookie.connect("activate", self.viewCookie)
		viewmenu.append(viewcookie)

		## View information of selected item
		viewprop = gtk.ImageMenuItem(gtk.STOCK_INFO)
		viewprop.set_label("Selection _Info")
		key, mod = gtk.accelerator_parse("<Ctrl>I")
		viewprop.add_accelerator("activate", agr, key, mod,
					 gtk.ACCEL_VISIBLE)
		viewmenu.append(viewprop)
		viewprop.connect("activate", self.viewprop)

		self.locShortcut = gtk.MenuItem("Current _URL")
		key, mod = gtk.accelerator_parse("<Ctrl>L")
		self.locShortcut.add_accelerator("activate", agr, key, mod,
						 gtk.ACCEL_VISIBLE)
		viewmenu.append(self.locShortcut)
		self.locShortcut.hide()
		self.locShortcut.connect("activate", self.locationBar)

		### Go menu
		gomenu = gtk.Menu()
		gom = gtk.MenuItem("_Go")
		gom.set_submenu(gomenu)

		## iTunes U subdirectory
		self.itunesuDir = gtk.Menu()
		itunesu = gtk.MenuItem("iTunes_U")
		itunesu.set_submenu(self.itunesuDir)
		#self.itunesuDir.append(gtk.MenuItem("directory here"))
		gomenu.append(itunesu)

		## Podcast subdirectory
		self.podcastDir = gtk.Menu()
		podcasts = gtk.MenuItem("_Podcasts")
		podcasts.set_submenu(self.podcastDir)
		#self.podcastDir.append(gtk.MenuItem("directory here"))
		gomenu.append(podcasts)

		## Go back
		back = gtk.ImageMenuItem(gtk.STOCK_GO_BACK)
		key, mod = gtk.accelerator_parse("<Alt>Left")
		back.add_accelerator("activate", agr, key, mod,
				     gtk.ACCEL_VISIBLE)
		back.connect("activate", self.goBack)
		gomenu.append(back)

		## Go forward
		forward = gtk.ImageMenuItem(gtk.STOCK_GO_FORWARD)
		key, mod = gtk.accelerator_parse("<Alt>Right")
		forward.add_accelerator("activate", agr, key, mod,
					gtk.ACCEL_VISIBLE)
		forward.connect("activate", self.goForward)
		gomenu.append(forward)

		## Refresh page
		refresh = gtk.ImageMenuItem(gtk.STOCK_REFRESH)
		key, mod = gtk.accelerator_parse("F5")
		refresh.add_accelerator("activate", agr, key, mod,
					gtk.ACCEL_VISIBLE)
		refresh.connect("activate", self.refresh)
		gomenu.append(refresh)

		## Stop loading
		stop = gtk.ImageMenuItem(gtk.STOCK_STOP)
		key, mod = gtk.accelerator_parse("Escape")
		stop.add_accelerator("activate", agr, key, mod,
				     gtk.ACCEL_VISIBLE)
		stop.connect("activate", self.stop)
		gomenu.append(stop)

		## Go to the initial page
		homeb = gtk.ImageMenuItem(gtk.STOCK_HOME)
		homeb.connect("activate", self.goHome)
		gomenu.append(homeb)

		### Actions menu
		itemmenu = gtk.Menu()
		itemm = gtk.MenuItem("_Actions")
		itemm.set_submenu(itemmenu)

		## Go to link
		follow = gtk.ImageMenuItem(gtk.STOCK_JUMP_TO)
		follow.connect("activate", self.followlink)
		follow.set_label("_Goto Link")
		key, mod = gtk.accelerator_parse("<Ctrl>G")
		follow.add_accelerator("activate", agr, key, mod,
				       gtk.ACCEL_VISIBLE)
		itemmenu.append(follow)

		## Play/View file
		playview = gtk.ImageMenuItem(gtk.STOCK_MEDIA_PLAY)
		playview.set_label("_Play/View File")
		playview.connect("activate", self.playview)
		key, mod = gtk.accelerator_parse("<Ctrl>P")
		playview.add_accelerator("activate", agr, key, mod,
					 gtk.ACCEL_VISIBLE)
		itemmenu.append(playview)

		## Download file
		download = gtk.ImageMenuItem(gtk.STOCK_SAVE)
		download.set_label("_Download File")
		download.connect("activate", self.download)
		key, mod = gtk.accelerator_parse("<Ctrl>D")
		download.add_accelerator("activate", agr, key, mod,
					 gtk.ACCEL_VISIBLE)
		itemmenu.append(download)

		## Add Page to podcast manager
		self.addpodmenu = gtk.ImageMenuItem(gtk.STOCK_ADD)
		self.addpodmenu.set_label("_Add Page to Podcast Manager")
		self.addpodmenu.connect("activate", self.addPod)
		itemmenu.append(self.addpodmenu)

		### Contextual (right-click) menu
		self.rcmenu = gtk.Menu()
		self.rcgoto = gtk.ImageMenuItem(gtk.STOCK_JUMP_TO)
		self.rcgoto.connect("activate", self.followlink)
		self.rcgoto.set_label("_Goto")
		self.rcgoto.show()

		self.rccopy = gtk.ImageMenuItem(gtk.STOCK_COPY)
		self.rccopy.connect("activate", self.copyRowLink)
		self.rccopy.set_label("_Copy Link")
		self.rccopy.show()

		self.rcplay = gtk.ImageMenuItem(gtk.STOCK_MEDIA_PLAY)
		self.rcplay.connect("activate", self.playview)
		self.rcplay.set_label("_Play/View")
		self.rcplay.show()

		self.rcdownload = gtk.ImageMenuItem(gtk.STOCK_SAVE)
		self.rcdownload.connect("activate", self.download)
		self.rcdownload.set_label("_Download")
		self.rcdownload.show()

		rcinfo = gtk.ImageMenuItem(gtk.STOCK_INFO)
		rcinfo.connect("activate", self.viewprop)
		rcinfo.set_label("Item _Info")
		rcinfo.show()

		self.rcmenu.append(rcinfo)
		self.rcmenu.append(self.rcgoto)
		self.rcmenu.append(self.rccopy)
		self.rcmenu.append(self.rcplay)
		self.rcmenu.append(self.rcdownload)
		self.treeview.connect("button_press_event", self.treeclick)

		### Help menu
		helpmenu = gtk.Menu()
		helpm = gtk.MenuItem("_Help")
		helpm.set_submenu(helpmenu)

		## Help
		helpitem = gtk.ImageMenuItem(gtk.STOCK_HELP)
		helpitem.connect("activate", self.showHelp)
		helpmenu.append(helpitem)

		## Check for updates
		helpupdate = gtk.MenuItem("Check for _Update...")
		helpupdate.connect("activate", self.progUpdate)
		helpmenu.append(helpupdate)

		## Report a bug
		helpreport = gtk.MenuItem("Report a Bug...")
		helpreport.connect("activate", self.bugReport)
		helpmenu.append(helpreport)

		## About the program
		helpabout = gtk.MenuItem("About")
		helpabout.connect("activate", self.showAbout)
		helpmenu.append(helpabout)

		#Set up the main menu:
		mb.append(filem)
		mb.append(editm)
		mb.append(viewm)
		mb.append(gom)
		mb.append(itemm)
		mb.append(helpm)

		#Location buttons: (University > section > title)
		self.locationhbox = gtk.HBox()
		#self.locationhbox.set_size_request(prefheight,-1)
		self.locationhbox.pack_start(gtk.Label(" Media files on this page: "),
					     False, False, 0)
		#This will hold references to the buttons in this box:
		#self.locationbuttons = [] not needed
		self.notebook = gtk.Notebook()
		self.notebook.set_property("enable-popup", True)
		self.notebook.connect_after("switch-page", self.tabChange) #important to connect-after! Normal connect will cause display problems and sometimes segfault.
		self.notebook.set_scrollable(True)
		self.notebookbox = gtk.HBox()
		self.notebookbox.pack_start(self.notebook, True, True, 0)

		bottom = gtk.VBox()
		bottom.pack_start(self.locationhbox, False, False, 2)
		bottom.pack_start(self.notebookbox, False, False, 2)
		bottom.pack_start(self.scrolledwindow, True, True, 2)

		# adjustable panel with description box above listing:
		vpaned = gtk.VPaned()
		vpaned.set_position(500)
		sw = gtk.ScrolledWindow()
		sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		self.descView = WebKitView(self)

		sw.add(self.descView)
		vpaned.pack1(sw, resize=True)
		vpaned.pack2(bottom, resize=False)

		self.toolbar = gtk.Toolbar()
		self.tbBack = gtk.ToolButton(gtk.STOCK_GO_BACK)
		self.tbBack.connect("clicked", self.goBack)
		self.tbBack.set_tooltip_text("Back")
		self.toolbar.insert(self.tbBack, -1)
		self.tbForward = gtk.ToolButton(gtk.STOCK_GO_FORWARD)
		self.tbForward.connect("clicked", self.goForward)
		self.tbForward.set_tooltip_text("Forward")
		self.toolbar.insert(self.tbForward, -1)
		tbRefresh = gtk.ToolButton(gtk.STOCK_REFRESH)
		tbRefresh.connect("clicked", self.refresh)
		tbRefresh.set_tooltip_text("Refresh Page")
		self.toolbar.insert(tbRefresh, -1)
		self.tbStop = gtk.ToolButton(gtk.STOCK_STOP)
		self.tbStop.connect("clicked", self.stop)
		self.tbStop.set_tooltip_text("Stop")
		self.toolbar.insert(self.tbStop, -1)

		self.toolbar.insert(gtk.SeparatorToolItem(), -1)

		opendl = gtk.ToolButton(gtk.STOCK_DIRECTORY)
		opendl.set_tooltip_text("Open Downloads Directory")
		opendl.connect("clicked", self.openDownloadDir)
		self.toolbar.insert(opendl, -1)
		self.toolbar.insert(gtk.SeparatorToolItem(), -1)

		self.tbInfo = gtk.ToolButton(gtk.STOCK_INFO)
		self.tbInfo.connect("clicked", self.viewprop)
		self.tbInfo.set_tooltip_text("View Selection Information")
		self.toolbar.insert(self.tbInfo, -1)
		self.tbGoto = gtk.ToolButton(gtk.STOCK_JUMP_TO)
		self.tbGoto.connect("clicked", self.followlink)
		self.tbGoto.set_tooltip_text("Goto Link")
		self.toolbar.insert(self.tbGoto, -1)
		self.tbPlay = gtk.ToolButton(gtk.STOCK_MEDIA_PLAY)
		self.tbPlay.connect("clicked", self.playview)
		self.tbPlay.set_tooltip_text("Play/View File")
		self.toolbar.insert(self.tbPlay, -1)
		self.tbDownload = gtk.ToolButton(gtk.STOCK_SAVE)
		self.tbDownload.connect("clicked", self.download)
		self.tbDownload.set_tooltip_text("Download File")
		self.toolbar.insert(self.tbDownload, -1)
		self.toolbar.insert(gtk.SeparatorToolItem(), -1)

		self.tbCopy = gtk.ToolButton(gtk.STOCK_COPY)
		self.tbCopy.connect("clicked", self.copyrss)
		self.tbCopy.set_tooltip_text("Copy Normal Podcast Url")
		self.toolbar.insert(self.tbCopy, -1)
		self.tbAddPod = gtk.ToolButton(gtk.STOCK_ADD)
		self.tbAddPod.set_tooltip_text("Add to Podcast Manager")
		self.tbAddPod.connect("clicked", self.addPod)
		self.toolbar.insert(self.tbAddPod, -1)
		self.toolbar.insert(gtk.SeparatorToolItem(), -1)
		tbFind = gtk.ToolButton(gtk.STOCK_FIND)

		tbZO = gtk.ToolButton(gtk.STOCK_ZOOM_OUT)
		tbZO.connect("clicked", self.webkitZO)
		self.toolbar.insert(tbZO, -1)
		tbZI = gtk.ToolButton(gtk.STOCK_ZOOM_IN)
		tbZI.connect("clicked", self.webkitZI)
		self.toolbar.insert(tbZI, -1)
		self.toolbar.insert(gtk.SeparatorToolItem(), -1)

		tbFind.set_tooltip_text("Advanced Search")
		tbFind.connect("clicked", self.advancedSearch)
		self.toolbar.insert(tbFind, -1)
		spacer = gtk.SeparatorToolItem()
		spacer.set_draw(0)
		spacer.set_expand(1)
		self.toolbar.insert(spacer, -1)
		self.tbAuth = gtk.ToolButton(gtk.STOCK_DIALOG_AUTHENTICATION)
		self.toolbar.insert(self.tbAuth, -1)

		self.toolbar.set_icon_size(gtk.ICON_SIZE_SMALL_TOOLBAR)

		# All those objects go in the main vbox:
		self.mainvbox = gtk.VBox()
		self.mainvbox.pack_start(menubox, False, False, 0)
		self.mainvbox.pack_start(self.toolbar, False, False, 0)
		self.mainvbox.pack_start(locationbox, False, False, 0)
		#self.mainvbox.pack_start(self.scrolledwindow, True, True, 0)
		self.mainvbox.pack_start(vpaned, True, True, 0)
		self.statusbar = gtk.Label()
		self.statusbar.set_justify(gtk.JUSTIFY_LEFT)
		self.mainvbox.pack_start(self.statusbar, False, True, 0)
		#self.window.set_property('allow-shrink', True)

		self.updateBackForward()
		self.window.add(self.mainvbox)
		self.window.show_all()

		#Start focus on the entry:
		self.window.set_focus(self.locationentry)

		# Disable the copy/add podcast until valid podcast is here.
		self.tbCopy.set_sensitive(self.podcast != "")
		self.tbAddPod.set_sensitive(self.podcast != "")
		self.addpodmenu.set_sensitive(self.podcast != "")
		self.copym.set_sensitive(self.podcast != "")
		self.tbAuth.hide()

		self.noneSelected()

		self.config = ConfigBox(self) # Only one configuration box, it has reference back to here to change toolbar,statusbar settings.

		# Set up the main url handler with downloading and cookies:
		self.cj = cookielib.CookieJar()
		self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
		self.opener.addheaders = [('User-agent', self.descView.ua),
					  ('Accept-Encoding', 'gzip'),
					  ('Accept-Language', 'en-US')]

	def webkitZI(self, obj):
		self.descView.zoom_in()

	def webkitZO(self, obj):
		self.descView.zoom_out()

	def webkitZN(self, obj):
		self.descView.set_zoom_level(1)

	def buttonGoto(self, obj, url):
		"Menu directory-shortcuts handler"
		self.gotoURL(url, True)

	def goHome(self, obj):
		self.gotoURL(self.config.home, True)

	def getDirectory(self):
		"""Sets up quick links in the Go menu.
		This info appears to have been moved to
		    <script id="protocol" type="text/x-apple-plist">
		sections, so this code no longer works correctly."""
		pass

	def noneSelected(self):
		"When no row is selected, buttons are greyed out."
		self.tbInfo.set_sensitive(False)
		self.tbPlay.set_sensitive(False)
		self.tbGoto.set_sensitive(False)
		self.tbDownload.set_sensitive(False)

	def addTab(self, match, urllink):
		label = gtk.Label()
		label.show()
		contents = gtk.Label()
		contents.show()
		contents.set_size_request(0, 0) # No tab contents
		if match[0:12] == ", Selected. ":
			match = match[12:]
			logging.debug("sel: " + match)
			label.set_markup("<i><b>" + glib.markup_escape_text(match) + "</b></i>")
			self.notebook.append_page(contents, label)
			self.notebook.set_current_page(-1) #select this one
			self.notebook.queue_draw_area(0, 0, -1, -1)
		else:
			match = match[2:]
			label.set_markup(glib.markup_escape_text(match))
			self.notebook.append_page(contents, label)
		self.taburls.append(urllink)
		self.notebook.show_all()

	def progUpdate(self, obj):
		"""Checks for update to the program."""
		openDefault("http://tunesviewer.sourceforge.net/checkversion.php?version="+TV_VERSION)

	def treesel(self, selection, model):
		"""Called when selection changes, changes the enabled toolbar buttons."""
		self.tbInfo.set_sensitive(True)
		ind = selection[0]
		gotoable = (self.liststore[ind][8] != "")
		playable = (self.liststore[ind][9] != "")
		downloadable = (self.liststore[ind][9] != "" and
				(self.liststore[ind][10] == "" or
				 self.liststore[ind][10] == "0"))
		self.tbGoto.set_sensitive(gotoable) # only if there is goto url
		self.tbPlay.set_sensitive(playable) # only if there is media url
		self.tbDownload.set_sensitive(downloadable)
		self.rcgoto.set_sensitive(gotoable)
		self.rccopy.set_sensitive(gotoable)
		self.rcplay.set_sensitive(playable)
		self.rcdownload.set_sensitive(downloadable)
		return True

	# 3 required functions for drag-drop:
	def motion_cb(self, wid, context, x, y, time):
		context.drag_status(gtk.gdk.ACTION_COPY, time)
		# Returning True which means "I accept this data".
		return True

	def drop_cb(self, wid, context, x, y, time):
		# Some data was dropped, get the data
		wid.drag_get_data(context, context.targets[-1], time)
		context.finish(True, False, time)
		return True

	def got_data_cb(self, wid, context, x, y, data, info, time):
		if data.get_target() != "text/html":
			logging.debug(data.get_text())
			if data.get_text() == data.data:
				url = data.data
			else:
				try:
					url = unicode(data.data, "utf-16")
				except:
					logging.warn("Couldn't decode the data grabbed.")
					url = ""
			logging.debug(url)
			logging.debug(url.lower()[:9])
			if url.lower()[:9] == "<a href=\"":
				url = url[9:url.find("\"", 9)]
				logging.debug("u: " + url)
			if url != "":
				self.gotoURL(url, True)
			context.finish(True, False, time)

	def find_in_page_cb(self, widget, findT):
		while 1:
			widget.currentFound += 1
			if widget.currentFound >= len(self.liststore):
				msg = gtk.MessageDialog(widget,
							gtk.DIALOG_MODAL,
							gtk.MESSAGE_INFO,
							gtk.BUTTONS_OK,
							"End of page.")
				msg.run()
				msg.destroy()
				widget.currentFound = -1 #start at beginning.
				break
			thisrow = self.liststore[widget.currentFound]
			if (str(thisrow[1]).lower().find(findT) > -1 or
			    str(thisrow[2]).lower().find(findT) > -1 or
			    str(thisrow[3]).lower().find(findT) > -1 or
			    str(thisrow[4]).lower().find(findT) > -1 or
			    str(thisrow[5]).lower().find(findT) > -1 or
			    str(thisrow[6]).lower().find(findT) > -1 or
			    str(thisrow[7]).lower().find(findT) > -1):
				logging.debug(str(thisrow[1])) #this is a match.
				self.treeview.get_selection().select_iter(thisrow.iter)
				self.treeview.scroll_to_cell(thisrow.path,
							     None, False, 0, 0)
				break

		# TODO: Fix webkit search so it will search and highlight
		# the text, this should work, but it doesn't:
		self.descView.search_text(findT, False, True, True)
		self.descView.set_highlight_text_matches(highlight=True)


	def openDownloadDir(self, obj):
		openDefault(self.config.downloadfolder)


	def viewsource(self, obj):
		"""
		Starts a new View Source box based on current url and source.
		"""
		VWin("Source of: " + self.url, self.source)


	def treeclick(self, treeview, event):
		"""
		For right click menu:
		see http://faq.pygtk.org/index.py?req=show&file=faq13.017.htp
		"""
		if event.button == 3:
			x = int(event.x)
			y = int(event.y)
			moment = event.time
			pthinfo = treeview.get_path_at_pos(x, y)
			if pthinfo is not None:
				path, col, cellx, celly = pthinfo
				treeview.grab_focus()
				treeview.set_cursor(path, col, 0)
				# Right click menu
				self.rcmenu.popup(None, None, None,
						  event.button, moment)
			return True

	def tabChange(self, obj1, obj2, i):
		if len(self.taburls) > i: #is in range
			if self.url != self.taburls[i]: # is different page
				logging.debug("Loading other tab...")
				self.gotoURL(self.taburls[i], True)


	def bugReport(self, obj):
		logging.debug("Opening bug")
		openDefault(BUG_URL)


	def showHelp(self, obj):
		logging.debug("Opening Help")
		openDefault(HELP_URL)


	def showAbout(self, obj):
		msg = gtk.MessageDialog(self.window,
					gtk.DIALOG_MODAL,
					gtk.MESSAGE_INFO,
					gtk.BUTTONS_CLOSE,
					"TunesViewer - Easy iTunesU access\n"
					"Version %s\n\n"
					"(C) 2009 - 2012 Luke Bryan\n"
					"2011 - 2012 Rogério Theodoro de Brito\n"
					"and other contributors.\n"
					"Icon based on Michał Rzeszutek's openclipart hat.\n"
					"Loading-throbber based on Firefox icon.\n"
					"PyGTK Webkit interface and inspector code (C) 2008 Jan Alonzo.\n"
					"This is open source software, distributed 'as is'." % (TV_VERSION,))
		msg.run()
		msg.destroy()

	def viewDownloads(self, obj):
		self.downloadbox.window.show()

	def viewCookie(self, obj):
		cList = []
		logging.debug(self.cj._cookies)
		for k in self.cj._cookies.keys():
			cList.append(k)
			for k2 in self.cj._cookies[k].keys():
				cList.append("   " + k2)
				for k3 in self.cj._cookies[k][k2]:
					cList.append("      " + k3 + " = " +
						     self.cj._cookies[k][k2][k3].value)
		VWin("Cookies", "\n".join(cList))

	def advancedSearch(self, obj):
		self.findbox.window.show_all()

	def searchCurrent(self, obj):
		self.findInPage.show_all()

	def pastego(self, obj):
		"Gets the clipboard contents, and goes to link."
		clip = gtk.clipboard_get()
		text = clip.wait_for_text()
		if text != None:
			self.gotoURL(text, True)

	def addPod(self, obj):
		"Adds the current podcast to the specified podcast manager."
		cmds = self.config.podcastprog.split(" ")
		for i in range(len(cmds)):
			if cmds[i] == "%u":
				cmds[i] = self.podcast
			if cmds[i] == "%i" and self.podcast[0:4] == "http":
				cmds[i] = "itpc" + self.podcast[self.podcast.find("://"):] #rhythmbox requires itpc to specify it's a podcast.
		try:
			subprocess.Popen(cmds)
		except OSError as e:
			msg = gtk.MessageDialog(self.window,
						gtk.DIALOG_MODAL,
						gtk.MESSAGE_WARNING,
						gtk.BUTTONS_CLOSE,
						"Error running: %s\n\n"
						"Is the program installed and working?\n%s" % (" ".join(cmds), e))
			msg.run()
			msg.destroy()

	def copyrss(self, obj):
		"""
		Copies the standard rss podcast link for the current page.
		"""
		logging.debug("Copying: " + self.podcast)
		gtk.Clipboard().set_text(self.podcast)

	def goBack(self, obj):
		"""
		Called when back-button is pressed.
		"""
		if len(self.backStack) > 0 and not(self.downloading):
			logging.debug(self.backStack)
			logging.debug(self.forwardStack)

			self.forwardStack.append(self.url)
			self.gotoURL(self.backStack[-1], False) # last in back stack
			if self.downloadError:
				#undo add to forward:
				self.forwardStack.pop()
			else:
				#remove from back:
				self.backStack.pop()

			logging.debug(self.backStack)
			logging.debug(self.forwardStack)
		else:
			gtk.gdk.beep()
		#Update the back, forward buttons:
		self.updateBackForward()

	def goForward(self, obj):
		"""
		Called when forward button is pressed.
		"""
		if len(self.forwardStack) > 0 and not(self.downloading):
			self.backStack.append(self.url)
			self.gotoURL(self.forwardStack[-1], False)
			if self.downloadError:
				#undo add to back:
				self.backStack.pop()
			else:
				#remove from forward:
				self.forwardStack.pop()
		else:
			gtk.gdk.beep()
		self.updateBackForward()

	def updateBackForward(self):
		"Disables the back and forward buttons when no back/forward is on stack."
		self.tbForward.set_sensitive(len(self.forwardStack))
		self.tbBack.set_sensitive(len(self.backStack))

	def stop(self, obj):
		"Called when stop is pressed, tries to stop downloader."
		self.downloading = False

	def refresh(self, obj):
		"Called when refresh is pressed, reopens current page."
		self.gotoURL(self.url, False)

	def gobutton(self, obj):
		"Called when the go-button is pressed."
		ind = self.modecombo.get_active()
		if ind == 0:
			self.gotoURL(self.locationentry.get_text(), True)
		elif ind == 1:
			self.gotoURL(SEARCH_U % self.locationentry.get_text(), True)
		else:
			self.gotoURL(SEARCH_P % self.locationentry.get_text(), True)

	def followlink(self, obj):
		"""
		Follows link of the selected item.
		"""
		if self.selected() is None:
			return
		self.gotoURL(self.selected()[8], True)

	def copyRowLink(self, obj):
		if self.selected() is None:
			return
		logging.debug(self.selected()[8])
		gtk.Clipboard().set_text(self.selected()[8])

	def combomodechanged(self, obj):
		"""
		Called when the search/url combobox is changed, sets focus
		to the location-entry.
		"""
		self.window.set_focus(self.locationentry)
		if self.modecombo.get_active() == 0:
			self.locationentry.set_text(self.url)
		self.locationentry.select_region(0, -1)

	def openprefs(self, obj):
		self.config.window.show_all()

	def exitclicked(self, obj):
		self.delete_event(None, None, None)

	def rowSelected(self, treeview, path, column):
		"""
		Called when row is selected with enter or double-click, runs
		default action.
		"""
		model = self.treeview.get_model()
		iter = model.get_iter(path)
		for i in range(7):
			logging.debug(model.get_value(iter, i))
		openurl = model.get_value(iter, 9) #directurl
		gotourl = model.get_value(iter, 8)

		if (int(self.config.defaultcommand) == 1 and openurl != ""):
			self.playview(None) # play directly.
			logging.debug("played")
		elif (int(self.config.defaultcommand) == 2 and openurl != ""):
			self.download(None) # download.
		else:
			logging.debug("goto")
			if (gotourl != "" and openurl == "" and
			    model.get_value(iter, 5) == "(Web Link)"):
				logging.debug("web link")
				openDefault(gotourl)
			else:
				self.gotoURL(gotourl, True)

	def playview(self, obj):
		"""
		Plays or views the selected file
		(Streaming to program directly, not downloading).
		"""
		logging.debug(self.selected())
		if self.selected() is None:
			return
		url = self.selected()[9]
		kind = self.selected()[4]
		if kind in self.config.openers:
			# Open the url with the program:
			start(self.config.openers[kind], url)
		elif url == "":
			msg = gtk.MessageDialog(self.window,
						gtk.DIALOG_MODAL,
						gtk.MESSAGE_WARNING,
						gtk.BUTTONS_CLOSE,
						"This item is not a file.")
			msg.run()
			msg.destroy()
			return
		else:
			msg = gtk.MessageDialog(self.window,
						gtk.DIALOG_MODAL,
						gtk.MESSAGE_WARNING,
						gtk.BUTTONS_CLOSE,
						"You don't have any program set to open " +
						kind +
						"\nfiles directly from the web. "
						"You must first choose the program in Preferences.")
			msg.run()
			msg.destroy()

	def locationBar(self, obj):
		"""
		Selects the url, similar to Ctrl+L in web browser.
		"""
		self.modecombo.set_active(0)

	def viewprop(self, obj):
		# the reference to the new ItemDetails is stored in infoboxes array.
		# if it isn't stored, the garbage collector will mess it up.
		self.infoboxes.append(ItemDetails(self, self.selected()))

	def selected(self):
		"""
		Gives the array of properties of selected item.
		"""
		(model, iter) = self.treeview.get_selection().get_selected()
		out = []
		for i in range(12):
			try:
				out.append(model.get_value(iter, i))
			except TypeError:
				return None
			except AttributeError:
				return None
		return out

	def download(self, obj):
		if self.selected() is None:
			return
		properties = self.selected()
		self.startDownload(properties)

	def startDownload(self, properties):
		name = htmlentitydecode(properties[1])
		artist = properties[2]
		duration = properties[3]
		extType = properties[4]
		comment = properties[5]
		url = properties[9]
		if url == "":
			msg = gtk.MessageDialog(self.window,
						gtk.DIALOG_MODAL,
						gtk.MESSAGE_WARNING,
						gtk.BUTTONS_CLOSE,
						"This item is not a file.")
			msg.run()
			msg.destroy()
			return
		if properties[10] != "0" and properties[10] != "":
			return
		self.downloadFile(name, artist, duration, extType, comment, url)

	def downloadFile(self, name, artist, duration, extType, comment, url):
		name = safeFilename(name, self.config.downloadsafe)
		artist = safeFilename(artist, self.config.downloadsafe)
		duration = safeFilename(duration, self.config.downloadsafe)
		if duration == "(unknown)":
			duration = "" #not specified in many files, pdfs etc.
		extType = safeFilename(extType, self.config.downloadsafe)
		comment = safeFilename(comment, self.config.downloadsafe)
		title = safeFilename(self.window.get_title(), self.config.downloadsafe)
		# Now make an appropriate local-file name:
		local = self.config.downloadfile \
		  .replace("%n", name).replace("%a", artist).replace("%p", title).replace("%c", comment).replace("%t", extType).replace("%l", duration)#.replace(os.sep, "-")
		logging.debug("LOCAL=" + local)

		final_file = os.path.join(self.config.downloadfolder, local)
		logging.debug(final_file)
		if not os.path.isfile(final_file):
			try:
				os.makedirs(os.path.dirname(final_file))
			except OSError:
				pass #File path already exists, can't create.
			try:
				#Try opening filename in the appropriate folder:
					a = open(final_file, "w")
					a.close()
			except IOError:
				# shorten filename to make the filesystem accept it.
				local = local.replace(" ", "")
				if len(local) > 100:
					local = local[-99:]

		self.downloadbox.newDownload(self.iconOfType(extType), url, final_file, self.opener)
		logging.debug("Starting download of " + local +
			      " to " + final_file)
		self.downloadbox.window.show()

	def main(self):
		"""
		Startup.
		"""
		# Check for crashed downloads, AFTER test for another currently running instance.
		socket.setdefaulttimeout(11) # should improve freeze-up when cancelling downloads
		try:
			pending_dl_file = os.path.expanduser("~/.tunesviewerDownloads")
			dlines = open(pending_dl_file, 'r').read().split("\n")
			os.remove(pending_dl_file)
			for i in range(len(dlines)):
				if dlines[i].startswith("####"):
					self.downloadbox.newDownload(None, dlines[i+1], dlines[i+2], self.opener)
		except IOError as e:
			logging.debug("No downloads crashed.")

		if self.url == "":
			self.gotoURL(self.config.home, False)
		else:
			self.gotoURL(self.url, True)
		self.throbber.hide()
		gtk.main()

	def delete_event(self, widget, event, data=None):
		"""
		Called when exiting, checks if downloads should be cancelled.
		"""

		pending_dl_file = os.path.expanduser("~/.tunesviewerDownloads")
		self.config.save_settings()
		if self.downloadbox.downloadrunning:
			msg = gtk.MessageDialog(self.window,
						gtk.DIALOG_MODAL,
						gtk.MESSAGE_QUESTION,
						gtk.BUTTONS_YES_NO,
						"Are you sure you want to exit? "
						"This will cancel all active downloads.")
			answer = msg.run()
			msg.destroy()
			if answer == gtk.RESPONSE_YES:
				# Clear crash recovery
				try:
					os.remove(pending_dl_file)
				except OSError as e:
					pass
				self.sock.sendUrl("EXIT")
				self.downloadbox.cancelAll()
				self.downloadbox.window.destroy()
				gtk.main_quit()

				return False
			else:
				return True
		else:
			# Clear crash recovery
			try:
				os.remove(pending_dl_file)
			except OSError as e:
				pass
			self.sock.sendUrl("EXIT")
			self.downloadbox.window.destroy()
			gtk.main_quit()


	def setLoadDisplay(self, load):
		"""
		Shows that page is loading.
		"""
		if load:
			if self.config.throbber:
				self.throbber.show()
			self.window.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
		else:
			self.window.window.set_cursor(None)
			self.throbber.hide()

	def gotoURL(self, url, newurl):
		"""
		Downloads data, then calls update.
		If newurl is true, forward is cleared.
		"""
		oldurl = self.url # previous url, to add to back stack.
		if url.startswith("download://"):
			logging.debug("DOWNLOAD:// interface called with xml:"+urllib.unquote(url))
			xml = urllib.unquote(url)[11:]
			dom = etree.fromstring(xml)
			keys = dom.xpath("//key")
			name = ""
			artist = ""
			duration = ""
			extType = ""
			comment = ""
			url = ""
			for key in keys:
				print key.text, key.getnext().text
				if key.text == "navbar":
					return
				if key.text == "URL" and key.getnext() is not None:
					url = key.getnext().text
				elif key.text == "artistName" and key.getnext() is not None:
					artist = key.getnext().text
				elif key.text == "fileExtension" and key.getnext() is not None:
					extType = "."+key.getnext().text
				elif key.text == "songName" and key.getnext() is not None:
					name = key.getnext().text
			if extType==".rtf":
				extType = ".zip"
			self.downloadFile(name, artist, duration, extType, comment, url)
			return
		elif url.startswith("copyurl://"):
			tocopy = urllib.unquote(url[10:].replace("[http:]","http:").replace("[https:]","https:"))
			gtk.Clipboard().set_text(tocopy)
			logging.debug("copied "+tocopy)
			return
		if self.downloading:
			return
		elif url.startswith("web"):
			logging.debug(url)
			openDefault(url[3:])
			return
		# Fix url based on http://bugs.python.org/issue918368
		try:
			url = urllib.quote(url, safe="%/:=&?~#+!$,;'@()*[]")
		except KeyError:
			#A workaround for bad input: http://bugs.python.org/issue1712522
			logging.warn("Error: unexpected input, " + url)
			return
		logging.debug(url)
		self.downloading = True
		self.tbStop.set_sensitive(True)

		#Fix page-link:
		if url.startswith("http://www.apple.com/itunes/affiliates/download/"):
			if url.find("Url=") > -1:
				url = urllib.unquote(url[url.find("Url=") + 4:])
			else:
				logging.debug("Dead end page")

		if (str.upper(url)[:4] == "ITMS" or str.upper(url)[:4] == "ITPC"):
			url = "http" + url[4:]
		elif url == "": #no url
			self.downloading = False
			self.tbStop.set_sensitive(False)
			return

		#Apparently the x-apple-tz header is UTC offset *60 *60.
		self.tz = str(-time.altzone)
		self.opener.addheaders = [('User-agent', self.descView.ua),
					  ('Accept-Encoding', 'gzip'),
					  ('X-Apple-Tz', self.tz)]
		htmMode = self.htmlmode.get_active() #the checkbox
		if htmMode:
			self.opener.addheaders = [('User-agent', self.descView.ua),
						  ('Accept-Encoding', 'gzip'),
						  ("X-Apple-Tz:", self.tz),
						  ("X-Apple-Store-Front", "143441-1,12")]
		if self.mobilemode.get_active():
			# As described on
			# http://blogs.oreilly.com/iphone/2008/03/tmi-apples-appstore-protocol-g.html
			self.opener.addheaders = [('User-agent', 'iTunes-iPhone/1.2.0'),
						  ('Accept-Encoding', 'gzip'),
						  ('X-Apple-Store-Front:', '143441-1,2')]
		#Show that it's loading:
		self.setLoadDisplay(True)

		t = Thread(target=self.loadPageThread, args=(self.opener, url, newurl))
		self.downloading = True
		self.tbStop.set_sensitive(True)
		t.start()

	def loadPageThread(self, opener, url, newurl):
		pageType = ""
		text = ""
		try:
			#Downloader:
			response = opener.open(url)
			pageType = response.info().getheader('Content-Type', 'noheader?')
			if pageType.startswith("text") or pageType=='noheader?': #(noheader on subscribe sometimes)
				next = response.read(100)
				while next != "" and self.downloading:
					text += next
					next = response.read(100)
				if next == "": #Finished successfully.
					self.downloadError = ""

					if response.info().get('Content-Encoding') == 'gzip':
						orig = len(text)
						f = gzip.GzipFile(fileobj=StringIO(text))
						try:
							text = f.read()
							logging.debug("Gzipped response: " + str(orig) + "->" + str(len(text)))
						except IOError as e: #bad file
							logging.debug(str(e))
				else:
					self.downloadError = "stopped."
			else:
				self.downloadbox.newDownload(None,
							     url,
							     os.path.join(self.config.downloadfolder,
									  safeFilename(url[url.rfind("/")+1:],
										       self.config.downloadsafe)),
							     opener)
				return
			response.close()
		except Exception as e:
			self.downloadError = "Download Error:\n" + str(e)
			logging.error(e)
		gobject.idle_add(self.update, url, pageType, text, newurl)


	def update(self, url, pageType, source, newurl):
		"""
		Updates display given url, content-type, and source.
		This does all the gui work after loadPageThread.
		"""
		self.downloading = False
		self.tbStop.set_sensitive(False)
		try:
			#Show it finished:
			self.setLoadDisplay(False)
		except AttributeError:
			pass #just exited, don't crash.
		if self.downloadError != "": #Warn if there is an error:
			msg = gtk.MessageDialog(self.window,
						gtk.DIALOG_MODAL,
						gtk.MESSAGE_ERROR,
						gtk.BUTTONS_CLOSE,
						str(self.downloadError))
			msg.run()
			msg.destroy()
			self.downloading = False
			return False
		if self.modecombo.get_active() == 0:
			self.locationentry.set_text(url)
		self.downloading = False
		self.tbStop.set_sensitive(False)

		if url.startswith("https://"): #security icon
			tip = "Secure page."
			self.tbAuth.show()
			try:#urllib.unquote?
				id = self.cj._cookies[".deimos.apple.com"]["/WebObjects"]["identity"].value
				logging.debug("identity: " + id)
				tip += "\nLogged in as: %s" % id
				logging.debug("credentialKey: " +
					      self.cj._cookies[".deimos.apple.com"]["/WebObjects"]["identity"].value)
			except:
				logging.debug("none")
			self.tbAuth.set_tooltip_text(tip)
		else:
			self.tbAuth.hide()

		#Parse the page and display:
		logging.debug("PARSING " + url + " " + pageType)
		parser = Parser(url, pageType, source)
		if parser.Redirect != "":
			logging.debug("REDIRECT: " + parser.Redirect)
			self.gotoURL(parser.Redirect, True)
			return False
		elif len(parser.mediaItems) == 1 and parser.singleItem:
			#Single item description page.
			self.startDownload(parser.mediaItems[0])
			return False
		else: #normal page, show it:
			logging.debug("normal page" + url)
			#Reset data:
			self.taburls = [] #reset tab-urls until finished to keep it from going to other tabs.
			while self.notebook.get_n_pages():
				self.notebook.remove_page(self.notebook.get_n_pages()-1)
			for i in range(len(parser.tabMatches)):
				self.addTab(parser.tabMatches[i], parser.tabLinks[i])
			self.liststore.clear()
			# fix performance problem. The treeview shouldn't be connected to
			# the treeview while updating! see http://eccentric.cx/misc/pygtk/pygtkfaq.html
			self.treeview.set_model(None)

			#Reset sorting:
			self.liststore.set_sort_column_id(-2, gtk.SORT_DESCENDING)

			#Load data:
			self.descView.loadHTML(parser.HTML, url)
			logging.debug("ITEMS: " + str(len(parser.mediaItems)))
			for item in parser.mediaItems:
				self.liststore.append(item)
			self.window.set_title(parser.Title)

			#Get the icons for all the rows:
			self.updateListIcons()

			#No item selected now, disable item buttons.
			self.noneSelected()
			self.treeview.set_model(self.liststore)
			logging.debug("Rows:" + str(len(self.liststore)))
			mediacount = 0
			linkscount = 0
			for row in self.liststore:
				if len(row) > 10 and row[9]:
					mediacount += 1
				elif row[8]:
					linkscount += 1
			#specific item should be selected?
			for i in self.liststore:
				if i[11] == parser.itemId:
					logging.debug("Selecting item " + parser.itemId)
					self.treeview.get_selection().select_iter(i.iter)
					self.treeview.scroll_to_cell(i.path,
								     None,
								     False, 0,
								     0)
			#Only change the stack if this is an actual page, not redirect/download.
			if newurl:
				self.forwardStack = []
				if self.url != "":
					self.backStack.append(self.url)
			self.url = url
			self.source = source
			self.podcast = parser.podcast
			#Update the back, forward buttons:
			self.updateBackForward()
			#Enable podcast-buttons if this is a podcast:
			self.tbCopy.set_sensitive(parser.podcast != "")
			self.tbAddPod.set_sensitive(parser.podcast != "")
			self.addpodmenu.set_sensitive(parser.podcast != "")

			rs = ""
			ls = ""
			ms = ""
			if len(self.liststore) != 1:
				rs = "s"
			if linkscount != 1:
				ls = "s"
			if mediacount != 1:
				ms = "s"
			self.statusbar.set_text("%s row%s, %s link%s, %s file%s" % \
			(len(self.liststore), rs, linkscount, ls, mediacount, ms))
			return False

	def updateListIcons(self):
		"""
		Sets the icons in the liststore/bottom panel based on the
		media type.
		"""
		self.icon_audio = None
		self.icon_video = None
		self.icon_book = None
		self.icon_zip = None
		self.icon_other = None
		self.icon_link = None
		try:
			icon_theme = gtk.icon_theme_get_default() #Access theme's icons:
			self.icon_audio = icon_theme.load_icon("sound", self.config.iconsizeN, 0)
			self.icon_video = icon_theme.load_icon("video", self.config.iconsizeN, 0)
			self.icon_pdf = icon_theme.load_icon("gnome-mime-application-pdf", self.config.iconsizeN, 0)
			self.icon_zip = icon_theme.load_icon("gnome-mime-application-zip", self.config.iconsizeN, 0)
			self.icon_other = icon_theme.load_icon("gnome-fs-regular", self.config.iconsizeN, 0)
			self.icon_link = icon_theme.load_icon("gtk-jump-to-ltr", self.config.iconsizeN, 0)
		except Exception as e:
			logging.warn("Could not set up all the icons: " + str(e))


		for row in self.liststore:
			content_type = row[4].lower()

			self.liststore.set(row.iter, 0,
					   self.iconOfType(content_type))

			url = row[10]

	def iconOfType(self, content_type):
		icon_of_type = {
			'.aif': self.icon_audio,
			'.aiff': self.icon_audio,
			'.amr': self.icon_audio,
			'.m4a': self.icon_audio,
			'.m4p': self.icon_audio,
			'.mp3': self.icon_audio,

			'.3gp': self.icon_video,
			'.m4b': self.icon_video,
			'.m4v': self.icon_video,
			'.mov': self.icon_video,
			'.mp4': self.icon_video,

			'.pdf': self.icon_pdf,

			'.epub': self.icon_other,

			'.zip': self.icon_zip,
			}

		try:
			return icon_of_type[content_type]
		except KeyError as e:
			logging.debug("Couldn't find specific icon for type %s" % str(e))
			return self.icon_other

class VWin:
	def __init__(self, title, source):
		"""
		When initialized, this will show a new window with text.
		"""
		self.window = gtk.Window()
		self.window.set_size_request(400, 400)
		self.window.set_title(title)

		self.sw = gtk.ScrolledWindow()
		self.sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		self.viewer = gtk.TextView()
		self.viewer.get_buffer().set_text(source)
		self.viewer.set_wrap_mode(gtk.WRAP_WORD)
		self.viewer.set_editable(False)
		#TextView inside ScrolledWindow goes in the window:
		self.sw.add(self.viewer)
		self.window.add(self.sw)
		self.window.show_all()


def parse_cli():
	import optparse
	parser = optparse.OptionParser()

	parser.add_option('-s', '--search', help='Give terms to search for university media')
	parser.add_option('-p','--search-podcast', help='Give terms to search podcasts',metavar='SEARCH', dest="podcastsearch")
	parser.add_option('-d','--download', help='download html only, no GUI', metavar='DOWNLOADFILE')
	parser.add_option('-v', '--verbose', help='Output debug information', action='store_true', default=False)
	parser.add_option('-V', '--version', help='Output version number and exit', action='store_true', default=False, dest="version")

	opts, args = parser.parse_args()

	if opts.search is not None:
		url = SEARCH_U % opts.search
	elif opts.podcastsearch is not None:
		url = SEARCH_P % opts.podcastsearch
	elif len(args) > 0:
		url = args[0]
	else:
		url = ''

	if opts.version:
		print ("TunesViewer " + TV_VERSION)
		import sys
		sys.exit(0)
	if opts.verbose:
		logging.basicConfig(level=logging.DEBUG)
	if opts.download:
		if url:
			opener = urllib2.build_opener()
			opener.addheaders = [('User-agent', USER_AGENT)]
			text = opener.open(url).read()
			parsed = Parser(url, "text/HTML", text)
			open(opts.download,'w').write(parsed.HTML)
			print "Wrote file to",opts.download
			import sys
			sys.exit(0)
		else:
			print "No url specified. Starting normally."

	return url


if __name__ == "__main__":

	url = parse_cli()
	# Create the TunesViewer instance and run it. If an instance is
	# already running, send the url to such instance.
	prog = TunesViewer()
	prog.sock = SingleWindowSocket(url, prog)

	if prog.sock.RUN:
		try:
			prog.url = url
			prog.main()
		except KeyboardInterrupt:
			print "Keyboard Interrupt, exiting."
			prog.exitclicked(None)
	else:
		logging.info("Sending url to already-running window.")
