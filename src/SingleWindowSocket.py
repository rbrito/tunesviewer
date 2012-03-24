#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 A socket class to ensure only one Tunesviewer instance at one time.

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
import os
import socket

from threading import Thread

import gobject

from constants import DATA_SOCKET, DATA_DIR

class SingleWindowSocket:
	"""
	Called on startup to emulate a singleton.

	A socket file is one of the ways to makes sure there is only one
	instance of the program.  Otherwise, it will mess up downloads when
	they both download to the same file.
	"""
	def __init__(self, url, main):
		self.caller = main
		self.RUN = False # When true, start program.
		try:
			os.makedirs(DATA_DIR)
		except OSError as e:
			# Errno 17 means something already exists
			if e.errno == 17 and os.path.isdir(DATA_DIR):
				# No problem
				pass
			elif e.errno == 17 and not os.path.isdir(DATA_DIR):
				logging.warn('%s already exists, but is not a directory: ' + str(e))
			else:
				logging.warn('Error creating data directory: ' + str(e))

		if os.path.exists(DATA_SOCKET):
			try:
				self.sendUrl(url)
			except socket.error as msg:
				logging.error("Possible stale socket (%s). Starting server." % str(msg))
				os.remove(DATA_SOCKET)
				self.RUN = True
				Thread(target=self.server).start()
		else:
			self.RUN = True
			Thread(target = self.server).start()

	def sendUrl(self, url):
		"""
		Sends to currently running instance.
		"""
		s = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
		s.connect(DATA_SOCKET)
		s.send(url)
		s.close()

	def server(self):
		"""
		Listens for urls and loads in this process.
		"""
		s = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
		s.settimeout(None) # important! Otherwise default timeout will apply.

		try:
			os.mkdir(DATA_DIR)
		except OSError as e:
			if e.errno == 17:
				pass
			else:
				logging.error('Error creating socket: %s.' % str(e))
		s.bind(DATA_SOCKET)

		while True:
			url = s.recv(65536) # Wait for a url to load.
			if url == 'EXIT':
				os.remove(DATA_SOCKET)
				return # End this thread to let program exit normally.
			gobject.idle_add(self.caller.gotoURL, url, True)
			gobject.idle_add(self.caller.window.present)
