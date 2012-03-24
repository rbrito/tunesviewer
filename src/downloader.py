#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
A class to handle a single download.

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

import httplib
import logging
import os
import time
import urllib2

from threading import Thread

import gobject
import gtk
import pango

from common import *

gobject.threads_init()

class Downloader:
	"""
	A downloader class to download a file.
	"""
	downloading = False # True if not cancelled or finished.
	success = False #Download succeeded.
	Err = "" # Error to show in progress box.
	copydir = None
	count = 0 # bytes downloaded
	filesize = 0 # total bytes
	readsize = "0" # Human-readable description of size.

	def __init__(self, icon, url, localfile, opener, downloadWindow):
		self.opener = opener # shared downloader
		self.url = url
		self.localfile = localfile
		#Reference to the download window's class
		self._downloadWindow = downloadWindow
		self._copyfile = downloadWindow.devicedir
		#This downloader has an upper and lower part inside a VBox:
		self._element = gtk.VBox() # main element container
		upper = gtk.HBox()
		upper.show()
		lower = gtk.HBox()
		lower.show()
		self._element.pack_start(upper, False, False, 0)
		self._element.pack_start(lower, False, False, 0)
		self._cancelbutton = gtk.Button("Cancel")
		self._cancelbutton.show()
		self._progress = gtk.ProgressBar(adjustment = None)
		self._progress.set_ellipsize(pango.ELLIPSIZE_END)
		self._progress.show()
		ic = gtk.Image()
		ic.set_from_pixbuf(icon)
		iconhold = gtk.EventBox()
		iconhold.connect("button-press-event", self.openit)
		iconhold.show()
		iconhold.add(ic)
		ic.show()
		upper.pack_start(iconhold, False, False, 7)
		upper.pack_start(self._progress, True, True, 0)
		upper.pack_start(self._cancelbutton, False, False, 0)
		name = gtk.Label("Downloading to: %s from: %s" % (localfile, url))
		name.show()
		name.set_ellipsize(pango.ELLIPSIZE_END)
		name.set_selectable(True)

		# Add action button
		self._combo = gtk.combo_box_new_text()
		self._combo.append_text("Choose Action:")
		self._combo.append_text("Open File")
		self._combo.append_text("Convert File")
		self._combo.append_text("Copy to Device")
		self._combo.append_text("Delete File")
		self._combo.set_active(0)
		self._combo.connect("changed", self.actionSelect)
		self._combo.show()

		self._mediasel = gtk.FileChooserButton("Choose the folder representing the device")
		self._mediasel.set_size_request(100, -1)
		self._mediasel.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
		self._mediasel.connect("current-folder-changed", self.folderChange)
		#self._mediasel.connect("file-set",self.folderChange)
		self._mediasel.hide()
		lower.pack_start(self._combo, False, False, 2)
		lower.pack_start(self._mediasel, False, False, 2)
		lower.pack_start(name, True, True, 0)
		#self._cancelbutton.show()
		if self._copyfile != None:
			self._mediasel.set_current_folder(self._copyfile)
		self._cancelbutton.connect_after("clicked", self.cancel)
		self._progress.show()
		self._element.show()

	def openit(self, obj, obj2):
		openDefault(self.localfile)

	def getElement(self):
		"""
		Return element containing the gui display for this
		download.
		"""
		return self._element

	def folderChange(self, obj):
		"""
		Called when the media-device-directory is changed, copies if
		download is finished.
		"""
		self._copydir = self._mediasel.get_current_folder()
		#Set the selection as the default for new downloads.
		self._downloadWindow.devicedir = self._copydir
		logging.debug(self._copydir)
		if self.success:
			#Downloaded, so copy it.
			self.copy2device()

	def copy2device(self):
		"""
		Copy to selected device.
		"""
		if self._copydir == None:
			self._progress.set_text("Select a directory.")
		else:
			#copy it:
			self._progress.set_text("Copying to %s..." % self._copydir)
			import shutil
			try:
				shutil.copy(self.localfile, self._copydir)
			except (IOError, os.error):
				self._progress.set_text("Error copying to %s." % self._copydir)
			else:
				self._progress.set_text("Copied to %s." % self._copydir)

	def actionSelect(self, obj):
		"""
		Called when the downloader's combo-box is changed.
		"""
		logging.debug(self._combo.get_active())
		if self._combo.get_active() == 3:
			self._mediasel.show()
		else:
			self._mediasel.hide()
		if self._combo.get_active() == 1 and self.success:
			# Open now, finished.
			openDefault(self.localfile)
		elif self._combo.get_active() == 2 and self.success:
			import subprocess
			try:
				subprocess.Popen(["soundconverter", self.localfile])
			except OSError:
				msg = gtk.MessageDialog(None,
							gtk.DIALOG_MODAL,
							gtk.MESSAGE_ERROR,
							gtk.BUTTONS_CLOSE,
							"Soundconverter not found, try installing it with your package manager.")
				msg.run()
				msg.destroy()
		elif self._combo.get_active() == 3 and self.success:
			# Try to copy, finished.
			self.copy2device()
		elif self._combo.get_active() == 4:
			logging.debug("del")
			self.deletefile()

	def cancel(self, obj):
		"""
		Cancels this download. (this is also called by delete command).
		"""
		#if self.downloading:
		self.downloading = False
		self.t.join() # wait for thread to cancel! Destroying this before the thread finishes may cause major crash!
		try:
			os.remove(self.localfile)
			logging.debug("removed " + self.localfile)
		except (IOError, OSError) as e:
			logging.debug("Removing file failed: " + str(e))

		self._element.destroy()
		#Remove all references to this.
		self._downloadWindow.downloaders.remove(self)
		logging.debug(self._downloadWindow.downloaders)

	def start(self):
		"""
		Starts download thread.
		"""
		self.t = Thread(target=self.downloadThread, args=())
		self.t.start()

	def downloadThread(self):
		"""
		This does the actual downloading, it should run as a thread.
		"""
		self.starttime = time.time()
		self._progress.set_text("Starting Download...")
		self.count = 0 # Counts downloaded size.
		self.downloading = True
		while self.downloading and not self.success:
			try:
				self.Err = ""
				self._netfile = self.opener.open(self.url)
				self.filesize = float(self._netfile.info()['Content-Length'])

				if os.path.exists(self.localfile) and os.path.isfile(self.localfile):
					self.count = os.path.getsize(self.localfile)

				logging.debug("%d of %d downloaded." % (self.count, self.filesize))

				if self.count >= self.filesize:
					self._progress.set_text("Already downloaded.")
					self._progress.set_fraction(1.0)
					self._cancelbutton.set_sensitive(False)
					self.downloading = False
					self.success = True
					self._netfile.close()
					return

				if os.path.exists(self.localfile) and os.path.isfile(self.localfile):
					#File already exists, start where it left off:
					#This seems to corrupt the file sometimes?
					self._netfile.close()
					req = urllib2.Request(self.url)
					logging.debug("File downloading at byte: %d." % self.count)
					req.add_header("Range", "bytes=%s-" % (self.count))
					self._netfile = self.opener.open(req)

				if self.downloading: # Don't do it if cancelled, downloading=false.
					next = self._netfile.read(1024)
					self._outfile = open(self.localfile, "ab") # to append binary
					self._outfile.write(next)
					self.readsize = desc(self.filesize) # get size mb/kb
					self.count += 1024
					while len(next) > 0 and self.downloading:
						next = self._netfile.read(1024)
						self._outfile.write(next)
						self.count += len(next)
					self.success = True
			except httplib.InvalidURL as e:
				self.Err = ("Invalid url. " + str(e))
				logging.warn("Error: " + str(e))
				if str(e).count("nonnumeric port"):
					#Workaround for bug: http://bugs.python.org/issue979407
					self.Err = ("Urllib failed! Opening with browser...")
					openDefault(self.url) #open with browser.
				self.downloading = False
				return
			except IOError as e:
				logging.warn(str(e))
				self.Err = ("Download error, retrying in a few seconds: " + str(e))
				try:
					self._outfile.close()
					self._netfile.close()
				except Exception:
					pass
				time.sleep(8) # Then repeat

		logging.debug("Finished one")
		try:
			self._outfile.close()
			self._netfile.close()
		except (IOError, OSError):
			pass
		if self.downloading: #Not cancelled.
			self.success = True #completed.
			self._progress.set_fraction(1.0)
			self._progress.set_text(self.readsize + " downloaded.")
			if self._combo.get_active() == 1:
				openDefault(self.localfile)
			elif self._combo.get_active() == 3:
				# Copy to Device
				self.copy2device()
			logging.debug("Pre dlnotify")
			self._cancelbutton.set_sensitive(False)
		#else:
			#This set_text isn't needed, it caused error when it was cancelled, and self._progress destroyed.
			#Shouldn't be accessing gui from a thread anyway.
			#see http://faq.pygtk.org/index.py?file=faq20.006.htp&req=show
			#self._progress.set_text("Error")
		self.downloading = False

	def deletefile(self):
		filesize = os.path.getsize(self.localfile)
		msg = gtk.MessageDialog(None,
					gtk.DIALOG_MODAL,
					gtk.MESSAGE_QUESTION,
					gtk.BUTTONS_YES_NO,
					"Are you sure you want to delete this %s file?\n%s" % (desc(filesize), self.localfile))
		answer = msg.run()
		msg.destroy()
		if answer == gtk.RESPONSE_YES:
			logging.debug("deleting...")
			self.cancel(None)
		else:
			self._combo.set_active(0)

	def update(self):
		if self.Err:
			self._progress.set_text(self.Err)
		elif self.count < self.filesize and self.downloading and self.count > 0:
			# Update the download progress.
			self._progress.set_fraction(self.count/self.filesize)
			#Estimated time remaining:
			# Assume time/totaltime = bytes/totalbytes
			# So, totaltime = time*totalbytes/bytes.
			t = time.time() - self.starttime
			remaining = time_convert((t * self.filesize/self.count - t)*1000)
			self._progress.set_text("%s%% of %s (%s remaining)" %
						(str(round(self.count/self.filesize * 100, 1)),
						 self.readsize, remaining))
		return True
