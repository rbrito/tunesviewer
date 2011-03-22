import gtk

class FindBox:
	# Advanced search based on http://deimos.apple.com/rsrc/doc/AppleEducation-iTunesUUsersGuide/UsingiTunesUSearch/chapter_10_section_4.html
	def __init__(self,mainwin):
		self.mainwin = mainwin
		self.window = gtk.Dialog("Advanced Search",None,gtk.DIALOG_DESTROY_WITH_PARENT,(gtk.STOCK_FIND,1,gtk.STOCK_CLOSE,0))
		self.window.set_default_response(1)
		self.window.set_icon(self.window.render_icon(gtk.STOCK_FIND, gtk.ICON_SIZE_BUTTON))
		self.window.connect("response",self.response) # Ok/Cancel
		#set up a table: http://www.pygtk.org/pygtk2tutorial/sec-PackingUsingTables.html
		vbox = self.window.get_content_area()
		self.notebook = gtk.Notebook()
		
		itable = gtk.Table(3,2,True)
		#attaching obj,left,right,top,bottom.
		itable.attach(gtk.Label("Title"),0,1,0,1)
		self.title = gtk.Entry()
		self.title.set_activates_default(True)
		itable.attach(self.title,1,2,0,1)
		
		itable.attach(gtk.Label("Academic Institution"),0,1,1,2)
		self.institution = gtk.Entry()
		self.institution.set_activates_default(True)
		itable.attach(self.institution,1,2,1,2)
		
		itable.attach(gtk.Label("Description"),0,1,2,3)
		self.description = gtk.Entry()
		self.description.set_activates_default(True)
		itable.attach(self.description,1,2,2,3)
		
		# -- podcast tab -- 
		podtable = gtk.Table(3,2,True)
		podtable.attach(gtk.Label("Title"),0,1,0,1)
		self.podtitle = gtk.Entry()
		self.podtitle.set_activates_default(True)
		podtable.attach(self.podtitle,1,2,0,1)
		
		podtable.attach(gtk.Label("Author"),0,1,1,2)
		self.podauthor = gtk.Entry()
		self.podauthor.set_activates_default(True)
		podtable.attach(self.podauthor,1,2,1,2)
		
		podtable.attach(gtk.Label("Description"),0,1,2,3)
		self.poddesc = gtk.Entry()
		self.poddesc.set_activates_default(True)
		podtable.attach(self.poddesc,1,2,2,3)
		
		self.notebook.append_page(itable,gtk.Label("iTunesU"))
		self.notebook.append_page(podtable,gtk.Label("Podcasts"))
		vbox.pack_start(self.notebook)
		#vbox.pack_start(table)
		self.window.connect("delete_event",self.delete_event)

	##
	# Cancels close, only hides window.
	def delete_event(self, widget, event, data=None):
		self.window.hide()
		return True # Hide, don't close.
		
	def response(self,obj,value):
		print obj,value
		if value == 0:
			self.window.hide()
		elif value == 1:
			#Use the search
			if self.notebook.get_current_page()==0:
				#&titleTerm= was changed to &allTitle=,this fixes searching, for example title at Yale
				self.mainwin.gotoURL("http://phobos.apple.com/WebObjects/MZSearch.woa/wa/advancedSearch?media=iTunesU&searchButton=submit&allTitle=%s&descriptionTerm=%s&institutionTerm=%s" % (self.title.get_text(),self.description.get_text(),self.institution.get_text()),True)
			else:
				self.mainwin.gotoURL("http://ax.search.itunes.apple.com/WebObjects/MZSearch.woa/wa/advancedSearch?media=podcast&titleTerm=%s&authorTerm=%s&descriptionTerm=%s&genreIndex=&languageTerm=" % (self.podtitle.get_text(),self.podauthor.get_text(),self.poddesc.get_text()),True)

