#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Download window class.

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

import gobject
import gio
import gtk

from downloader import Downloader
from common import *
import constants

class DownloadBox:
	"""
	Window for showing and keeping track of downloads.
	"""
	downloaders = [] # Holds references to the downloader objects
	downloaded = 0
	total = 0
	lastCompleteDownloads = 0
	devicedir = None # last selected mp3-player directory:

	##
	# True when a download is running
	downloadrunning = False

	def __init__(self, Wopener):
		self.Wopener = Wopener # reference to main prog.
		self.window = gtk.Window()
		self.window.set_icon(self.window.render_icon(gtk.STOCK_SAVE,
							     gtk.ICON_SIZE_BUTTON))
		self.window.set_title("Downloads")
		self.window.set_size_request(500, 200)
		self.window.connect("delete_event", self.onclose)
		self.vbox = gtk.VBox()
		self.vbox.show()
		scrolledwindow = gtk.ScrolledWindow()
		scrolledwindow.show()
		scrolledwindow.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
		scrolledwindow.add_with_viewport(self.vbox)
		self.window.add(scrolledwindow)

	def updateLoop(self):
		"""
		Updates each downloader display.
		"""
		# Get downloaded/total
		self.downloaded = 0
		self.total = 0
		# Also get bytes/bytes total, for overall download percentage:
		totalbytes = 0
		dlbytes = 0
		for i in self.downloaders:
			i.update()
			if i.success:
				self.downloaded += 1
				self.total += 1
			else: #elif i.downloading:
				self.total += 1
			totalbytes += i.filesize
			dlbytes += i.count
		percent = ""
		if totalbytes != 0:
			percent = str(round(dlbytes/totalbytes*100, 1)) + "%, "
		self.window.set_title("Downloads (%s%s/%s downloaded)" %
		  (percent, str(self.downloaded), str(self.total)))
		if self.downloaded == self.total:
			self.downloadrunning = False
			self.downloadNotify()
			return False # Downloads Done.
		else:
			return True

	def onclose(self, widget, data):
		"""
		Cancels closing window, hides it instead.
		"""
		self.window.hide()
		return True # Cancel close window.

	def cancelAll(self):
		"""
		Tell all downloaders to cancel.
		"""
		while len(self.downloaders):
			self.downloaders[0].cancel(0)

	def downloadNotify(self):
		if (self.Wopener.config.notifyseconds != 0 and
		    self.lastCompleteDownloads != self.downloaded):
			self.lastCompleteDownloads = self.downloaded
			try:
				import pynotify
				if self.total == 1:
					s = ""
				else:
					s = "s"
				pynotify.init("TunesViewer")
				n = pynotify.Notification("Download%s Finished" % s,
					"%s/%s download%s completed successfully." % (self.downloaded, self.total, s), gtk.STOCK_GO_DOWN)
				n.set_timeout(1000 * self.Wopener.config.notifyseconds)
				n.show()
			except (ImportError, gio.Error, glib.GError) as e:
				logging.warn("Notification failed: " + str(e))

	def newDownload(self, icon, url, localfile, opener):
		"""
		Downloads a url

		Takes a url, filetype icon, local filename, and opener.
		"""
		#Check if already downloading/downloaded:
		for i in self.downloaders:
			if url == i.url or localfile == i.localfile: # already in download-box.
				if i.downloading:
					message = "File is already downloading."
				else:#if (i.success):
					message = "File already downloaded."
				msg = gtk.MessageDialog(self.window,
							gtk.DIALOG_MODAL,
							gtk.MESSAGE_INFO,
							gtk.BUTTONS_CLOSE,
							message)
				msg.run()
				msg.destroy()
				return
		self.window.show()
		d = Downloader(icon, url, localfile, opener, self)
		self.downloaders.append(d)
		# Add the visible downloader progressbar etc.
		el = d.getElement()
		el.show()
		self.vbox.pack_start(el, False, False, 10)
		self.window.show()
		if not self.downloadrunning:
			#Start download loop:
			self.downloadrunning = True
			# instead of updating every kb or mb, update regularly.
			# This should work well no matter what the download speed is.
			logging.debug("STARTING TIMEOUT")
			# Only update the progress bar about once a second,
			# to lower the CPU load.
			gobject.timeout_add(1000, self.updateLoop)
		d.start()
		f = open(constants.DATA_FILE, 'a')
		f.write("#### url and localfile name: ####\n" + url + "\n" + localfile + "\n")
