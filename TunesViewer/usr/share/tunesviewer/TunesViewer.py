#!/usr/bin/env python

# TunesViewer
# Small, easy-to-use tool to access iTunesU and podcast media.
# Designed by Luke 2009 - 2011
# Loading-icon is from mozilla's throbber icon.

#Licensed under Apache license
#Unless required by applicable law or agreed to in writing, software
#distributed under the License is distributed on an "AS IS" BASIS,
#WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#See the License for the specific language governing permissions and
#limitations under the License.

#Import the standard python libraries needed:
import urllib, urllib2, cookielib
import sys, os, tempfile, subprocess, time
from threading import Thread
import gc, re

#Import GTK for gui.
import gobject
gobject.threads_init()
import pygtk, pango, glib
pygtk.require('2.0')
import gtk
import webkit

from configbox import ConfigBox
from findinpagebox import FindInPageBox
from downloadbox import DownloadBox
from findbox import FindBox
from itemdetails import ItemDetails
from common import *

try:
	from lxml import etree
except ImportError, e:
	print "This program requires LXML, but it is not installed."
	msg = gtk.MessageDialog(None,gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR,gtk.BUTTONS_CLOSE, "This program requires LXML, but it is not installed.\nPlease install python-lxml with your system's package manager, or follow the installation instructions at:\nhttp://codespeak.net/lxml/index.html#download")
	msg.run()
	msg.destroy()
	sys.exit(1)

#Set download timeout to wait a while before quitting:
import socket
socket.setdefaulttimeout(20)


def resource_cb(view, frame, resource, request, response):
	#print dir(request)
	#if request.get_property('message'): 
	# request.get_property('message').set_data('User-agent','iTunes/10.1')
	import urllib2
	uri = request.get_uri()
	if not(uri.startswith("data:")) and not(uri.endswith('jsz')):
		#if (uri.endswith("htm")):
		import urllib2
		opener = urllib2.build_opener();
		opener.addheaders = [('User-agent', 'iTunes/10.2'),("X-Apple-Store-Front","143441-1,12"),("X-Apple-Tz:","-21600")]
		page = opener.open(uri);
		if page.info().gettype().count("text/html"):
			data = page.read();
			request.set_uri("data:"+page.info().gettype()+","+data)



##
# Tries to get the array element of the dom, returns None if it doesn't exist.
def getItemsArray(dom):
	array = None
	els = dom.xpath("/Document/TrackList/plist/dict/key")#isinstance(i.tag,str) and i.tag == "key" and 
	for i in els: #all childnodes:
		if (i.text=="items"):
			array = i.getnext()
	return array


##
# Removes nodes like <Test comparison="lt" value="7.1" property="iTunes version">
# Including these would make many duplicates.
def removeOldData(dom):
	tests = dom.xpath("//Test") # get all <test> elements
	for i in tests:
		if (i.get("comparison")=="lt" or (i.get("comparison") and i.get("comparison").find("less")>-1)):
			i.getparent().remove(i)

def htmlentitydecode(s):
	if s: # based on http://wiki.python.org/moin/EscapingHtml
		from htmlentitydefs import name2codepoint
		return (re.sub('&(%s);' % '|'.join(name2codepoint), 
				lambda m: unichr(name2codepoint[m.group(1)]), s)).replace("&apos;","'")
	else:
		return ""


##
# Gets all text content of the node.
def textContent(element):
	#out = element.text
	#for i in element.itertext(): # includes comment nodes... :(
	#	out += i
	#return out
	out = []
	if type(element).__name__=="_Element":
		if element.text:
			out.append( element.text )
		for i in element:
			out.append(textContent(i))
			if i.tail:
				out.append(i.tail)
	return "".join(out)

