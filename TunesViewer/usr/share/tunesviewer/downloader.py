import os
import time
from threading import Thread

import gobject
gobject.threads_init()
import pango
import gtk
from common import *

class Downloader:
	"""A downloader class to download a file."""
	downloading=False
	success=False
	copydir=None
	def __init__(self,icon,url,localfile,opener,downloadWindow):
		self.opener = opener # shared downloader
		self.url = url
		self.localfile = localfile
		self.count = 0 #bytes downloaded
		self.filesize = 0 #total bytes
		#Reference to the download window's class
		self.downloadWindow = downloadWindow
		self.copyfile = downloadWindow.devicedir
		#This downloader has an upper and lower part inside a VBox:
		self.element = gtk.VBox() # main element container
		upper = gtk.HBox(); upper.show()
		lower = gtk.HBox(); lower.show()
		self.element.pack_start(upper,False,False,0)
		self.element.pack_start(lower,False,False,0)
		self.cancelbutton = gtk.Button("Cancel")
		self.cancelbutton.show()
		self.progress = gtk.ProgressBar(adjustment=None)
		self.progress.show()
		ic = gtk.Image()
		ic.set_from_pixbuf(icon)
		iconhold = gtk.EventBox()
		iconhold.connect("button-press-event",self.openit)
		iconhold.show()
		iconhold.add(ic)
		ic.show()
		upper.pack_start(iconhold,False,False,7)
		upper.pack_start(self.progress,True,True,0)
		upper.pack_start(self.cancelbutton,False,False,0)
		name = gtk.Label("Downloading to: %s from: %s" % (localfile, url))
		name.show()
		name.set_ellipsize(pango.ELLIPSIZE_END)
		name.set_selectable(True)
		
		#Add action button
		self.combo = gtk.combo_box_new_text()
		self.combo.append_text("Choose Action:")
		self.combo.append_text("Open File")
		self.combo.append_text("Convert File")
		self.combo.append_text("Copy to Device")
		self.combo.append_text("Delete File")
		self.combo.set_active(0)
		self.combo.connect("changed",self.actionSelect)
		self.combo.show()
		
		self.mediasel = gtk.FileChooserButton("Choose the folder representing the device")
		self.mediasel.set_size_request(100,-1)
		self.mediasel.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
		self.mediasel.connect("current-folder-changed",self.folderChange)
		#self.mediasel.connect("file-set",self.folderChange)
		self.mediasel.hide()
		lower.pack_start(self.combo,False,False,2)
		lower.pack_start(self.mediasel,False,False,2)
		lower.pack_start(name,True,True,0)
		#self.cancelbutton.show()
		if self.copyfile != None:
			self.mediasel.set_current_folder(self.copyfile)
		self.cancelbutton.connect_after("clicked",self.cancel)
		self.progress.show()
		self.element.show()
	
	def openit(self,obj,obj2):
		openDefault(self.localfile);

	def getElement(self):
		"""Return element containing the gui display for this download"""
		return self.element
	
	##
	# Called when the media-device-directory is changed, copies if download is finished.
	def folderChange(self,obj):
		self.copydir = self.mediasel.get_current_folder()
		#Set the selection as the default for new downloads.
		self.downloadWindow.devicedir = self.copydir
		print self.copydir
		if (self.success):
			#Downloaded, so copy it.
			self.copy2device()

	def copy2device(self):
		"""Copy to selected device"""
		if self.copydir == None:
			self.progress.set_text("Select a directory.")
		else:
			#copy it:
			self.progress.set_text("Copying to %s..." % self.copydir)
			import shutil
			try:
				shutil.copy(self.localfile,self.copydir)
			except:
				self.progress.set_text("Error copying to %s." % self.copydir)
			else:
				self.progress.set_text("Copied to %s." % self.copydir)
	
	def actionSelect(self,obj):
		"Called when the downloader's combo-box is changed."
		print self.combo.get_active()
		if self.combo.get_active()==3:
			self.mediasel.show()
		else:
			self.mediasel.hide()
		if self.combo.get_active()==1 and self.success:
			#Open now, finished.
			openDefault(self.localfile)
		elif self.combo.get_active()==2 and self.success:
			import subprocess
			try:
				subprocess.Popen(["soundconverter",self.localfile])
			except OSError:
				msg = gtk.MessageDialog(None,gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR,gtk.BUTTONS_CLOSE, "Soundconverter not found, try installing it with your package manager.")
				msg.run()
				msg.destroy()
		elif self.combo.get_active()==3 and self.success:
			#Try to copy, finished.
			self.copy2device()
		elif (self.combo.get_active()==4):
			print "del"
			self.deletefile()
	
	def cancel(self,obj):
		"Cancels this download. (this is also called by delete command)"
		#if self.downloading:
		self.downloading = False
		self.t.join() #wait for thread to cancel! Destroying this before the thread finishes may cause major crash!
		try:
			os.remove(self.localfile)
			print "removed "+self.localfile
		except:
			print "Removing file failed."
		
		self.element.destroy()
		#Remove all references to this.
		self.downloadWindow.downloaders.remove(self)
		print self.downloadWindow.downloaders
	
	def start(self):
		"Starts download thread"
		self.t = Thread(target=self.downloadThread, args=())
		self.t.start()
	
	def downloadThread(self):
		"This does the actual downloading, it should run as a thread."
		self.downloading = True
		self.starttime = time.time()
		self.progress.set_text("Starting Download...")
		try:
			self.netfile = self.opener.open(self.url)
		except Exception, e:
			self.progress.set_text("Could not open url.")
			print "Error:",e
			if str(e).count("nonnumeric port"):
				#Workaround for bug: http://bugs.python.org/issue979407
				self.progress.set_text("Urllib failed! Opening with browser...");
				openDefault(self.url)#open with browser.
			self.downloading = False
			return
		self.filesize = float(self.netfile.info()['Content-Length'])
		try:
			#print os.path.getsize(self.localfile)
			if self.filesize == os.path.getsize(self.localfile):
				self.progress.set_text("Already downloaded.")
				self.progress.set_fraction(1.0)
				self.cancelbutton.set_sensitive(False)
				self.downloading = False
				self.success = True
				self.netfile.close()
				return
		except Exception, e:
			print "Error:",e
		
		print self.filesize
		try: #downloading:
			next = self.netfile.read(1024)
		except IOError:
			self.progress.set_text("Couldn't start download.")
			self.netfile.close()
			return
		try: #writing to file:
			self.outfile = open(self.localfile,"wb") #to write binary
			self.outfile.write(next)
		except IOError:
			print "ioerr"
			self.progress.set_text("Couldn't write to file, check download-directory.")#+self.localfile)
			self.netfile.close()
			return
		self.readsize = desc(self.filesize) # description of total size.
		self.count = 1024 # Counts downloaded size.
		self.percent=0 # progressbar %
		
		while (len(next)>0 and self.downloading):
			try:
				next = self.netfile.read(1024)
				self.outfile.write(next)
				self.count += len(next)
			except Exception,e:
				self.progress.set_text("Error: "+str(e))
				self.downloading=False
		print "finished one"
		self.outfile.close()
		self.netfile.close()
		if self.downloading: #Not cancelled.
			self.success = True #completed.
			self.progress.set_fraction(1.0)
			self.progress.set_text(self.readsize+" downloaded.")
			if (self.combo.get_active()==1):
				openDefault(self.localfile)
			elif (self.combo.get_active()==3):
				# Copy to Device
				self.copy2device()
				#do something
			print "pre dlnotify"
			self.cancelbutton.set_sensitive(False)
			#running downloadNotify here seems to cause freeze sometimes.
			#self.downloadNotify()
		#else:
			#This set_text isn't needed, it caused error when it was cancelled, and self.progress destroyed.
			#self.progress.set_text("Error")
		self.downloading = False
	
	def deletefile(self):
		filesize = os.path.getsize(self.localfile)
		msg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO,"Are you sure you want to delete this %s file?\n%s" % (desc(filesize),self.localfile))
		answer = msg.run()
		msg.destroy()
		if answer == gtk.RESPONSE_YES:
			print "deleting..."
			self.cancel(None)
		else:
			self.combo.set_active(0)
	
	def update(self):
		if (self.count < self.filesize and self.downloading and self.count > 0):
			# Update the display.
			self.progress.set_fraction(self.count/self.filesize)
			#Estimated time remaining: 
			# Assume time/totaltime = bytes/totalbytes
			# So, totaltime = time*totalbytes/bytes.
			t = time.time() - self.starttime
			remaining = timeFind((t * self.filesize/self.count - t)*1000)
			self.progress.set_text("%s%% of %s (%s remaining)" % (str(round(self.count/self.filesize *100,1)),self.readsize, remaining))
		return True
