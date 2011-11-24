import socket, os, gobject
from threading import Thread

SOCKET = os.path.expanduser("~/.tunesviewerLOCK")

class SingleWindowSocket:
	"""
	Called on startup (See last lines of TunesViewer.py).
	A socket file makes sure there is only one instance of the program.
	Otherwise, it will mess up downloads when they both download to the same file.
	"""
	def __init__(self,url,main):
		self.caller = main
		self.RUN = False #When true, start program.
		if os.path.exists(SOCKET):
			try:
				self.sendUrl(url)
			except socket.error, msg:
				print "Error:",msg
				print "Previous program crashed? Starting server."
				os.remove(SOCKET)
				self.RUN = True
				Thread(target=self.server).start()
		else:
			self.RUN = True
			Thread(target=self.server).start()
	
	def sendUrl(self,url):
		"Sends to currently running instance."
		s = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
		s.connect(SOCKET)
		s.send(url)
		s.close()
	
	def server(self):
		"Listens for urls and loads in this process."
		s = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
		s.bind(SOCKET)
		while True:
			url = s.recv(65536) #Wait for a url to load.
			if url=='EXIT':
				os.remove(SOCKET)
				return #End this thread to let program exit normally.
			gobject.idle_add(self.caller.gotoURL, url, True)
			gobject.idle_add(self.caller.window.present)
