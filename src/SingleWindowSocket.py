import logging
import os
import socket

from threading import Thread

import gobject

from constants import TV_SOCKET

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
		print TV_SOCKET
		if os.path.exists(TV_SOCKET):
			try:
				self.sendUrl(url)
			except socket.error as msg:
				logging.error("Error:")
				logging.error(msg)
				logging.error("Previous program crashed? Starting server.")
				os.remove(TV_SOCKET)
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
		s.connect(TV_SOCKET)
		s.send(url)
		s.close()

	def server(self):
		"""
		Listens for urls and loads in this process.
		"""
		s = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
		s.settimeout(None) # important! Otherwise default timeout will apply.
		try:
			os.mkdir(os.path.dirname(TV_SOCKET))
		except OSError as e:
			pass
		s.bind(TV_SOCKET)
		while True:
			url = s.recv(65536) # Wait for a url to load.
			if url == 'EXIT':
				os.remove(TV_SOCKET)
				return # End this thread to let program exit normally.
			gobject.idle_add(self.caller.gotoURL, url, True)
			gobject.idle_add(self.caller.window.present)
