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
		s.bind(TV_SOCKET)

		while True:
			url = s.recv(65536) # Wait for a url to load.
			if url == 'EXIT':
				os.remove(DATA_SOCKET)
				return # End this thread to let program exit normally.
			gobject.idle_add(self.caller.gotoURL, url, True)
			gobject.idle_add(self.caller.window.present)
