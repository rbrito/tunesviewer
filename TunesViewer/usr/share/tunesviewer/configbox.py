import os
import ConfigParser
import gtk

class ConfigBox:
	#Initialize variable defaults, these variables are directly accessed by the other classes.
	downloadfolder = os.path.expanduser("~")
	downloadsafe = False
	toolbar = True
	statusbar = False
	throbber = True
	downloadfile = "%n - %a %l%t"
	openers = {".mp3" : "/usr/bin/vlc --http-user-agent=iTunes/10.2 --http-caching=10000", ".m4a" : "/usr/bin/vlc --http-user-agent=iTunes/10.2 --http-caching=10000", ".mov" : "/usr/bin/vlc --http-user-agent=iTunes/10.2 --http-caching=10000", ".mp4" : "/usr/bin/vlc --http-user-agent=iTunes/10.2 --http-caching=10000", ".m4v" : "/usr/bin/vlc --http-user-agent=iTunes/10.2 --http-caching=10000", ".m4p" : "/usr/bin/vlc --http-user-agent=iTunes/10.2 --http-caching=10000", ".aiff" : "/usr/bin/vlc --http-user-agent=iTunes/10.2 --http-caching=10000", ".aif" : "/usr/bin/vlc --http-user-agent=iTunes/10.2 --http-caching=10000", ".aifc" : "/usr/bin/vlc --http-user-agent=iTunes/10.2 --http-caching=10000" }
	podcastprog = "rhythmbox %i"
	defaultcommand=2
	notifyseconds = 7
	iconsizeN = 16
	imagesizeN = 48
	# new for 0.9:
	scaleImage = True
	autoRedirect = True
	# new for 1.0:
	alwaysHTML = ["/artist/","/institution/","/wa/viewGenre","/wa/viewRoom","/wa/viewSeeAll","/wa/viewArtist","/wa/viewTagged","/wa/viewGrouping","://c.itunes.apple.com","://t.co/"]
	
	def __init__(self,mw):
		self.window = gtk.Dialog("TunesViewer Preferences",None,gtk.DIALOG_DESTROY_WITH_PARENT,(gtk.STOCK_OK,1,gtk.STOCK_CANCEL,0))
		self.mainwin = mw
		self.window.set_icon(self.window.render_icon(gtk.STOCK_PREFERENCES, gtk.ICON_SIZE_BUTTON))
		self.window.connect("response",self.response) # Ok/Cancel
		self.window.connect("delete_event",self.delete_event)
		#vbox = self.window.get_content_area()
		dtab = gtk.VBox() # for downloads tab
		vtab = gtk.VBox() # for display tab
		tabs = gtk.Notebook()
		tabs.append_page(dtab,gtk.Label("Downloads"))
		tabs.append_page(vtab,gtk.Label("Display"))
		self.window.get_content_area().pack_start(tabs,True,True,0)
		
		# Start of Download tab
		dhbox = gtk.HBox()
		self.combo = gtk.combo_box_new_text()
		self.combo.append_text("Only Follow links")
		self.combo.append_text("View Streaming or Follow-link")
		self.combo.append_text("Download or Follow-link")
		self.combo.set_active(1)
		dhbox.pack_start(gtk.Label("Default action: "),False,False,0)
		dhbox.pack_start(self.combo,True,True,0)
		dtab.pack_start(dhbox,True,False,0)
		
		self.downloadsel = gtk.FileChooserButton("Select a folder to download to")
		self.downloadsel.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
		hbox = gtk.HBox()
		hbox.pack_start(gtk.Label("Download Folder: "),False,False,0)
		hbox.pack_start(self.downloadsel,True,True,0)
		dtab.pack_start(hbox,True,False,0)
		
		lab = gtk.Label("Download File-name\n(%n=name, %a=artist, %c=comment, %l=length, %t=filetype)")
		lab.set_alignment(0,1)
		dtab.pack_start(lab,True,True,0)
		self.filenamesel = gtk.Entry()
		dtab.pack_start(self.filenamesel,True,False,0)
		self.downloadsafeCheck = gtk.CheckButton("Force safe _filenames for dos/fat filesystems")
		dtab.pack_start(self.downloadsafeCheck,False,False,0)
		
		lab2 = gtk.Label("Default streaming applications:\nUse this for each line:\n.filetype:/path/to/opener")
		lab2.set_alignment(0,1)
		dtab.pack_start(lab2,True,False,0)
		sw = gtk.ScrolledWindow()
		sw.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
		self.viewer = gtk.TextView()
		sw.add(self.viewer)
		dtab.pack_start(sw,True,True,0)
		
		dtab.pack_start(gtk.Label("Podcast manager command: (%u is the url, %i is itpc:// url)"))
		self.podcastprogbox = gtk.combo_box_entry_new_text()#gtk.Entry()
		self.podcastprogbox.append_text("amarok -l %i")
		self.podcastprogbox.append_text("gpodder -s %u")
		self.podcastprogbox.append_text("miro %u")
		self.podcastprogbox.append_text("rhythmbox %i")
		self.podcastprogbox.append_text("banshee %i")
		dtab.pack_start(self.podcastprogbox,True,False,0)
		# End download tab
		
		# Start of Display tab
		self.toolbarCheck = gtk.CheckButton("Show Toolbar")
		self.statusbarCheck = gtk.CheckButton("Show Statusbar")
		self.throbberCheck = gtk.CheckButton("Show Loading icon")
		self.scaleImageCheck = gtk.CheckButton("Scale main image to recommended size")
		self.autoRedirectCheck = gtk.CheckButton("Automatically redirect")
		vtab.pack_start(self.toolbarCheck,False,False,5)
		vtab.pack_start(self.statusbarCheck,False,False,0)
		vtab.pack_start(self.throbberCheck,False, False, 5)
		vtab.pack_start(self.scaleImageCheck,False,False,0)
		vtab.pack_start(self.autoRedirectCheck,False,False,05)
		
		hbox = gtk.HBox()
		hbox.pack_start(gtk.Label("Show download notification for "),False,False,0)
		self.notifyEntry = gtk.Entry()
		hbox.pack_start(self.notifyEntry,False,False,0)
		hbox.pack_start(gtk.Label("seconds."),False,False,0)
		
		vtab.pack_start(hbox,True,False,0)
		
		hbox = gtk.HBox()
		hbox.pack_start(gtk.Label("Icon size: "),False,False,0)
		self.iconsize = gtk.Entry(); self.iconsize.set_width_chars(3)
		hbox.pack_start(self.iconsize,False,False,0)
		hbox.pack_start(gtk.Label(" Image size: "),False,False,0)
		self.imagesize = gtk.Entry(); self.imagesize.set_width_chars(3)
		hbox.pack_start(self.imagesize,False,False,0)
		vtab.pack_start(hbox,True,False,0)
		#vtab.pack_start(gtk.Label("\n"))
		
		sw = gtk.ScrolledWindow()
		sw.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
		vtab.pack_start(gtk.Label("Always request HTML when url includes..."),False,False,0)
		self.alwaysHTMLText = gtk.TextView()
		sw.add(self.alwaysHTMLText)
		vtab.pack_start(sw)
		
		# default program frame:
		defFrame = gtk.Frame(label="Default handler for itms,itmss,itpc protocols:")
		vtab.pack_start(defFrame)
		defv = gtk.VBox()
		defFrame.add(defv)
		setbutton = gtk.Button("Set TunesViewer as default opener")
		setbutton.connect("clicked",self.setdefault)
		defv.pack_start(setbutton,True,False,0)
		self.setOtherProg = gtk.Entry()
		self.setOtherProg.set_text("rhythmbox %s")
		setother = gtk.Button("Set Default")
		setother.connect("clicked",self.setOtherDefault)
		otherHbox = gtk.HBox()
		otherHbox.pack_start(gtk.Label("Other program:"))
		otherHbox.pack_start(self.setOtherProg)
		otherHbox.pack_start(setother)
		defv.pack_start(otherHbox,True,False,0)
		# End display tab
		
		#Set initial configuration:
		self.load_settings()
		
	##
	# Turns text into a dictionary of filetype -> program associations.
	def getopeners(self,text):
		# Map filetype to opener, start new dictionary:
		out = dict()
		list = text.split("\n")
		for i in list:
			if i.find(":")>-1:
				format = i[:i.find(":")]
				opener = i[i.find(":")+1:]
				#print format,opener
				out[format] = opener
		return out
	
	def openertext(self,opener):
		"""Turn a dictionary back to text
		Text is broken into seperate lines, each in the form "filetype:program".
		"""
		out = ""
		for key,value in opener.items():
			out += key+":"+value+"\n"
		return out

	def save_settings(self):
		"""Save the changed values, and write to file"""
		# gui -> variable -> disk
		print "Saving Prefs"
		#First set the variables to the new values:
		text = self.viewer.get_buffer().get_slice(self.viewer.get_buffer().get_start_iter(),self.viewer.get_buffer().get_end_iter())
		self.openers = self.getopeners(text)
		self.downloadfile = self.filenamesel.get_text()
		self.downloadsafe = self.downloadsafeCheck.get_active()
		self.toolbar = self.toolbarCheck.get_active()
		self.statusbar = self.statusbarCheck.get_active()
		self.autoRedirect = self.autoRedirectCheck.get_active()
		self.scaleImage = self.scaleImageCheck.get_active()
		self.throbber = self.throbberCheck.get_active()
		self.downloadfolder = self.downloadsel.get_current_folder()
		if self.downloadfolder == None:
			self.downloadfolder = os.path.expanduser("~")
		self.defaultcommand = self.combo.get_active()
		self.notifyseconds = int(self.notifyEntry.get_text())
		self.podcastprog = self.podcastprogbox.child.get_text()
		try:
			self.iconsizeN = int(self.iconsize.get_text())
			self.imagesizeN = int(self.imagesize.get_text())
		except Exception,e:
			print "Couldn't convert icon size:",e
		buf = self.alwaysHTMLText.get_buffer()
		self.alwaysHTML = buf.get_slice(buf.get_start_iter(),buf.get_end_iter()).split("\n")
		
		#Then write config file:
		config = ConfigParser.ConfigParser()
		sec = "TunesViewerPrefs"
		config.add_section(sec)
		config.set(sec,"DefaultMode",self.defaultcommand)
		config.set(sec,"Openers",text)
		config.set(sec,"DownloadFolder",self.downloadfolder)
		config.set(sec,"DownloadFile",self.downloadfile)
		config.set(sec,"DownloadSafeFilename",self.downloadsafe)
		config.set(sec,"Toolbar",self.toolbar)
		config.set(sec,"Statusbar",self.statusbar)
		config.set(sec,"NotifySeconds",str(self.notifyseconds))
		config.set(sec,"PodcastProg",self.podcastprog)
		config.set(sec,"ImageSize",self.imagesizeN)
		config.set(sec,"IconSize",self.iconsizeN)
		config.set(sec,"AutoRedirect",self.autoRedirect)
		config.set(sec,"ScaleImage",self.scaleImage)
		config.set(sec,"alwaysHTML-URLs", "\n".join(self.alwaysHTML))
		config.set(sec,"throbber",self.throbber)
		config.write(open(os.path.expanduser("~/.tunesviewerprefs"),"w"))
		self.setVisibility()

	def load_settings(self):
		"""Try to load settings from file, then update display"""
		# disk -> variables -> gui
		print "Loading Prefs"
		first = False
		if os.path.isfile(os.path.expanduser("~/.tunesviewerprefs")):
			try:
				#Load to the main variables:
				config = ConfigParser.ConfigParser()
				config.read(os.path.expanduser("~/.tunesviewerprefs"))
				sec = "TunesViewerPrefs"
				self.defaultcommand = config.get(sec,"DefaultMode")
				self.openers = self.getopeners(config.get(sec,"Openers"))
				folder = config.get(sec,"DownloadFolder")
				if os.path.isdir(folder):
					self.downloadfolder = folder
				else:
					print "Not a valid directory: %s" % folder
				self.downloadfile = config.get(sec,"DownloadFile")
				self.downloadsafe = (config.get(sec,"DownloadSafeFilename") == "True")
				self.notifyseconds = int(config.get(sec,"NotifySeconds"))
				self.podcastprog = config.get(sec,"PodcastProg")
				self.imagesizeN = int(config.get(sec,"ImageSize"))
				self.iconsizeN = int(config.get(sec,"IconSize"))
				self.toolbar = (config.get(sec,"Toolbar")=="True")
				self.statusbar = (config.get(sec,"Statusbar")=="True")
				self.scaleImage = (config.get(sec,"ScaleImage")=="True")
				self.autoRedirect = (config.get(sec,"AutoRedirect")=="True")
				self.alwaysHTML = config.get(sec,"alwaysHTML-URLs").split("\n")
				self.throbber = (config.get(sec,"Throbber")=="True")
			except Exception,e:
				print "Load-settings error:",e
		else:
			first = True
		
		#Load to the screen:
		self.downloadsel.set_current_folder(self.downloadfolder)
		#unfortunately these two are not the same:
		#print self.downloadfolder
		#print self.downloadsel.get_current_folder()
		self.viewer.get_buffer().set_text(self.openertext(self.openers))
		self.downloadsafeCheck.set_active(self.downloadsafe)
		self.toolbarCheck.set_active(self.toolbar)
		self.statusbarCheck.set_active(self.statusbar)
		self.scaleImageCheck.set_active(self.scaleImage)
		self.autoRedirectCheck.set_active(self.autoRedirect)
		self.throbberCheck.set_active(self.throbber)
		self.filenamesel.set_text(self.downloadfile)
		self.combo.set_active(int(self.defaultcommand))
		self.notifyEntry.set_text(str(self.notifyseconds))
		self.podcastprogbox.child.set_text(self.podcastprog)
		self.imagesize.set_text(str(self.imagesizeN))
		self.iconsize.set_text(str(self.iconsizeN))
		self.alwaysHTMLText.get_buffer().set_text("\n".join(self.alwaysHTML))
		#print self.defaultcommand
		if first:
			self.first_setup()
		self.setVisibility()
	
	def setVisibility(self):
		if self.toolbar:
			self.mainwin.toolbar.show()
		else:
			self.mainwin.toolbar.hide()
		if self.statusbar:
			self.mainwin.statusbar.show()
		else:
			self.mainwin.statusbar.hide()
	
	##
	# Cancels close, only hides window.
	def delete_event(self, widget, event, data=None):
		self.window.hide()
		return True # Hide, don't close.
		
	def first_setup(self):
		import subprocess
		try:
			self.save_settings()
			subprocess.Popen(["/usr/share/tunesviewer/firstsetup.py"])
		except Exception,e:
			print "First-time setup error:",e
		
	##
	# Saves or loads settings when ok or cancel or close is selected.
	def response(self,obj,value):
		if value==1:
			self.save_settings()
		else:
			self.load_settings()
		#Done, call the hide-window event:
		self.delete_event(None,None,None)
		
	##
	# Sets this as the default protocol opener.
	def setdefault(self,obj):
		try:
			file("/usr/bin/tunesviewer")
		except IOError:
			msg = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE,
				"The link /usr/bin/tunesviewer does not exist.")
			msg.run()
			msg.destroy()
			return
		# Try setting the protocol defaults:
		err = 0
		err += self.setdefaultprotocol("itms","/usr/bin/tunesviewer %s")
		err += self.setdefaultprotocol("itmss","/usr/bin/tunesviewer %s")
		err += self.setdefaultprotocol("itpc","/usr/bin/tunesviewer %s")
		if (err):
			msg = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE,
				"Unable to set defaults.")
			msg.run()
			msg.destroy()
		else:
			msg = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL, gtk.MESSAGE_INFO, gtk.BUTTONS_CLOSE,
				"Default set. Now you should be able to open itunesU with this program using a web browser.")
			msg.run()
			msg.destroy()
			
	def setOtherDefault(self,obj):
		err = 0
		err += self.setdefaultprotocol("itms",self.setOtherProg.get_text());
		err += self.setdefaultprotocol("itmss",self.setOtherProg.get_text());
		err += self.setdefaultprotocol("itpc",self.setOtherProg.get_text());
		if (err):
			msg = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE,
				"Unable to set defaults.")
			msg.run()
			msg.destroy()

	def setdefaultprotocol(self,protocol,program):
		"""Try to set program as default protocol handler
		Return True if there is an error.
		"""
		err = os.system("gconftool-2 -s /desktop/gnome/url-handlers/"+protocol+"/enabled --type Boolean true")
		err2 = os.system("gconftool-2 -s /desktop/gnome/url-handlers/"+protocol+"/command '"+program+"' --type String")
		return (err or err2)
		