class TunesViewer:
	source= "" # full xml source
	url= "" # page url
	podcast= "" #podcast url
	downloading=False #when true, don't download again, freezing prog. (Enforces having ONE gotoURL)
	downloadError=""
	infoboxes = []
	redirectPages = []
	
	tempcache = tempfile.mkdtemp("TunesViewer") # for cached images etc. This directory will be REMOVED at exit.
	cachemap = {}
	nextcachename = 1 #filename for next file
	
	# Lists can be used as stacks: just use list.append(...) and list.pop()
	# Stacks for back and forward buttons:
	backStack = []
	forwardStack = []

	#Initializes the main window
	def __init__(self, dname = None):
		self.downloadbox = DownloadBox(self)# Only one downloadbox is constructed
		self.findbox = FindBox(self)
		self.findInPage = FindInPageBox()
		self.findInPage.connect('find', self.find_in_page_cb)
		# Create a new window, initialize all widgets:
		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.window.set_title("TunesViewer")
		self.window.set_size_request(350, 350) #minimum
		self.window.resize(580,500)
		self.window.connect("delete_event", self.delete_event)
		# set add drag-drop, based on: http://stackoverflow.com/questions/1219863/python-gtk-drag-and-drop-get-url
		self.window.drag_dest_set(0, [], 0)
		self.window.connect('drag_motion', self.motion_cb)
		self.window.connect('drag_drop', self.drop_cb)
		self.window.connect('drag_data_received', self.got_data_cb)
		
		try:
			pixbuf = gtk.gdk.pixbuf_new_from_file('/usr/share/icons/hicolor/scalable/apps/tunesview.svg')
			self.window.set_icon(pixbuf)
		except:
			print "Couldn't load window icon."
		
		# will hold icon, title, artist, time, type, comment, releasedate,datemodified, gotourl, previewurl, imageurl, itemid.
		self.liststore = gtk.ListStore(gtk.gdk.Pixbuf,str,str,str,str,str,str,str,str,str,str,str)
		
		#Liststore goes in a TreeView inside a Scrolledwindow:
		self.treeview = gtk.TreeView(model=self.liststore)
		self.treeview.set_enable_search(True)
		self.scrolledwindow = gtk.ScrolledWindow()
		self.scrolledwindow.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
		self.scrolledwindow.add(self.treeview)
		
		cell = gtk.CellRendererText()
		#Set the cell-renderer to ellipsize ... at end.
		cell.set_property("ellipsize",pango.ELLIPSIZE_END)
		#Set single-paragraph-mode, no huge multiline display rows.
		cell.set_property("single-paragraph-mode",True)
		
		col = gtk.TreeViewColumn(" ")
		#col.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
		pb = gtk.CellRendererPixbuf()
		col.pack_start(pb)
		col.add_attribute(pb,'pixbuf',0)
		self.treeview.append_column(col)
		
		# Now each column is created and added:
		col = gtk.TreeViewColumn("Name")
		col.pack_start(cell)
		col.add_attribute(cell,'markup',1) # because markup, not text, is required in tooltip.
		col.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
		col.set_fixed_width(200)
		col.set_expand(True)
		col.set_resizable(True)
		col.set_reorderable(True)
		#col.set_max_width(100)
		self.treeview.set_search_column(1)
		col.set_sort_column_id(1)
		#col.set_property('resizable',1)
		self.treeview.append_column(col)
		self.treeview.set_tooltip_column(1) #needs markup, not text
		
		col = gtk.TreeViewColumn("Author")
		col.pack_start(cell)
		col.add_attribute(cell,'text',2)
		col.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
		#col.set_expand(True)
		col.set_fixed_width(150)
		col.set_resizable(True)
		col.set_reorderable(True)
		self.treeview.set_search_column(2)
		col.set_sort_column_id(2)
		self.treeview.append_column(col)
		
		col = gtk.TreeViewColumn("Time")
		col.pack_start(cell)
		col.add_attribute(cell,'text',3)
		col.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
		col.set_resizable(True)
		col.set_reorderable(True)
		self.treeview.set_search_column(3)
		col.set_sort_column_id(3)
		self.treeview.append_column(col)
		
		col = gtk.TreeViewColumn("Type")
		col.pack_start(cell)
		col.add_attribute(cell,'text',4)
		col.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
		col.set_resizable(True)
		col.set_reorderable(True)
		self.treeview.set_search_column(4)
		col.set_sort_column_id(4)
		self.treeview.append_column(col)
		
		col = gtk.TreeViewColumn("Comment")
		col.pack_start(cell)
		col.add_attribute(cell,'text',5)
		col.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
		col.set_expand(True)
		col.set_min_width(100)
		col.set_resizable(True)
		col.set_reorderable(True)
		self.treeview.set_search_column(5)
		col.set_sort_column_id(5)
		self.treeview.append_column(col)
		self.treeview.set_search_column(0)
		#gtk.Settings.
		
		col = gtk.TreeViewColumn("Release Date")
		col.pack_start(cell)
		col.add_attribute(cell,'text',6)
		col.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
		col.set_resizable(True)
		col.set_reorderable(True)
		self.treeview.set_search_column(6)
		col.set_sort_column_id(6)
		self.treeview.append_column(col)
		self.treeview.set_search_column(0)
		
		col = gtk.TreeViewColumn("Modified Date")
		col.pack_start(cell)
		col.add_attribute(cell,'text',7)
		col.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
		col.set_resizable(True)
		col.set_reorderable(True)
		self.treeview.set_search_column(7)
		col.set_sort_column_id(7)
		self.treeview.append_column(col)
		self.treeview.set_search_column(1)
		
		self.treeview.connect("row-activated",self.rowSelected)
		self.treeview.get_selection().set_select_function(self.treesel,data=None)
		
		# Make the locationbar-searchbar:
		locationbox = gtk.HBox()
		self.modecombo = gtk.combo_box_new_text()
		self.modecombo.append_text("Url:")
		self.modecombo.append_text("iTunesU Search:")
		self.modecombo.append_text("Podcast Search:")
		self.modecombo.set_active(1)
		self.modecombo.connect("changed",self.combomodechanged)
		locationbox.pack_start(self.modecombo,False,False,0)
		self.locationentry = gtk.Entry()
		self.locationentry.connect("activate",self.gobutton)
		locationbox.pack_start(self.locationentry,True,True,0)
		gobutton = gtk.Button(label="Go", stock=gtk.STOCK_OK)
		# set GO label (http://www.harshj.com/2007/11/17/setting-a-custom-label-for-a-button-with-stock-icon-in-pygtk/)
		try:
			gobutton.get_children()[0].get_children()[0].get_children()[1].set_label("G_O")
		except:
			pass
		gobutton.connect("clicked",self.gobutton)
		locationbox.pack_start(gobutton,False,False,0)
		prefheight = self.locationentry.size_request()[1]
		#Default button is very tall, try to make buttons the same height as the text box:
		#print gobutton.size_request()
		gobutton.set_size_request(-1,prefheight)
		
		# Now make menus: http://zetcode.com/tutorials/pygtktutorial/menus/
		agr = gtk.AccelGroup()
		self.window.add_accel_group(agr)
		menubox = gtk.HBox()
		mb = gtk.MenuBar()
		menubox.pack_start(mb,1,1,0)
		self.throbber = gtk.Image()
		#Based on firefox throbber:
		#self.throbber.set_from_animation(gtk.gdk.PixbufAnimation(gtk.icon_theme_get_default().lookup_icon("process-working",16,0).get_filename()))
		#self.throbber.set_from_animation(gtk.gdk.PixbufAnimation(gtk.icon_theme_get_default().lookup_icon("process-working",16,0).get_filename()))
		self.throbber.set_from_animation(gtk.gdk.PixbufAnimation('/usr/share/tunesviewer/Throbber.gif'))
		
		#print gtk.icon_theme_get_default().lookup_icon("gnome-spinner",16,0).get_filename()
		menubox.pack_start(self.throbber,expand=False)
		filemenu = gtk.Menu()
		filem = gtk.MenuItem("_File")
		filem.set_submenu(filemenu)
		aSearch = gtk.ImageMenuItem(gtk.STOCK_FIND)
		aSearch.set_label("Advanced _Search...")
		aSearch.connect("activate",self.advancedSearch)
		key, mod = gtk.accelerator_parse("<Ctrl>K")
		aSearch.add_accelerator("activate", agr, key, mod, gtk.ACCEL_VISIBLE)
		filemenu.append(aSearch)
		pSearch = gtk.ImageMenuItem(gtk.STOCK_FIND)
		pSearch.set_label("Find on Current Page...")
		pSearch.connect("activate",self.searchCurrent)
		key, mod = gtk.accelerator_parse("<Ctrl>F")
		pSearch.add_accelerator("activate",agr, key, mod, gtk.ACCEL_VISIBLE)
		filemenu.append(pSearch)
		filemenu.append(gtk.SeparatorMenuItem())
		exit = gtk.ImageMenuItem(gtk.STOCK_QUIT)
		exit.set_label("E_xit")
		exit.connect("activate", self.exitclicked)
		filemenu.append(exit)
		
		editmenu = gtk.Menu()
		editm = gtk.MenuItem("_Edit")
		editm.set_submenu(editmenu)
		copym = gtk.ImageMenuItem(gtk.STOCK_COPY)
		copym.set_label("_Copy Normal Podcast Url")
		copym.connect("activate",self.copyrss)
		key, mod = gtk.accelerator_parse("<Ctrl><Shift>C")
		copym.add_accelerator("activate", agr, key, mod, gtk.ACCEL_VISIBLE)
		editmenu.append(copym)
		pastem = gtk.ImageMenuItem(gtk.STOCK_PASTE)
		pastem.set_label("Paste and _Goto Url")
		pastem.connect("activate",self.pastego)
		key, mod = gtk.accelerator_parse("<Ctrl><Shift>V")
		pastem.add_accelerator("activate", agr, key, mod, gtk.ACCEL_VISIBLE)
		editmenu.append(pastem)
		editmenu.append(gtk.SeparatorMenuItem())
		prefs = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)
		prefs.connect("activate", self.openprefs)
		editmenu.append(prefs)
		
		viewmenu = gtk.Menu()
		viewm = gtk.MenuItem("_View")
		viewm.set_submenu(viewmenu)
		self.htmlmode = gtk.CheckMenuItem("Request _HTML Mode")
		viewmenu.append(self.htmlmode)
		viewmenu.append(gtk.SeparatorMenuItem())
		viewdownloads = gtk.MenuItem("Show _Downloads")
		viewdownloads.connect("activate",self.viewDownloads)
		viewmenu.append(viewdownloads)
		viewdir = gtk.ImageMenuItem(gtk.STOCK_DIRECTORY)
		viewdir.set_label("Downloads Directory")
		viewdir.connect("activate",self.openDownloadDir)
		viewmenu.append(viewdir)
		viewmenu.append(gtk.SeparatorMenuItem())
		viewsource = gtk.MenuItem("Page _Source")
		key, mod = gtk.accelerator_parse("<Ctrl>U")
		viewsource.add_accelerator("activate", agr, key, mod, gtk.ACCEL_VISIBLE)
		viewsource.connect("activate",self.viewsource)
		viewmenu.append(viewsource)
		viewcookie = gtk.MenuItem("_Cookies")
		viewcookie.connect("activate",self.viewCookie)
		viewmenu.append(viewcookie)
		viewprop = gtk.ImageMenuItem(gtk.STOCK_INFO)
		viewprop.set_label("Selection _Info")
		key, mod = gtk.accelerator_parse("<Ctrl>I")
		viewprop.add_accelerator("activate",agr,key,mod,gtk.ACCEL_VISIBLE)
		viewmenu.append(viewprop)
		viewprop.connect("activate",self.viewprop)
		
		gomenu = gtk.Menu()
		gom = gtk.MenuItem("_Go")
		gom.set_submenu(gomenu)
		
		#make the directory links
		self.itunesuDir = gtk.Menu()
		itunesu = gtk.MenuItem("iTunes_U")
		itunesu.set_submenu(self.itunesuDir)
		#self.itunesuDir.append(gtk.MenuItem("directory here"))
		gomenu.append(itunesu)
		self.podcastDir = gtk.Menu()
		podcasts = gtk.MenuItem("_Podcasts")
		podcasts.set_submenu(self.podcastDir)
		#self.podcastDir.append(gtk.MenuItem("directory here"))
		gomenu.append(podcasts)
		
		back = gtk.ImageMenuItem(gtk.STOCK_GO_BACK)
		key, mod = gtk.accelerator_parse("<Alt>Left")
		back.add_accelerator("activate", agr, key, 
			mod, gtk.ACCEL_VISIBLE)
		back.connect("activate",self.goBack)
		gomenu.append(back)
		forward = gtk.ImageMenuItem(gtk.STOCK_GO_FORWARD)
		key, mod = gtk.accelerator_parse("<Alt>Right")
		forward.add_accelerator("activate", agr, key, 
			mod, gtk.ACCEL_VISIBLE)
		forward.connect("activate",self.goForward)
		gomenu.append(forward)
		refresh = gtk.ImageMenuItem(gtk.STOCK_REFRESH)
		key, mod = gtk.accelerator_parse("F5")
		refresh.add_accelerator("activate", agr, key, 
			mod, gtk.ACCEL_VISIBLE)
		refresh.connect("activate",self.refresh)
		gomenu.append(refresh)
		stop = gtk.ImageMenuItem(gtk.STOCK_STOP)
		key, mod = gtk.accelerator_parse("Escape")
		stop.add_accelerator("activate", agr, key, 
			mod, gtk.ACCEL_VISIBLE)
		stop.connect("activate",self.stop)
		gomenu.append(stop)
		
		itemmenu = gtk.Menu()
		itemm = gtk.MenuItem("_Actions")
		itemm.set_submenu(itemmenu)
		follow = gtk.ImageMenuItem(gtk.STOCK_JUMP_TO)
		follow.connect("activate", self.followlink)
		follow.set_label("_Goto Link")
		key, mod = gtk.accelerator_parse("<Ctrl>G")
		follow.add_accelerator("activate", agr, key, 
			mod, gtk.ACCEL_VISIBLE)
		itemmenu.append(follow)
		playview = gtk.ImageMenuItem(gtk.STOCK_MEDIA_PLAY)
		playview.set_label("_Play/View File")
		playview.connect("activate", self.playview)
		key, mod = gtk.accelerator_parse("<Ctrl>P")
		playview.add_accelerator("activate", agr, key, 
			mod, gtk.ACCEL_VISIBLE)
		itemmenu.append(playview)
		download = gtk.ImageMenuItem(gtk.STOCK_SAVE)
		download.set_label("_Download File")
		download.connect("activate", self.download)
		key, mod = gtk.accelerator_parse("<Ctrl>D")
		download.add_accelerator("activate", agr, key, 
			mod, gtk.ACCEL_VISIBLE)
		itemmenu.append(download)
		self.addpodmenu = gtk.ImageMenuItem(gtk.STOCK_ADD)
		self.addpodmenu.set_label("_Add Page to Podcast Manager")
		self.addpodmenu.connect("activate",self.addPod)
		itemmenu.append(self.addpodmenu)
		
		# right click menu
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
		rcinfo.connect("activate",self.viewprop)
		rcinfo.set_label("Item _Info")
		rcinfo.show()
		self.rcmenu.append(rcinfo)
		self.rcmenu.append(self.rcgoto)
		self.rcmenu.append(self.rccopy)
		self.rcmenu.append(self.rcplay)
		self.rcmenu.append(self.rcdownload)
		self.treeview.connect("button_press_event", self.treeclick)
		
		helpmenu = gtk.Menu()
		helpm = gtk.MenuItem("_Help")
		helpm.set_submenu(helpmenu)
		helpitem = gtk.MenuItem("_Help")
		helpitem.connect("activate",self.showHelp)
		helpupdate = gtk.MenuItem("Check for _Update...")
		helpupdate.connect("activate",self.progUpdate)
		helpreport = gtk.MenuItem("Report a Bug...")
		helpreport.connect("activate",self.bugReport)
		helpabout = gtk.MenuItem("About")
		helpabout.connect("activate",self.showAbout)
		helpmenu.append(helpitem)
		helpmenu.append(helpupdate)
		helpmenu.append(helpreport)
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
		self.locationhbox.pack_start(gtk.Label(" Media files on this page: "),False,False,0)
		#This will hold references to the buttons in this box:
		#self.locationbuttons = [] not needed
		self.notebook = gtk.Notebook()
		self.notebook.set_property("enable-popup",True)
		self.notebook.connect_after("switch-page",self.tabChange) #important to connect-after! Normal connect will cause display problems and sometimes segfault.
		self.notebook.set_scrollable(True)
		self.notebookbox = gtk.HBox()
		self.notebookbox.pack_start(self.notebook,True,True,0)
		#for i in range(5): #test tabs:
			#label = gtk.Label("Page %d kakl" % (i+1))
			#if i==3:
				#label.set_markup("<b><i>Page </i></b>")
			#a = gtk.Label()
			#a.set_size_request(0, 0)
			#self.notebook.append_page(a, label)
		
		bottom = gtk.VBox()
		bottom.pack_start(self.locationhbox,False,False,2)
		bottom.pack_start(self.notebookbox,False,False,2)
		bottom.pack_start(self.scrolledwindow,True,True,2)

		# adjustable panel with description box above listing:
		vpaned = gtk.VPaned()
		vpaned.set_position(125)
		sw = gtk.ScrolledWindow()
		sw.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
		self.descView = webkit.WebView()#gtk.TextView() #TODO: Change to webkit.WebView.
		self.descView.connect("load-finished",self.webKitLoaded)
		self.descView.connect("navigation-policy-decision-requested",self.webkitGo)
		self.descView.connect("resource-request-starting",self.webkitReqStart)
		#resource_cb)#
		sw.add(self.descView)
		vpaned.add1(sw)
		vpaned.add2(bottom)
		
		self.toolbar = gtk.Toolbar()
		self.tbBack = gtk.ToolButton(gtk.STOCK_GO_BACK)
		self.tbBack.connect("clicked",self.goBack)
		self.tbBack.set_tooltip_text("Back")
		self.toolbar.insert(self.tbBack,-1)
		self.tbForward = gtk.ToolButton(gtk.STOCK_GO_FORWARD)
		self.tbForward.connect("clicked",self.goForward)
		self.tbForward.set_tooltip_text("Forward")
		self.toolbar.insert(self.tbForward,-1)
		tbRefresh = gtk.ToolButton(gtk.STOCK_REFRESH)
		tbRefresh.connect("clicked",self.refresh)
		tbRefresh.set_tooltip_text("Refresh Page")
		self.toolbar.insert(tbRefresh,-1)
		self.tbStop = gtk.ToolButton(gtk.STOCK_STOP)
		self.tbStop.connect("clicked",self.stop)
		self.tbStop.set_tooltip_text("Stop")
		self.toolbar.insert(self.tbStop,-1)
		
		self.toolbar.insert(gtk.SeparatorToolItem(),-1)
		
		
		opendl = gtk.ToolButton(gtk.STOCK_DIRECTORY)
		opendl.set_tooltip_text("Open Downloads Directory")
		opendl.connect("clicked",self.openDownloadDir)
		self.toolbar.insert(opendl,-1)
		self.toolbar.insert(gtk.SeparatorToolItem(),-1)
		
		self.tbInfo = gtk.ToolButton(gtk.STOCK_INFO)
		self.tbInfo.connect("clicked",self.viewprop)
		self.tbInfo.set_tooltip_text("View Selection Information")
		self.toolbar.insert(self.tbInfo,-1)
		self.tbGoto = gtk.ToolButton(gtk.STOCK_JUMP_TO)
		self.tbGoto.connect("clicked",self.followlink)
		self.tbGoto.set_tooltip_text("Goto Link")
		self.toolbar.insert(self.tbGoto,-1)
		self.tbPlay = gtk.ToolButton(gtk.STOCK_MEDIA_PLAY)
		self.tbPlay.connect("clicked",self.playview)
		self.tbPlay.set_tooltip_text("Play/View File")
		self.toolbar.insert(self.tbPlay,-1)
		self.tbDownload = gtk.ToolButton(gtk.STOCK_SAVE)
		self.tbDownload.connect("clicked",self.download)
		self.tbDownload.set_tooltip_text("Download File")
		self.toolbar.insert(self.tbDownload,-1)
		self.toolbar.insert(gtk.SeparatorToolItem(),-1)
		
		self.tbCopy = gtk.ToolButton(gtk.STOCK_COPY)
		self.tbCopy.connect("clicked",self.copyrss)
		self.tbCopy.set_tooltip_text("Copy Normal Podcast Url")
		self.toolbar.insert(self.tbCopy,-1)
		self.tbAddPod = gtk.ToolButton(gtk.STOCK_ADD)
		self.tbAddPod.set_tooltip_text("Add to Podcast Manager")
		self.tbAddPod.connect("clicked",self.addPod)
		self.toolbar.insert(self.tbAddPod,-1)
		self.toolbar.insert(gtk.SeparatorToolItem(),-1)
		tbFind = gtk.ToolButton(gtk.STOCK_FIND)
		
		tbZO = gtk.ToolButton(gtk.STOCK_ZOOM_OUT)
		tbZO.connect("clicked",self.webkitZO)
		self.toolbar.insert(tbZO,-1)
		tbZI = gtk.ToolButton(gtk.STOCK_ZOOM_IN)
		tbZI.connect("clicked",self.webkitZI)
		self.toolbar.insert(tbZI,-1)
		self.toolbar.insert(gtk.SeparatorToolItem(),-1)
		
		tbFind.set_tooltip_text("Advanced Search")
		tbFind.connect("clicked",self.advancedSearch)
		self.toolbar.insert(tbFind,-1)
		spacer = gtk.SeparatorToolItem()
		spacer.set_draw(0); spacer.set_expand(1)
		self.toolbar.insert(spacer,-1)
		self.tbAuth = gtk.ToolButton(gtk.STOCK_DIALOG_AUTHENTICATION)
		self.toolbar.insert(self.tbAuth,-1)
		
		self.toolbar.set_icon_size(gtk.ICON_SIZE_SMALL_TOOLBAR)

		# All those objects go in the main vbox:
		self.mainvbox = gtk.VBox()
		self.mainvbox.pack_start(menubox, False, False, 0)
		self.mainvbox.pack_start(self.toolbar, False, False, 0)
		self.mainvbox.pack_start(locationbox,False,False,0)
		#self.mainvbox.pack_start(self.scrolledwindow, True, True, 0)
		self.mainvbox.pack_start(vpaned, True, True, 0)
		self.statusbar = gtk.Label()
		self.statusbar.set_justify(gtk.JUSTIFY_LEFT)
		self.mainvbox.pack_start(self.statusbar,False,True,0)
		#self.window.set_property('allow-shrink',True)

		self.updateBackForward()
		self.window.add(self.mainvbox)
		self.window.show_all()
		
		#Start focus on the entry:
		self.window.set_focus(self.locationentry)
		
		# Disable the copy/add podcast until valid podcast is here.
		self.tbCopy.set_sensitive(self.podcast!="")
		self.tbAddPod.set_sensitive(self.podcast!="")
		self.addpodmenu.set_sensitive(self.podcast!="")
		self.tbAuth.hide()
		
		self.noneSelected()
		
		self.config = ConfigBox(self) # Only one configuration box, it has reference back to here to change toolbar,statusbar settings.
		
		# Set up the main url handler with downloading and cookies:
		self.cj = cookielib.CookieJar()
		self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
		self.opener.addheaders = [('User-agent', 'iTunes/10.2')]
		#Load in background...
		t = Thread(target=self.getDirectory, args=())
		t.start()
		
	def webkitZI(self,obj):
		self.descView.zoom_in()
		
	def webkitZO(self,obj):
		self.descView.zoom_out()
		
	def webkitGo(self,view,frame,net_req,nav_act,pol_dec):
		#if (self.noload):
		#	print "noload"
		#	return True;
		print "webkit-request."
		if self.webkitLoading==False:
			print "Noload" #Don't load in browser, let this program download it...
			print net_req.get_uri()
			self.gotoURL(net_req.get_uri(),True);
			return True
			
	def webkitReqStart(self, webView, webFrame, webResource, NetReq, NetResp):
		pass#print dir(NetReq.get_property('message'));#the soupmessage... how to change headers????
		#print NetReq.get_property('message').get_property('request-headers'), "HEAD"
		#test console:
		#while True:
		#		print eval(raw_input(">"))
	
	##
	# Location buttons handler
	def buttonGoto(self,obj,url):
		self.gotoURL(url,True)
	
	def getDirectory(self):
		#Set up quick links:
		done = False
		while (not(done)):
			try:
				mainpage = self.opener.open("http://phobos.apple.com/WebObjects/MZStore.woa/wa/viewGrouping?id=38").read()
				mainpage = etree.fromstring(mainpage)
				els = mainpage.xpath("/a:Document/a:Protocol/a:plist/a:dict/a:dict/a:array/a:dict", namespaces={'a':'http://www.apple.com/itms/'})
				for i in els:
					for j in i:
						#print j.tag,j.text
						if j.text=="title" and j.getnext().text=="Podcasts":
							urlel = j.getnext().getnext().getnext()
							item = gtk.MenuItem("_Podcasts")
							item.connect("activate",self.buttonGoto,urlel.text)
							item.show(); self.podcastDir.append(item)
							#print urlel.tag
							while not(urlel.tag.endswith("array")):
								urlel = urlel.getnext()
							for d in urlel:#each section in podcasts
								if len(d)==6:
									label = d[1].text
									url = d[3].text
									#print label,url
									item = gtk.MenuItem("_"+label)
									item.connect("activate",self.buttonGoto,url)
									item.show(); self.podcastDir.append(item)
						elif j.text=="title" and j.getnext().text=="iTunes U":
							urlel = j.getnext().getnext().getnext()
							item = gtk.MenuItem("_iTunesU")
							item.connect("activate",self.buttonGoto,urlel.text)
							item.show(); self.itunesuDir.append(item)
							#print urlel.tag
							while not(urlel.tag.endswith("array")):
								urlel = urlel.getnext()
							for d in urlel: #each section in podcasts
								if len(d)==6:
									label = d[1].text
									url = d[3].text
									item = gtk.MenuItem("_"+label)
									item.connect("activate",self.buttonGoto,url)
									item.show(); self.itunesuDir.append(item)
				done = True
			except Exception,e:
				print "Directory error:",e
				import random
				time.sleep(random.randint(5,20))
	
	##
	# When no row is selected, buttons are greyed out.
	def noneSelected(self):
		self.tbInfo.set_sensitive(False)
		self.tbPlay.set_sensitive(False)
		self.tbGoto.set_sensitive(False)
		self.tbDownload.set_sensitive(False)
	
	##
	# Check for updates to this program.
	def progUpdate(self,obj):
		openDefault("http://tunesviewer.sourceforge.net/checkversion.php?version=1.0")
	
	##
	# Called when selection changes, changes the enabled toolbar buttons.
	def treesel(self,selection, model):
		self.tbInfo.set_sensitive(True)
		ind = selection[0]
		gotoable = (self.liststore[ind][8] != "")
		downloadable = (self.liststore[ind][9] != "")
		self.tbGoto.set_sensitive(gotoable) # only if there is goto url
		self.tbPlay.set_sensitive(downloadable) # only if there is media url
		self.tbDownload.set_sensitive(downloadable)
		self.rcgoto.set_sensitive(gotoable)
		self.rccopy.set_sensitive(gotoable)
		self.rcplay.set_sensitive(downloadable)
		self.rcdownload.set_sensitive(downloadable) 
		return True
	
	# 3 required functions for drag-drop:
	def motion_cb(self,wid, context, x, y, time):
		context.drag_status(gtk.gdk.ACTION_COPY, time)
		# Returning True which means "I accept this data".
		return True
	def drop_cb(self,wid, context, x, y, time):
		# Some data was dropped, get the data
		wid.drag_get_data(context, context.targets[-1], time)
		context.finish(True,False, time)
		return True
	def got_data_cb(self,wid, context, x, y, data, info, time):
		if data.get_target() != "text/html":
			# Got data.
			print data.get_text()
			#print data.get_target()
			#print data.target()
			#print dir(data)
			if data.get_text() == data.data:
				url = data.data
			else:
				try:
					url = unicode(data.data,"utf-16")
				except:
					print "couldn't decode that."
					url=""
			print url
			#try:
				#url = data.data.decode("utf-16")
			#except:
				#pass
			print url.lower()[:9]
			if url.lower()[:9]=="<a href=\"":
				url = url[9:url.find("\"",9)]
				print "u:",url
			if url!="":
				self.gotoURL(url,True)
			context.finish(True, False, time)

	def find_in_page_cb(self, widget, findT):
		while(1):
			widget.currentFound+=1
			if widget.currentFound >= len(self.liststore):
				msg = gtk.MessageDialog(widget, gtk.DIALOG_MODAL, gtk.MESSAGE_INFO, gtk.BUTTONS_OK, "End of page.")
				msg.run()
				msg.destroy()
				widget.currentFound = -1 #start at beginning.
				break
			thisrow = self.liststore[widget.currentFound]
			if str(thisrow[1]).lower().find(findT)>-1 \
				or str(thisrow[2]).lower().find(findT)>-1 \
				or str(thisrow[3]).lower().find(findT)>-1 \
				or str(thisrow[4]).lower().find(findT)>-1 \
				or str(thisrow[5]).lower().find(findT)>-1 \
				or str(thisrow[6]).lower().find(findT)>-1 \
				or str(thisrow[7]).lower().find(findT)>-1:
					print str(thisrow[1]) #this is a match.
					self.treeview.get_selection().select_iter(thisrow.iter)
					self.treeview.scroll_to_cell(thisrow.path,None,False,0,0)
					break
	
	def openDownloadDir(self, obj):
		openDefault(self.config.downloadfolder)
	
	##
	# Starts a new View Source box based on current url and source.
	def viewsource(self,obj):
		VWin("Source of: "+self.url,self.source)
	
	# see http://faq.pygtk.org/index.py?req=show&file=faq13.017.htp
	def treeclick(self, treeview, event):
		if event.button == 3:
			x = int(event.x)
			y = int(event.y)
			time = event.time
			pthinfo = treeview.get_path_at_pos(x, y)
			if pthinfo is not None:
				path, col, cellx, celly = pthinfo
				treeview.grab_focus()
				treeview.set_cursor( path, col, 0)
				# Right click menu
				self.rcmenu.popup( None, None, None, event.button, time)
			return True

	def tabChange(self,obj1,obj2,i):
		#print obj1,obj2,i,self.taburls
		if len(self.taburls) > i: #is in range
			if self.url != self.taburls[i]: # is different page
				print "loading other tab..."
				self.gotoURL(self.taburls[i],True)

	def bugReport(self,obj):
		print "Opening bug"
		openDefault("http://sourceforge.net/tracker/?group_id=305696&atid=1288143")

	def showHelp(self,obj):
		print "Opening Help"
		openDefault("/usr/share/tunesviewer/help.txt")

	def showAbout(self,obj):
		msg = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL, gtk.MESSAGE_INFO, gtk.BUTTONS_CLOSE, "TunesViewer - Easy iTunesU access in Linux\nVersion 1.1 by Luke Bryan\nThis is open source software, distributed 'as is'")
		msg.run()
		msg.destroy()

	##
	# Shows the downloads-box.
	def viewDownloads(self,obj):
		self.downloadbox.window.show()

	def viewCookie(self,obj):
		cList = []
		print self.cj._cookies
		for k in self.cj._cookies.keys():
			cList.append(k)
			for k2 in self.cj._cookies[k].keys():
				cList.append("   "+k2)
				for k3 in self.cj._cookies[k][k2]:
					cList.append("	  "+k3+" = "+self.cj._cookies[k][k2][k3].value)
		VWin("Cookies","\n".join(cList))
	##
	# Shows the find-box.
	def advancedSearch(self,obj):
		self.findbox.window.show_all()
		
	def searchCurrent(self,obj):
		self.findInPage.show_all()

	##
	# Get clipboard contents, and goto link.
	def pastego(self,obj):
		clip = gtk.clipboard_get()
		text = clip.wait_for_text()
		if text != None:
			self.gotoURL(text,True)

	##
	# Add to podcast manager.
	def addPod(self,obj):
		cmds = self.config.podcastprog.split(" ")
		for i in range(len(cmds)):
			if cmds[i]=="%u":
				cmds[i] = self.podcast
			if cmds[i]=="%i" and self.podcast[0:4]=="http":
				cmds[i] = "itpc"+self.podcast[self.podcast.find("://"):] #rhythmbox requires itpc to specify it's a podcast.
		try:
			subprocess.Popen(cmds)
		except OSError,e:
			msg = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_CLOSE,
			"Error running: %s\n\nIs the program installed and working?\n%s" % (" ".join(cmds), e))
			msg.run()
			msg.destroy()

	##
	# Copies the standard rss podcast link for the current page.
	def copyrss(self,obj):
		print "copying:",self.podcast
		gtk.Clipboard().set_text(self.podcast)
	
	##
	# Called when back-button is pressed.
	def goBack(self,obj):
		if len(self.backStack)>0 and not(self.downloading):
			print self.backStack, self.forwardStack
			self.forwardStack.append(self.url)
			self.gotoURL(self.backStack[-1],False) # last in back stack
			if self.downloadError:
				#undo add to forward:
				self.forwardStack.pop()
			else:
				#remove from back:
				self.backStack.pop()
			print self.backStack, self.forwardStack
		else:
			gtk.gdk.beep()
		#Update the back, forward buttons:
		self.updateBackForward()
	
	##
	# Called when forward-button is pressed.
	def goForward(self,obj):
		if len(self.forwardStack)>0 and not(self.downloading):
			self.backStack.append(self.url)
			self.gotoURL(self.forwardStack[-1],False)
			if self.downloadError:
				#undo add to back:
				self.backStack.pop()
			else:
				#remove from forward:
				self.forwardStack.pop()
		else:
			gtk.gdk.beep()
		self.updateBackForward()
	##
	# Disables the back and forward buttons when appropriate.
	def updateBackForward(self):
		#Only enable the button when there is something to go back/forward to on the stack:
		self.tbForward.set_sensitive(len(self.forwardStack))
		self.tbBack.set_sensitive(len(self.backStack))
	
	##
	# Called when stop is pressed, tries to stop downloader.
	def stop(self,obj):
		self.downloading = False
	
	##
	# Called when refresh is pressed, reopens current page.
	def refresh(self,obj):
		self.gotoURL(self.url,False)
	
	##
	# Called when the go-button is pressed.
	def gobutton(self,obj):
		ind = self.modecombo.get_active()
		if (ind==0):
			self.gotoURL(self.locationentry.get_text(),True)
		elif (ind==1):
			self.gotoURL('http://search.itunes.apple.com/WebObjects/MZSearch.woa/wa/search?media=iTunesU&submit=media&term='+
					self.locationentry.get_text(),True)
		else:
			self.gotoURL('http://ax.search.itunes.apple.com/WebObjects/MZSearch.woa/wa/search?submit=media&term='+self.locationentry.get_text()+'&media=podcast',True)
	
	##
	# Follows link of the selected item.
	def followlink(self,obj):
		if self.selected() == None:
			return
		self.gotoURL(self.selected()[8],True)
	
	def copyRowLink(self,obj):
		if self.selected() == None:
			return
		print self.selected()[8]
		gtk.Clipboard().set_text(self.selected()[8])
	
	##
	# Called when the search/url combobox is changed, sets focus to the location-entry.
	def combomodechanged(self,obj):
		self.window.set_focus(self.locationentry)
		if self.modecombo.get_active() == 0:
			self.locationentry.set_text(self.url)
	
	def openprefs(self,obj):
		self.config.window.show_all()
	
	def exitclicked(self,obj):
		self.delete_event(None,None,None)
	
	##
	# Called when row is selected with enter or double-click,
	# runs the default action.
	def rowSelected(self, treeview, path, column):
		model = self.treeview.get_model()
		iter = model.get_iter(path)
		print model.get_value(iter,0)
		print model.get_value(iter,1)
		print model.get_value(iter,2)
		print model.get_value(iter,3)
		print model.get_value(iter,4)
		print model.get_value(iter,5)
		print model.get_value(iter,6)
		openurl = model.get_value(iter,9) #directurl
		gotourl = model.get_value(iter,8)
		
		if (int(self.config.defaultcommand)==1 and openurl!=""):
			self.playview(None) # play directly.
			print "played"
		elif (int(self.config.defaultcommand)==2 and openurl!=""):
			self.download(None) # download.
		else:
			print "goto"
			if gotourl!="" and openurl=="" and model.get_value(iter,5)=="(Web Link)":
				print "web link"
				openDefault(gotourl)
			else:
				self.gotoURL(gotourl,True)
	
	##
	# Plays or views the selected file (Streaming to program direct, not downloading).
	def playview(self,obj):
		print self.selected()
		if self.selected() == None:
			return
		url = self.selected()[9]
		type = self.selected()[4]
		if self.config.openers.has_key(type):
			# Open the url with the program:
			start(self.config.openers[type], url)
		elif url=="":
			msg = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_CLOSE, "This item is not a file.")
			msg.run()
			msg.destroy()
			return
		else:
			msg = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_CLOSE, "You don't have any program set to open "+type+
			"\nfiles directly from the web. You must first choose the program in Preferences.")
			msg.run()
			msg.destroy()
	
	def viewprop(self,obj):
		# the reference to the new ItemDetails is stored in infoboxes array.
		# if it isn't stored, the garbage collector will mess it up.
		self.infoboxes.append(ItemDetails(self,self.selected()))
	##
	# Gives array of properties of selected item.
	def selected(self):
		(model,iter) = self.treeview.get_selection().get_selected()
		out = []
		for i in range(12):
			try:
				out.append(model.get_value(iter,i))
			except TypeError:
				return None
			except AttributeError:
				return None
		return out
	
	def download(self,obj):
		if self.selected() == None:
			return
		properties = self.selected()
		name = htmlentitydecode(properties[1])
		artist = properties[2]
		duration = properties[3]
		type = properties[4]
		comment = properties[5]
		url = properties[9]
		if url=="":
			msg = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_CLOSE, "This item is not a file.")
			msg.run()
			msg.destroy()
			return
		#Now make an appropriate local-file name:
		local = self.config.downloadfile.replace("%n",name).replace("%a",artist).replace("%c",comment).replace("%t",type).replace("%l",duration).replace(os.sep,"-")
		if self.config.downloadsafe:
			local = safeFilename(local) # Make dos safe filename.
		if (not(os.path.isfile(os.path.join(self.config.downloadfolder,local)))):
			#Doesn't exist, try starting it:
			try:
				#Try opening filename in the appropriate folder:
					a=open(os.path.join(self.config.downloadfolder,local),"w")
					a.close()
			except IOError:
				# shorten filename to make the filesystem accept it.
				local = local.replace(" ","")
				if (len(local) > 100):
					local = local[-99:]
		#It should be good, run it:
		self.downloadbox.newDownload(properties[0],url,os.path.join(self.config.downloadfolder,local),self.opener)
		print "starting download",local
		self.downloadbox.window.show()
	##
	# Startup function
	def main(self):
		if (self.url==""):
			self.gotoURL(self.url,False)
		else:
			self.gotoURL(self.url,True)
		self.throbber.hide()
		gtk.main()
	
	##
	# Called when exiting, checks if downloads should be cancelled.
	def delete_event(self, widget, event, data=None):
		#print self.downloadbox.downloadrunning, self.downloadbox.total
		import shutil
		if self.downloadbox.downloadrunning:
			msg = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL, gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO,
					"Are you sure you want to exit? This will cancel all active downloads.")
			answer = msg.run()
			msg.destroy()
			if (answer == gtk.RESPONSE_YES):
				self.downloadbox.cancelAll()
				self.downloadbox.window.destroy()
				shutil.rmtree(self.tempcache)
				gtk.main_quit()
				sys.exit()
				return False
			else:
				return True
		else:
			shutil.rmtree(self.tempcache)
			gtk.main_quit()
	
	def setLoadDisplay(self,load):
		if load:
			if self.config.throbber:
				self.throbber.show()
			self.window.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
		else:
			self.window.window.set_cursor(None)
			self.throbber.hide()
	
	##
	# downloads data, then calls update.
	# If newurl is true, forward is cleared.
	def gotoURL(self,url,newurl):
		oldurl = self.url # previous url, to add to back stack.
		if self.downloading:
			gtk.gdk.beep()
			return
		self.downloading = True
		self.tbStop.set_sensitive(True)
		#Fix page-link:
		if url.startswith("http://www.apple.com/itunes/affiliates/download/"):
			if url.find("Url=")>-1:
				url = urllib.unquote(url[url.find("Url=")+4:])
			else:
				print "Dead end page"
		# Fix url based on http://bugs.python.org/issue918368
		url = urllib.quote(url, safe="%/:=&?~#+!$,;'@()*[]")
		print url
		
		if (str.upper(url)[:4] == "ITMS" or str.upper(url)[:4] == "ITPC"):
			url = "http"+url[4:]
		elif (url==""): #no url
			self.downloading = False
			self.tbStop.set_sensitive(False)
			return
		self.opener.addheaders = [('User-agent', 'iTunes/10.2')]
		htmMode = self.htmlmode.get_active() #the checkbox
		for line in self.config.alwaysHTML:
			if line!="" and url.find(line)>-1:
				print "Requesting-HTM mode, preference for %s" % (line)
				# based on http://willnorris.com/2009/09/itunes-9-now-with-more-webkit
				htmMode = True
		if htmMode:
			self.opener.addheaders = [('User-agent', 'iTunes/10.2'),("X-Apple-Store-Front","143441-1,12"),("X-Apple-Tz:","-21600")]
		#Show that it's loading:
		#self.throbber.show()
		#self.window.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
		self.setLoadDisplay(True)
		
		t = Thread(target=self.loadPageThread, args=(self.opener,url))
		self.downloading = True
		self.tbStop.set_sensitive(True)
		t.start()
		while (self.downloading):
			#Just wait...
			while gtk.events_pending():
				gtk.main_iteration_do(False)
			time.sleep(0.02)
		try:
			self.setLoadDisplay(False)
			#self.window.window.set_cursor(None)
			#self.throbber.hide()
		except AttributeError:
			pass #just exited, don't crash.
		if self.downloadError != "": #Warn if there is an error:
			msg = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE,
					str(self.downloadError))
			msg.run()
			msg.destroy()
			self.downloading = False
			return
		#No error... continue
		ustart = self.source.find("<body onload=\"return open('")
		if ustart >-1:#This is a redirect-page.
			newU = self.source[ustart+27:self.source.find("'",ustart+27)]
			print "redirect to",newU
			self.downloading = False
			self.tbStop.set_sensitive(False)
			self.gotoURL(newU,False)
			return
		
		if newurl:
			self.forwardStack = []
			if oldurl != "":
				self.backStack.append(oldurl)
		
		#Update the back, forward buttons:
		self.updateBackForward()
			#print self.backStack
		
		if self.modecombo.get_active() == 0:
			self.locationentry.set_text(url)
		print "downloaded."
		self.downloading = False
		self.tbStop.set_sensitive(False)
		self.update()
		
	def loadPageThread(self,opener,url):
		try:
			#Downloader:
			o = opener.open(url)
			text = ""
			
			next = o.read(100)
			while (next != "" and self.downloading):
				text += next
				next = o.read(100)
			if next == "": #Finished successfully.
				self.downloadError = ""
				self.source = text
				self.url = url
			else:
				self.downloadError = "stopped."
			o.close()
		except Exception, e:
			self.downloadError = "Download Error:\n"+str(e)
			print e
		self.downloading = False
		self.tbStop.set_sensitive(False)
		
	##
	# Changes the weird DateTTimeZ format found in the xml date-time.
	def formatTime(self,text):
		return text.replace("T"," ").replace("Z"," ")
	
	def loadIntoWebKit(self,html, url):
		self.webkitLoading=True
		self.descView.load_html_string(html,url);
		self.webkitLoading=False
	
	def webKitLoaded(self, view,frame):
		#Fix <a target="external" etc.
		self.descView.execute_script("window.onload = new function strt() {as = document.getElementsByTagName(\"a\"); for (a in as) {as[a].target=\"\"}; /*alert(as.length)*/}")
	##
	# Updates display based on the current self.source. (Parses the xml and displays.)
	def update(self):
		print "startupdate",self.url
		if self.url.startswith("https://"):
			tip = "Secure page."
			self.tbAuth.show()
			try:#urllib.unquote?
				id=(self.cj._cookies[".deimos.apple.com"]["/WebObjects"]["identity"].value)
				print "identity:",id
				tip+="\nLogged in as: %s" % id;
				print "credentialKey:",(self.cj._cookies[".deimos.apple.com"]["/WebObjects"]["identity"].value)
			except:
				print "none"
			self.tbAuth.set_tooltip_text(tip)
		else:
			self.tbAuth.hide()
		sttime = time.time()
		#Reset data:
		self.taburls = [] #reset tab-urls until finished to keep it from going to other tabs.
		while self.notebook.get_n_pages():
			self.notebook.remove_page(self.notebook.get_n_pages()-1)
		self.liststore.clear()
		
		# fix performance problem. The treeview shouldn't be connected to 
		# the treeview while updating! see http://eccentric.cx/misc/pygtk/pygtkfaq.html
		self.treeview.set_model(None)
		
		#Reset sorting:
		self.liststore.set_sort_column_id(-2,gtk.SORT_DESCENDING)
		
		HTMLSet = False
		HTMLImage = ""
		try:
			#remove bad xml (see http://stackoverflow.com/questions/1016910/how-can-i-strip-invalid-xml-characters-from-strings-in-perl)
			bad = "[^\x09\x0A\x0D\x20-\xD7FF\xE000-\xFFFD]"#\x10000-\x10FFFF]"
			self.source = re.sub(bad," ",self.source) # now it should be valid xml.
			dom = etree.fromstring(self.source.replace('xmlns="http://www.apple.com/itms/"',''))#(this xmlns causes problems with xpath)
			if dom.tag == "html" or dom.tag=="{http://www.w3.org/2005/Atom}feed":
				#Don't want normal pages/atom pages, those are for the web browser!
				raise Exception
		except Exception, e:
			print "ERR", e
			if (self.source.lower().find('<html xmlns="http://www.apple.com/itms/"')>-1):
					print "Parsing HTML"
					self.loadIntoWebKit(self.source,self.url);
					HTMLSet = True
					import lxml.html
					dom = lxml.html.document_fromstring(self.source.replace('<html xmlns="http://www.apple.com/itms/"','<html'))
			elif (self.source != ""): # There is data, but invalid data.
				#self.loadIntoWebKit("","about:")
				msg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_YES_NO,
						"This seems to be a page that should open with a web browser:\n%s\nDo you want to view it?" % self.url)
				if msg.run()==gtk.RESPONSE_YES:
					openDefault(self.url)
				self.loadIntoWebKit("(This page should be opened in a web browser)","about:")
				HTMLSet = True
				msg.destroy()
				return
			else:
				print "unknown source:",self.source
				return
		
		print "tag",dom.tag
		if dom.tag=="rss": #rss files are added
			items = dom.xpath("//item")
			print "rss:",len(items)
			for item in items:
				title=""
				author=""
				linkurl=""
				duration=""
				url=""
				description=""
				pubdate=""
				for i in item:
					if i.tag=="title":
						title=i.text
					elif i.tag=="author" or i.tag.endswith("author"):
						author=i.text
					elif i.tag=="link":
						linkurl=i.text
					elif i.tag=="description":
						description=i.text
					elif i.tag=="pubDate":
						pubdate=i.text
					elif i.tag=="enclosure":
						url=i.get("url")
					elif i.tag.endswith("duration"):
						duration = i.text
				self.liststore.append([None,markup(title,False),author,duration,typeof(url),description,pubdate,"",linkurl,url,"",""])
		
		removeOldData(dom)
		
		items = []
		arr = getItemsArray(dom) # get the tracks list element
		
		keys = dom.xpath("//key") #important parts of document! this is only calculated once to save time
		#Now get location path:
		location = []; locationLinks=[]; lastloc = "" # location description and links and last location in location bar.
		locationelements = dom.xpath("//Path")

		if len(locationelements) > 0:
			for i in locationelements[0]:
				if (type(i).__name__=='_Element' and i.tag=="PathElement"):
					location.append(i.get("displayName"))
					locationLinks.append(i.text)
		if location == ["iTunes U"]:
			section = dom.xpath("//HBoxView") #looking for first section with location info.
			if len(section)>0: # may be out of range
				section = section[0]
				for i in section:
					if (type(i).__name__=='_Element'):
						for j in i:
							if type(j).__name__=='_Element' and j.tag=="GotoURL":
								location.append(j.text.strip())
								locationLinks.append(j.get("url"))
								print j.text.strip(), j.get("url")
								lastloc = j.get("url")
				#print textContent(section)
				if textContent(section).find(">")>-1:
					section.getparent().remove(section) # redundant section > section ... info is removed.
		
		#initialize last-seen variables to nothing, then recursively look at every element, starting with documentElement:
		self.last_el_link = ""
		self.last_el_pic = ""
		self.last_text = ""
		self.addingD = False
		self.Description = ""
		if dom.tag=="html":
			self.seeHTMLElement(dom)
		else:
			self.seeElement(dom,False)
		
		if arr == None:
			ks = dom.xpath("/Document/Protocol/plist/dict/array/dict")
			if len(ks):
				arr = ks
				print "Special end page after html link?"
		
		if arr == None: #No tracklisting.
			hasmedia=False
			if len(self.liststore)==0: #blank.
				print "nothing here!"
				for i in keys:
					if i.text == "url":
						el = i.getnext()
						url = el.text
						print url
						#fix it...
						self.liststore.append([None,"Redirect, try this link","","","","(Link)","","",url,"","",""])
						self.liststore.append([None,"(Try selecting View menu - Request HTML Mode, and refresh this page...)","","","","","","","","","",""])
						if self.config.autoRedirect:
							if self.redirectPages.count(url):
								print "redirect loop :(" #already redirected here.
							else:
								self.redirectPages.append(url)
								self.gotoURL(url,False)
								return
							self.redirectPages = []
					elif i.text=="explanation" or i.text=="message":
						self.Description += textContent(i.getnext())+"\n"
			if self.source.find("<key>message</key><string>Your request could not be completed.</string>")>-1:
				HTMLImage = "(Try selecting View menu - Request HTML Mode, then refresh this page.)"
		else: # add the tracks:
			hasmedia=True
			# for each item...
			for i in arr:
				if type(i).__name__=='_Element' and i.tag=="dict":
					# for each <dict> track info....</dict> get this information:
					name=""
					artist=""
					duration=""
					comments=""
					rtype=""
					url=""
					directurl=""
					releaseDate = ""
					modifiedDate = ""
					id = ""
					for j in i:
						if j.tag == "key":# get each piece of data:
							if (j.text=="songName" or j.text=="itemName"):
								t = j.getnext().text
								if t:
									name = t
							elif (j.text=="artistName"):
								t = j.getnext().text
								if t:
									artist = t
							elif (j.text=="duration"):
								t = j.getnext().text
								if t:
									duration = t
							elif (j.text=="comments" or j.text=="description" or j.text=="longDescription"):
								t = j.getnext().text
								if t:
									comments = t
							elif (j.text=="url"):
								t = j.getnext().text
								if t:
									url = t
							#Added Capital "URL", for the special case end page after html link.
							elif (j.text=="URL" or j.text=="previewURL" or j.text=="episodeURL" or j.text=="preview-url"):
								t = j.getnext().text
								if t:
									directurl = t
							elif (j.text=="explicit"):
								el = j.getnext()
								if el.text=="1":
									rtype = "[Explicit] "
								if el.text=="2":
									rtype = "[Clean] "
							elif (j.text=="releaseDate"):
								t = j.getnext().text
								if t:
									releaseDate = t
							elif (j.text=="dateModified"):
								t = j.getnext().text
								if t:
									modifiedDate = t
							elif (j.text=="itemId"):
								t = j.getnext().text
								if t:
									id = t
							elif (j.text=="metadata"):#for the special case end page after html link
								i.extend(j.getnext().getchildren())# look inside this <dict><key></key><string></string>... also.
					self.liststore.append([None,markup(name,False),artist,timeFind(duration), typeof(directurl),rtype+comments,self.formatTime(releaseDate),self.formatTime(modifiedDate), url,directurl,"",id])
		#Now put page details in the detail-box on top.
		if dom.tag=="rss":
			out = ""
			image = dom.xpath("/rss/channel/image/url")
			if len(image)>0:
				#get recommended width, height:
				w, h = None,None
				try:
					w = dom.xpath("/rss/channel/image/width")[0].text
					h = dom.xpath("/rss/channel/image/height")[0].text
				except:
					pass
				HTMLImage = self.imgText(image[0].text, h, w)
			#else: #TODO: fix this namespace problem
				#image = dom.xpath("/rss/channel/itunes:image",namespaces={'itunes': 'http://www.itunes.com/DTDs/Podcast-1.0.dtd'})[0]
				#if len(image)>0...
			channel = dom.xpath("/rss/channel")
			if len(channel):
				for i in channel[0]:
					if not(image) and i.tag=="{http://www.itunes.com/dtds/podcast-1.0.dtd}image":
						HTMLImage = self.imgText(i.get("href"),None,None)
					if i.text and i.text.strip()!="" and isinstance(i.tag,str):
						thisname = "".join(i.tag.replace("{","}").split("}")[::2])# remove {....dtd} from tag
						out+= "<b>%s:</b> %s\n" % (thisname, i.text)
				try:
					self.window.set_title(dom.xpath("/rss/channel/title")[0].text+" - TunesViewer")
				except IndexError,e:
					self.window.set_title("TunesViewer")
		else:
			out = " > ".join(location)+"\n"
			self.window.set_title(out[:-1]+" - TunesViewer")
			out = ""
			for i in range(len(location)):
				out += "<a href=\""+locationLinks[i]+"\">"+location[i]+"</a> &gt; "
			out = out [:-6]
			if dom.tag == "html":
				self.window.set_title(dom.xpath("/html/head/title")[0].text_content()+" - TunesViewer")
		#Got a page, so clear the redirect list
		self.redirectPages = []
		
		#Get Podcast url
		# already have keys = dom.xpath("//key")
		self.podcast=""
		if len(location)>0 and location[0]=="Search Results":
			print "search page, not podcast."
		elif dom.tag=="rss":
			self.podcast=self.url
		elif hasmedia:
			for i in keys:
				if (i.text == "feedURL"):
					self.podcast = i.getnext().text #Get next text node's text.
					print "Podcast:",self.podcast
					break
			if self.podcast == "":
				#Last <pathelement> should have the page podcast url, with some modification.
				#keys = dom.getElementsByTagName("PathElement")
				#newurl = textContent(keys[len(keys)-1])
				self.podcast = lastloc
				if lastloc=="":
					self.podcast = self.url
				if (self.podcast.find("/Browse/") >-1):
					self.podcast = self.podcast.replace("/Browse/","/Feed/")
				elif (self.podcast.find("/BrowsePrivately/") >-1):
					self.podcast = self.podcast.replace("/BrowsePrivately/","/Feed/")
					# If it's a protected podcast, it will have special goto-url:
					pbvs = dom.xpath("//PictureButtonView")
					for pbv in pbvs:
						if pbv.get("alt")=="Subscribe":
							self.podcast = pbv.getparent().get("draggingURL")
				else:
					print "Not a podcast page."
		else: # not a podcast page? Check for html podcast feed-url in page:
			buttons = dom.xpath("//button")
			if len(buttons):
				isPod = True
				podurl = buttons[len(buttons)-1].get("feed-url") #the last feed-url, see if all feed-urls are this one.
				for b in buttons:
					if b.get("feed-url") and b.get("feed-url")!=podurl: #has feed-url, but it's different.
						isPod = False
				if isPod and podurl: # Every media file has link to same url, so it must be podcast url of this page.
					self.podcast = podurl
				elif len(buttons)>1 and buttons[0].get("subscribe-podcast-url"):
					self.podcast = buttons[0].get("subscribe-podcast-url") #unfortunately these seem to be blocked for now?
		#Enable podcast-buttons if this is podcast:
		self.tbCopy.set_sensitive(self.podcast!="")
		self.tbAddPod.set_sensitive(self.podcast!="")
		self.addpodmenu.set_sensitive(self.podcast!="")
		print "s:",time.time()-sttime
		
		#None selected now, disable item buttons.
		self.noneSelected()
		self.treeview.set_model(self.liststore)
		print "rows:",len(self.liststore)
		mediacount = 0
		linkscount = 0
		for row in self.liststore:
			if len(row) > 10 and row[9]:
				mediacount += 1
			elif row[8]:
				linkscount += 1
		rs = ""
		ls = ""
		ms = ""
		if len(self.liststore)!=1:
			rs = "s"
		if linkscount !=1:
			ls = "s"
		if mediacount != 1:
			ms = "s"
		self.statusbar.set_text("%s row%s, %s link%s, %s file%s" % \
		(len(self.liststore), rs, linkscount, ls, mediacount, ms))
		
		self.icon_audio=None
		self.icon_video=None
		self.icon_other=None
		self.icon_link=None
		try:
			icon_theme = gtk.icon_theme_get_default() #Access theme's icons:
			self.icon_audio = icon_theme.load_icon("sound",self.config.iconsizeN,0)
			self.icon_video = icon_theme.load_icon("video",self.config.iconsizeN,0)
			self.icon_other = icon_theme.load_icon("gnome-fs-regular",self.config.iconsizeN,0)
			self.icon_link = icon_theme.load_icon("gtk-jump-to-ltr",self.config.iconsizeN,0)
		except Exception, e:
			print "Exception:",e;
			
		pics = dom.xpath("//PictureView")
		if len(pics)>0: #get main picture for this page:
				num = 0
				while (num<len(pics) and (( pics[num].get("height")=="550") or ( (pics[num].get("alt")=="Explicit" or pics[num].get("alt")=="Clean")))):
					num+=1 # skip this one
				if num<len(pics): # didn't go off end of list
					h = pics[num].get("height")
					w = pics[num].get("width")
					pic = pics[num].get("url")
					HTMLImage = self.imgText(pic, h, w)
		#Get the icons for all the rows:
		self.updateListIcons()
		
		#Done with this:
		del dom
		# avoid possible memory leak: http://faq.pygtk.org/index.py?req=show&file=faq08.004.htp
		gc.collect()
		
		if self.url.find("?i="): # link to specific item, select it.
			id = self.url[self.url.rfind("?i=")+3:]
			id = id.split("&")[0]
			for i in self.liststore:
				if i[11]==id:
					print "selecting item",id
					self.treeview.get_selection().select_iter(i.iter)
					self.treeview.scroll_to_cell(i.path,None,False,0,0)
					#self.treeview.grab_focus()
		#test console:
		#while True:
		#		print eval(raw_input(">"))
		print "update took:",(time.time() - sttime),"seconds"
		if HTMLSet:
			for i in self.liststore:
				if i[4]!='':
					print "selecting item",i
					#self.treeview.get_selection().select_iter(i.iter)
					self.treeview.scroll_to_cell(i.path,None,False,0,0)
					break;
		else:
			self.loadIntoWebKit("<html><style>img {float:left; margin-right:6px; -webkit-box-shadow: 0 3px 5px #999999;}</style><body>"+HTMLImage+out.replace("\n","<br>")+"<p>"+self.Description.replace("\n","<br>")+"</body></html>","about:");
	#recursively looks at xml elements:
	def seeElement(self,element,isheading):
		if isinstance(element.tag,str):
			# check this element:
			if element.tag == "GotoURL":
				urllink = element.get("url")
				name = textContent(element).strip()
				if element.get("draggingName"):
					author = element.get("draggingName")
				else:
					author = ""
				#See if there is text right after it for author.
				nexttext = element.getparent().getparent().getnext()
				
				match = re.match("Tab [0-9][0-9]* of [0-9][0-9]*",author)
				if match: # Tab handler:
					match = author[match.end():]
					#print author,"TAB!", match
					label = gtk.Label(); label.show()
					contents = gtk.Label(); contents.show()
					contents.set_size_request(0, 0) # No tab contents
					if match[0:12]==", Selected. ":
						match = match[12:]
						print "sel:",match
						label.set_markup("<i><b>"+glib.markup_escape_text(match)+"</b></i>")
						self.notebook.append_page(contents,label)
						self.notebook.set_current_page(-1) #select this one
						self.notebook.queue_draw_area(0,0,-1,-1)
					else:
						match = match[2:]
						label.set_markup(glib.markup_escape_text(match))
						self.notebook.append_page(contents,label)
					self.taburls.append(urllink)
					self.notebook.show_all()
				else:
					# If there's a TextView-node right after, it should be the author-text or college name.
					if nexttext != None and isinstance(nexttext.tag,str) and nexttext.tag == "TextView":
						author = textContent(nexttext).strip()
					if name != "":
						#text link. Does it have picture?
						arturl = ""
						if self.last_el_link == urllink:
							arturl = self.last_el_pic
							#(last pic was the icon for this, it will be added:)
							self.Description += "<img src=\"%s\" width=%s height=%s>" % (self.last_el_pic, self.config.imagesizeN, self.config.imagesizeN)
						self.Description += "<a href=\"%s\">%s - %s</a><br>" % (urllink, HTmarkup(name,isheading), author);
						#self.liststore.append([None, markup(name.strip(),isheading), author.strip(), "", "", "(Link)", "", "", urllink, "", arturl, ""])
					elif len(element): #No name, this must be the picture-link that comes before the text-link. 
						picurl = "" # We'll try to find picture url in the <PictureView> inside the <View> inside this <GotoURL>.
						el = element[0] # first childnode
						if el != None and isinstance(el.tag,str) and (el.tag == "PictureView" or el.tag == "PictureButtonView"):
							picurl = el.get("url")
							#print "PIC",urllink, picurl, el.get("alt")
							self.last_el_link = urllink
							self.last_el_pic = picurl
							if el.get("alt")=="next page" or el.get("alt")=="previous page":
								self.Description += "<a href=\"%s\">%s</a>" % (urllink, HTmarkup(el.get("alt"),isheading))
								#self.liststore.append([None, markup(el.get("alt"),isheading), "", "","","(Link)","","",urllink,"",picurl,""])
						elif el != None and isinstance(el.tag,str) and el.tag == "View":
							el = el[0]
							if el != None and isinstance(el.tag,str) and el.tag == "PictureView":
								picurl = el.get("url")
								#print "pic",urllink, picurl
								self.last_el_link = urllink
								self.last_el_pic = picurl
					else:
						print "blank element:",element,element.text
			elif element.tag == "OpenURL":
				urllink = element.get("url")
				name = textContent(element).strip()
				if element.get("draggingName"):
					author = element.get("draggingName")
				else:
					author = ""
				#See if there is text right after it for author.
				nexttext = element.getparent().getparent().getnext()
				# If there's a TextView-node right after, it should be the author-text or college name.
				if nexttext != None and isinstance(nexttext.tag,str) and nexttext.tag == "TextView":
					author = textContent(nexttext).strip()
				self.Description += "<a href=\"%s\">%s" % (urllink, HTmarkup(name,isheading))
				#if urllink and urllink[0:4]=="itms":
					#lnk = "(Link)"
				#else:
					#lnk = "(Web Link)"
				#self.liststore.append([None, markup(name.strip(),isheading), author.strip(), "","",lnk,"","",urllink,"","",""])
			elif element.tag == "TextView":
				if element.get("headingLevel")=="2" or (element.get("topInset")=="1" and element.get("leftInset")=="1"):
					isheading = True
				text, goto = self.searchLink(element)
				if text.strip() != self.last_text: # don't repeat (without this some text will show twice).
					if True:# self.addingD: # put in description (top box)
						self.Description += "\n%s\n<br>" % text.strip()
					#else:
					#	self.liststore.append([None,markup(text.strip(),isheading),"","","","","","","","","",""])
					#	if element.get("styleSet")=="normal11":
					#		#text style. May be description/review/info, show in description box also:
					#		self.Description += "\n%s\n" % text.strip()
					self.last_text = text.strip()
				if goto != None:
					for i in element:
						if isinstance(i.tag,str):
							self.seeElement(i,isheading)
			else:
				#sometimes podcast ratings are in hboxview alt, get the text alts.
				if element.tag == "HBoxView" and element.get("alt"): #and element.getAttribute("alt").lower()!=element.getAttribute("alt").upper():
					self.Description += HTmarkup(element.get("alt"),False)
					#self.liststore.append([None,markup(element.get("alt"),False),"","","","","","","","","",""])
				
				# Recursively do this to all elements:
				for node in element:
					self.seeElement(node,isheading)
				#[self.seeElement(e,isheading) for e in element] #faster??
		elif type(element).__name__=='_Comment': #element.nodeType == element.COMMENT_NODE:
			# Set it to add the description to self.Description when it is between these comment nodes:
			if element.text.find("BEGIN description")>-1:
				self.addingD = True
			elif element.text.find("END description")>-1:
				self.addingD = False
	
	def seeHTMLElement(self,element):
		if isinstance(element.tag,str): # normal element
			if element.get("audio-preview-url") or element.get("video-preview-url"): #Ping audio/vid.
				if element.get("video-preview-url"):
					url = element.get("video-preview-url")
				else:
					url = element.get("audio-preview-url")
				title = ""
				if element.get("preview-title"):
					title = element.get("preview-title")
				author = ""
				if element.get("preview-artist"):
					author = element.get("preview-artist")
				duration = ""
				if element.get("preview-duration"):
					duration = timeFind(element.get("preview-duration"))
				self.liststore.append([None,markup(title,False),author,duration,typeof(url),"","","","",url,"",""])
			elif element.tag == "a" or element.tag=="option":
				# Get link data
				urllink = element.get("href")
				#img = self.getImgUrl(element)
				img = "" #In html
				name = self.getTextByClass(element,"name")
				
				if name =="" and element.get("tooltip-title"):
					name = element.get("tooltip-title")#For Ping profiles
				if name =="":
					name = element.text_content()
				if name =="" and element.get("class"):
					name = element.get("class")
				
				author = self.getTextByClass(element,"artist")
				if author == "" and element.get("tooltip-artist"):
					author = element.get("tooltip-artist")#For Ping profiles
				if urllink and name != "" and name !="artwork-link": #and author != "":
					if element.get("href")==self.last_el_link:
						img = self.last_el_pic
					self.liststore.append([None,markup(name.rstrip().lstrip(),False), author.strip(), "","","(Link)","","",urllink,"",img,""])
				elif element.getnext() is not None and element.getnext().get("class")=="lockup-info": # next one is the real link.
					self.last_el_link = element.get("href")
					self.last_el_pic = img
				elif name=="artwork-link":
					self.last_el_link = element.get("href")
					self.last_el_pic = img
				elif urllink: # other; it must be single image link.
					self.liststore.append([None,markup(name.rstrip().lstrip(),False), author.rstrip().lstrip(), "","","(Link)","","",urllink,"",img,""])
				#print urllink
			elif element.tag=="tr" and element.get("class") and (element.get("class").find("track-preview")>-1 or element.get("class").find("podcast-episode")>-1):
				#If you view the source of podcast html in browser, you'll find the info in the rows using firebug.
				title=""; exp=""
				if element.get("preview-title"):
					title = element.get("preview-title")
				artist = ""
				if element.get("preview-artist"):
					artist = element.get("preview-artist")
				time="";
				if element.get("duration"):
					print element.get("duration")
					time = timeFind(element.get("duration"))
				if element.get("rating-riaa") and element.get("rating-riaa")!="0":
					exp = "[Explicit] "
				url = ""
				if element.get("audio-preview-url"):
					url = element.get("audio-preview-url")
				elif element.get("video-preview-url"):
					url = element.get("video-preview-url")
				type = typeof(url)
				comment = ""; releaseDate=""; gotou = ""
				for sub in element:
					cl = sub.get("class")
					val = sub.get("sort-value")
					if cl and val: #has class and value, check them:
						if cl.find("name")>-1:
							title=val
						if cl.find("album")>-1:
							artist=val
							if len(sub) and sub[0].get("href"):
								gotou = sub[0].get("href") # the <a href in this cell
						if cl.find("time")>-1:
							#print "time",val
							time = timeFind(val)
						if cl.find("release-date")>-1:
							releaseDate=val
						if cl.find("description")>-1:
							comment = val
				self.liststore.append([None,markup(title,False),artist,time,type,exp+comment,releaseDate,"",gotou,url,"",""])
				for i in element:
					self.seeHTMLElement(i)
			#Don't need to show all elements, with webkit view...
			#elif element.tag!="script" and element.text and element.text.strip():
				#isHeading = (element.tag=="h3" or element.tag=="h2" or element.tag=="h1")
				#self.liststore.append([None,markup(element.text.strip(),isHeading),"","","","","","","","","",""])
				#if element.tail and element.tail.strip():
					##Added to get Ping updates:
					#self.liststore.append([None,markup(element.tail.strip(),False),"","","","","","","","","",""])
				#for i in element:
					#self.seeHTMLElement(i)
					
			#elif 0:#element.tag == "div" and element.text_content().rstrip().lstrip():# text?
				#self.liststore.append([None,markup(element.text_content().strip(),False),"","","","","","","","","",""])
				#if self.hasAlink(element):
					#for i in element:
						#self.seeHTMLElement(i)
			elif element.tag=="button" and element.get("anonymous-download-url"):#Added for epub feature
				self.liststore.append([None,markup(element.get("title"),False),element.get("item-name"),"",typeof(element.get("anonymous-download-url")),"","","",element.get("anonymous-download-url"),"","",""])#Special 
			else: # go through the childnodes.
				if element.tail and element.tail.strip():
					#Added to get Ping updates:
					self.liststore.append([None,markup(element.tail.strip(),False),"","","","","","","","","",""])
				for i in element:
					self.seeHTMLElement(i)
	
	def getTextByClass(self,element,classtext):
		if element.get("class") == classtext:
			return element.text_content()
		else:
			out = ""
			for i in element:
				out += self.getTextByClass(i,classtext)
			return out
	
	def hasAlink(self,element):
		if isinstance(element.tag,str):
			if element.tag=="a":
				return True
			else:
				for i in element:
					if self.hasAlink(i):
						return True
				return False
	
	def getImgUrl(self,element): # find the image
		if isinstance(element.tag,str) and element.tag == "img":
			return element.get("src")
		else:
			for i in element:
				out = self.getImgUrl(i)
				if out:
					return out
			return ""
	
	##
	# Gets an image pixbuf from a url. Uses cached image if available.
	def getImagePixbuf(self,url):
		#print "getimagepixbuf for",url
		if self.cachemap.has_key(url): #already downloaded.
			cached = os.path.join(self.tempcache,self.cachemap[url])
			if os.path.isfile(cached):
				try:
					return gtk.gdk.pixbuf_new_from_file(cached)
				except:
					print "can't make image from",cached
		else: #download:
			myid = self.nextcachename
			self.nextcachename += 1
			try:
				net = self.opener.open(url)
			except ValueError, e:
					import urlparse
					print "relative url?"
					print self.url,url
					url = urlparse.urljoin(self.url,url)
					net = self.opener.open(url)
			filename = os.path.join(self.tempcache, str(myid))
			local = open(filename,"wb")
			local.write(net.read())
			local.close(); net.close();
			self.cachemap[url] = filename
			print filename
			try:
				return gtk.gdk.pixbuf_new_from_file(filename)
			except:
				print "can't make image from",filename
	
	def imgText(self,picurl,height,width):
		if self.config.scaleImage and height and width:
			return '<img src="%s" height="%s" width="%s">' % (picurl, height, width)
		else:
			return '<img src="%s">' % picurl
	
	##
	# Updates the icons in the liststore based on contents.
	def updateListIcons(self):
		for row in self.liststore:
			type = row[4].lower()
			if type:
				if type==".mp3" or type==".m4a" or type==".amr" or type==".m4p" or type==".aiff" or type==".aif" or type==".aifc":
					self.liststore.set(row.iter,0, self.icon_audio)
				elif type==".mp4" or type==".m4v" or type==".mov" or type==".m4b":
					self.liststore.set(row.iter,0, self.icon_video)
				else:
					self.liststore.set(row.iter,0, self.icon_other)
			elif row[8]: #it's a link
				self.liststore.set(row.iter,0, self.icon_link)
			url = row[10]
		# rows have basic icons now.
		# set up threads to download image icons:
		if self.config.imagesizeN > 0:
			for i in range(4):
				t = Thread(target=self.imagedownloader, args=(4,i,self.url))
				t.start()
	
	def imagedownloader(self, mod, number, pageurl):
		# downloads and sets image when the row number % mod == number.
		for i in range(len(self.liststore)):
			if i % mod == number and pageurl==self.url:
				tries = 3
				while tries and os.path.isdir(self.tempcache) and i<len(self.liststore) and self.liststore[i][10]:
					try:
						if self.url==pageurl:
							pixbuf = self.getImagePixbuf(self.liststore[i][10])
							if pageurl==self.url and pixbuf != None:
								pixbuf = pixbuf.scale_simple(self.config.imagesizeN,self.config.imagesizeN,gtk.gdk.INTERP_BILINEAR)
								self.liststore.set(self.liststore[i].iter,0,pixbuf)
							else: #left the page. cancel all this.
								return
						else:
							return
					except IOError,e:
						print "Row pic error:",e#,self.liststore[i][10]
						tries -= 1
					except IndexError,e:
						print "update index error:",e
						tries=0
					else: #ok.
						tries=0
	
	##
	# Given an element, finds all text in it and the link in it (if any).
	def searchLink(self,element):
		text, goto = "", None
		if isinstance(element.tag,str):#element.nodeType == element.ELEMENT_NODE:
			if element.tag == "OpenURL" or element.tag == "GotoURL" or element.tag == "a": # for both xml and html <a.
				goto = element
			elif element.tag == "PictureView" and element.get("url").find("/stars/rating_star_")>-1:
				text += "*"
			else:
				try:
					int(element.text)
					isInt = True
				except:
					isInt = False
				if element.text and not(isInt and element.get("normalStyle")=="descriptionTextColor"): #To ignore repeated numbers like <SetFontStyle normalStyle="descriptionTextColor">8</SetFontStyle>
					text += element.text
				for i in element:
					t,g = self.searchLink(i)
					text += t
					if i.tail:
						text += i.tail # tailing text
					if g!=None:
						goto = g
		return text, goto


##
# When initialized, this will show a new window with text.
class VWin:
	def __init__(self,title,source):
		#print url,source
		self.window = gtk.Window()
		self.window.set_size_request(400, 400)
		self.window.set_title(title)
		#self.window.connect("delete_event", self.window.destroy)
		self.sw = gtk.ScrolledWindow()
		self.sw.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
		self.viewer = gtk.TextView()
		self.viewer.get_buffer().set_text(source)
		self.viewer.set_wrap_mode(gtk.WRAP_WORD)
		self.viewer.set_editable(False)
		#TextView inside ScrolledWindow goes in the window:
		self.sw.add(self.viewer)
		self.window.add(self.sw)
		self.window.show_all()


args = sys.argv[1:]
url = ""
if len(args) > 1 and args[0] == "-s":
	url = 'http://search.itunes.apple.com/WebObjects/MZSearch.woa/wa/search?media=iTunesU&submit=media&term='+args[1]
elif len(args) > 0:
	url = args[0]

# Create the TunesViewer instance and run it:
print "TunesViewer 1.1"
prog = TunesViewer()
prog.url = url
prog.main()
