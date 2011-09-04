#!/usr/bin/env python

# TunesViewer
# A small, easy-to-use tool to access iTunesU and podcast media.
# Designed by Luke Bryan 2009 - 2011
# Loading-icon is from mozilla's throbber icon.

#Licensed under Apache license
#Unless required by applicable law or agreed to in writing, software
#distributed under the License is distributed on an "AS IS" BASIS,
#WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#See the License for the specific language governing permissions and
#limitations under the License.

#Import the standard python libraries needed:
import urllib, urllib2, cookielib, gzip
import sys, os, subprocess, time
from threading import Thread
from StringIO import StringIO

#Import GTK for gui.
import gobject
gobject.threads_init()
import pygtk, pango, glib
pygtk.require('2.0')
import gtk

from configbox import ConfigBox
from findinpagebox import FindInPageBox
from downloadbox import DownloadBox
from findbox import FindBox
from itemdetails import ItemDetails
from webkitview import WebKitView
from Parser import Parser
from SingleWindowSocket import SingleWindowSocket
from common import *

try:
	from lxml import etree
except ImportError, e:
	print "This program requires LXML, but it is not installed."
	msg = gtk.MessageDialog(None,gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR,gtk.BUTTONS_CLOSE, "This program requires LXML, but it is not installed.\nPlease install python-lxml with your system's package manager, or follow the installation instructions at:\nhttp://codespeak.net/lxml/index.html#download")
	msg.run()
	msg.destroy()
	sys.exit(1)

class TunesViewer:
	source= "" # full html/xml source
	url= "" # page url
	podcast= "" #podcast url
	downloading=False #when true, don't download again, freezing prog. (Enforces having ONE gotoURL)
	downloadError=""
	infoboxes = []
	redirectPages = []
	
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
		self.window.resize(610,520)
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
		
		# will hold icon, title, artist, time, type, comment, releasedate,datemodified, gotourl, previewurl, price, itemid.
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
		self.copym = gtk.ImageMenuItem(gtk.STOCK_COPY)
		self.copym.set_label("_Copy Normal Podcast Url")
		self.copym.connect("activate",self.copyrss)
		key, mod = gtk.accelerator_parse("<Ctrl><Shift>C")
		self.copym.add_accelerator("activate", agr, key, mod, gtk.ACCEL_VISIBLE)
		editmenu.append(self.copym)
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
		self.htmlmode.set_active(True)
		viewmenu.append(self.htmlmode)
		self.mobilemode = gtk.CheckMenuItem("Mobile Mode")
		#viewmenu.append(self.mobilemode)
		viewmenu.append(gtk.SeparatorMenuItem())
		viewdownloads = gtk.ImageMenuItem(gtk.STOCK_GO_DOWN)
		viewdownloads.set_label("Show _Downloads")
		key, mod = gtk.accelerator_parse("<Ctrl>j")
		viewdownloads.add_accelerator("activate",agr,key,mod,gtk.ACCEL_VISIBLE)
		viewdownloads.connect("activate",self.viewDownloads)
		viewmenu.append(viewdownloads)
		viewdir = gtk.ImageMenuItem(gtk.STOCK_DIRECTORY)
		viewdir.set_label("Downloads Directory")
		viewdir.connect("activate",self.openDownloadDir)
		viewmenu.append(viewdir)
		viewmenu.append(gtk.SeparatorMenuItem())
		
		ziItem = gtk.ImageMenuItem(gtk.STOCK_ZOOM_IN)
		key, mod = gtk.accelerator_parse("<Ctrl>plus")
		ziItem.add_accelerator("activate",agr,key,mod,gtk.ACCEL_VISIBLE)
		ziItem.connect("activate",self.webkitZI)
		viewmenu.append(ziItem)
		zoItem = gtk.ImageMenuItem(gtk.STOCK_ZOOM_OUT)
		key, mod = gtk.accelerator_parse("<Ctrl>minus")
		zoItem.add_accelerator("activate",agr,key,mod,gtk.ACCEL_VISIBLE)
		zoItem.connect("activate",self.webkitZO)
		viewmenu.append(zoItem)
		znItem = gtk.ImageMenuItem(gtk.STOCK_ZOOM_100)
		key, mod = gtk.accelerator_parse("<Ctrl>0")
		znItem.add_accelerator("activate",agr,key,mod,gtk.ACCEL_VISIBLE)
		znItem.connect("activate",self.webkitZN)
		viewmenu.append(znItem)
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
		
		self.locShortcut = gtk.MenuItem("Current _URL")
		key, mod = gtk.accelerator_parse("<Ctrl>L")
		self.locShortcut.add_accelerator("activate",agr,key,mod,gtk.ACCEL_VISIBLE)
		viewmenu.append(self.locShortcut)
		self.locShortcut.hide()
		self.locShortcut.connect("activate",self.locationBar)
		
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
		homeb = gtk.ImageMenuItem(gtk.STOCK_HOME)
		homeb.connect("activate",self.goHome)
		gomenu.append(homeb)
		
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
		helpitem = gtk.ImageMenuItem(gtk.STOCK_HELP)
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
		vpaned.set_position(260)
		sw = gtk.ScrolledWindow()
		sw.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
		self.descView = WebKitView(self)
		
		sw.add(self.descView)
		vpaned.pack1(sw,resize=True)
		vpaned.pack2(bottom,resize=False)
		
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
		self.copym.set_sensitive(self.podcast!="")
		self.tbAuth.hide()
		
		self.noneSelected()
		
		self.config = ConfigBox(self) # Only one configuration box, it has reference back to here to change toolbar,statusbar settings.
		
		# Set up the main url handler with downloading and cookies:
		self.cj = cookielib.CookieJar()
		self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
		self.opener.addheaders = [('User-agent', self.descView.ua),('Accept-Encoding','gzip'),('Accept-Language','en-US')]

		#Check for crashed downloads:
		try:
			dlines = open(os.path.expanduser("~/.tunesviewerDownloads"),'r').read().split("\n")
			os.remove(os.path.expanduser("~/.tunesviewerDownloads"))
			for i in range(len(dlines)):
				if dlines[i].startswith("####"):
					self.downloadbox.newDownload(None,dlines[i+1],dlines[i+2],self.opener)
		except IOError, e:
			print "no downloads crashed."
		
	def webkitZI(self,obj):
		self.descView.zoom_in()
		
	def webkitZO(self,obj):
		self.descView.zoom_out()
		
	def webkitZN(self,obj):
		self.descView.set_zoom_level(1)
	
	def buttonGoto(self,obj,url):
		"Menu directory-shortcuts handler"
		self.gotoURL(url,True)
	
	def goHome(self,obj):
		self.gotoURL(self.config.home,True)
	
	def getDirectory(self):
		"""Sets up quick links in the Go menu.
		This info appears to have been moved to <script id="protocol" type="text/x-apple-plist">
		sections, so this code no longer works correctly."""
		#done = False
		#tried = 0
		#while (tried < 3):
			#try:
				#opener = urllib2.build_opener()
				#opener.addheaders = [('User-agent', 'iTunes/8.2')] # Get old xml format.
				#mainpage = opener.open("http://phobos.apple.com/WebObjects/MZStore.woa/wa/viewGrouping?id=38").read()
				#mainpage = etree.fromstring(mainpage)
				#els = mainpage.xpath("/a:Document/a:Protocol/a:plist/a:dict/a:dict/a:array/a:dict", namespaces={'a':'http://www.apple.com/itms/'})
				#for i in els:
					#for j in i:
						##print j.tag,j.text
						#if j.text=="title" and j.getnext().text=="Podcasts":
							#urlel = j.getnext().getnext().getnext()
							#item = gtk.MenuItem("_Podcasts")
							#item.connect("activate",self.buttonGoto,urlel.text)
							#item.show(); self.podcastDir.append(item)
							##print urlel.tag
							#while not(urlel.tag.endswith("array")):
								#urlel = urlel.getnext()
							#for d in urlel:#each section in podcasts
								#if len(d)==6:
									#label = d[1].text
									#url = d[3].text
									##print label,url
									#item = gtk.MenuItem("_"+label)
									#item.connect("activate",self.buttonGoto,url)
									#item.show(); self.podcastDir.append(item)
						#elif j.text=="title" and j.getnext().text=="iTunes U":
							#urlel = j.getnext().getnext().getnext()
							#item = gtk.MenuItem("_iTunesU")
							#item.connect("activate",self.buttonGoto,urlel.text)
							#item.show(); self.itunesuDir.append(item)
							##print urlel.tag
							#while not(urlel.tag.endswith("array")):
								#urlel = urlel.getnext()
							#for d in urlel: #each section in podcasts
								#if len(d)==6:
									#label = d[1].text
									#url = d[3].text
									#item = gtk.MenuItem("_"+label)
									#item.connect("activate",self.buttonGoto,url)
									#item.show(); self.itunesuDir.append(item)
				#done = True
				#tried = 4 #exit
			#except Exception,e:
				#print self.downloadbox.window
				#print "Directory error:",e
				#import random
				#time.sleep(random.randint(1,10))
				#tried+=1
	
	def noneSelected(self):
		"When no row is selected, buttons are greyed out."
		self.tbInfo.set_sensitive(False)
		self.tbPlay.set_sensitive(False)
		self.tbGoto.set_sensitive(False)
		self.tbDownload.set_sensitive(False)
	
	def progUpdate(self,obj):
		"Checks for update to the program."
		openDefault("http://tunesviewer.sourceforge.net/checkversion.php?version=1.3")
	
	def treesel(self,selection, model):
		"Called when selection changes, changes the enabled toolbar buttons."
		self.tbInfo.set_sensitive(True)
		ind = selection[0]
		gotoable = (self.liststore[ind][8] != "")
		playable = (self.liststore[ind][9] != "")
		downloadable = (self.liststore[ind][9] != "" and (self.liststore[ind][10]=="" or self.liststore[ind][10]=="0"))
		self.tbGoto.set_sensitive(gotoable) # only if there is goto url
		self.tbPlay.set_sensitive(playable) # only if there is media url
		self.tbDownload.set_sensitive(downloadable)
		self.rcgoto.set_sensitive(gotoable)
		self.rccopy.set_sensitive(gotoable)
		self.rcplay.set_sensitive(playable)
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
		#TODO: Fix webkit search so it will search and highlight the text, this should work, but it doesn't:
		self.descView.search_text(findT, False, True, True)
		self.descView.set_highlight_text_matches(highlight=True)
	
	def openDownloadDir(self, obj):
		openDefault(self.config.downloadfolder)
	
	def viewsource(self,obj):
		"Starts a new View Source box based on current url and source."
		VWin("Source of: "+self.url,self.source)
	
	def treeclick(self, treeview, event):
		"For right click menu - see http://faq.pygtk.org/index.py?req=show&file=faq13.017.htp"
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
		msg = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL, gtk.MESSAGE_INFO, gtk.BUTTONS_CLOSE, "TunesViewer - Easy iTunesU access in Linux\nVersion 1.3 by Luke Bryan\nThis is open source software, distributed 'as is'")
		msg.run()
		msg.destroy()

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
					cList.append("      "+k3+" = "+self.cj._cookies[k][k2][k3].value)
		VWin("Cookies","\n".join(cList))
	
	def advancedSearch(self,obj):
		self.findbox.window.show_all()
		
	def searchCurrent(self,obj):
		self.findInPage.show_all()

	def pastego(self,obj):
		"Gets the clipboard contents, and goes to link."
		clip = gtk.clipboard_get()
		text = clip.wait_for_text()
		if text != None:
			self.gotoURL(text,True)

	def addPod(self,obj):
		"Adds the current podcast to the specified podcast manager."
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

	def copyrss(self,obj):
		"Copies the standard rss podcast link for the current page."
		print "copying:",self.podcast
		gtk.Clipboard().set_text(self.podcast)
	
	def goBack(self,obj):
		"Called when back-button is pressed."
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
	
	def goForward(self,obj):
		"Called when forward button is pressed"
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
	
	def updateBackForward(self):
		"Disables the back and forward buttons when no back/forward is on stack."
		self.tbForward.set_sensitive(len(self.forwardStack))
		self.tbBack.set_sensitive(len(self.backStack))
	
	def stop(self,obj):
		"Called when stop is pressed, tries to stop downloader."
		self.downloading = False
	
	def refresh(self,obj):
		"Called when refresh is pressed, reopens current page."
		self.gotoURL(self.url,False)
	
	def gobutton(self,obj):
		"Called when the go-button is pressed."
		ind = self.modecombo.get_active()
		if (ind==0):
			self.gotoURL(self.locationentry.get_text(),True)
		elif (ind==1):
			self.gotoURL('http://search.itunes.apple.com/WebObjects/MZSearch.woa/wa/search?media=iTunesU&submit=media&term='+
					self.locationentry.get_text(),True)
		else:
			self.gotoURL('http://ax.search.itunes.apple.com/WebObjects/MZSearch.woa/wa/search?submit=media&term='+self.locationentry.get_text()+'&media=podcast',True)
	
	def followlink(self,obj):
		"Follows link of the selected item."
		if self.selected() == None:
			return
		self.gotoURL(self.selected()[8],True)
	
	def copyRowLink(self,obj):
		if self.selected() == None:
			return
		print self.selected()[8]
		gtk.Clipboard().set_text(self.selected()[8])
	
	def combomodechanged(self,obj):
		""" Called when the search/url combobox is changed, sets focus to the location-entry. """
		self.window.set_focus(self.locationentry)
		if self.modecombo.get_active() == 0:
			self.locationentry.set_text(self.url)
		self.locationentry.select_region(0,-1)
	
	def openprefs(self,obj):
		self.config.window.show_all()
	
	def exitclicked(self,obj):
		self.delete_event(None,None,None)
	
	def rowSelected(self, treeview, path, column):
		""" Called when row is selected with enter or double-click, runs default action. """
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
	
	def playview(self,obj):
		""" Plays or views the selected file (Streaming to program directly, not downloading). """
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
	
	def locationBar(self,obj):
		"Selects the url, similar to Ctrl+L in web browser"
		self.modecombo.set_active(0)
	
	def viewprop(self,obj):
		# the reference to the new ItemDetails is stored in infoboxes array.
		# if it isn't stored, the garbage collector will mess it up.
		self.infoboxes.append(ItemDetails(self,self.selected()))
	
	def selected(self):
		""" Gives the array of properties of selected item. """
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
		self.startDownload(properties)
		
	def startDownload(self, properties):
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
		if properties[10] != "0" and properties[10] != "":
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
	
	def main(self): #Startup
		if (self.url==""):
			self.gotoURL(self.config.home,False)
		else:
			self.gotoURL(self.url,True)
		self.throbber.hide()
		gtk.main()
	
	def delete_event(self, widget, event, data=None):
		""" Called when exiting, checks if downloads should be cancelled. """
		#print self.downloadbox.downloadrunning, self.downloadbox.total
		import shutil
		if self.downloadbox.downloadrunning:
			msg = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL, gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO,
					"Are you sure you want to exit? This will cancel all active downloads.")
			answer = msg.run()
			msg.destroy()
			if (answer == gtk.RESPONSE_YES):
				#Clear crash recovery
				try:
					os.remove(os.path.expanduser("~/.tunesviewerDownloads"))
				except OSError, e:
					pass
				self.sock.sendUrl("EXIT")
				self.downloadbox.cancelAll()
				self.downloadbox.window.destroy()
				gtk.main_quit()
				#sys.exit()
				return False
			else:
				return True
		else:
			#Clear crash recovery
			try:
				os.remove(os.path.expanduser("~/.tunesviewerDownloads"))
			except OSError, e:
				pass
			self.sock.sendUrl("EXIT")
			self.downloadbox.window.destroy()
			gtk.main_quit()
			#sys.exit()
	
	def setLoadDisplay(self,load):
		""" Shows that page is loading """
		if load:
			if self.config.throbber:
				self.throbber.show()
			self.window.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
		else:
			self.window.window.set_cursor(None)
			self.throbber.hide()
	
	def gotoURL(self,url,newurl):
		"""Downloads data, then calls update.
		If newurl is true, forward is cleared."""
		oldurl = self.url # previous url, to add to back stack.
		if self.downloading:
			return
		elif url.startswith("web://"):
			print url
			openDefault(url[6:])
			return
			#label = url[11:].split(" ")
			#print "download://"+label[0];
			#if len(label)==2:
				#name=label[0]
				#url=label[1]
				#self.downloadbox.newDownload(None,url,os.path.join(self.config.downloadfolder,name),self.opener)
		# Fix url based on http://bugs.python.org/issue918368
		try:
			url = urllib.quote(url, safe="%/:=&?~#+!$,;'@()*[]")
		except KeyError:
			#A workaround for bad input: http://bugs.python.org/issue1712522
			print "Error: unexpected input, ",url
			return
		print url
		self.downloading = True
		self.tbStop.set_sensitive(True)
		
		#Fix page-link:
		if url.startswith("http://www.apple.com/itunes/affiliates/download/"):
			if url.find("Url=")>-1:
				url = urllib.unquote(url[url.find("Url=")+4:])
			else:
				print "Dead end page"
		
		if (str.upper(url)[:4] == "ITMS" or str.upper(url)[:4] == "ITPC"):
			url = "http"+url[4:]
		elif (url==""): #no url
			self.downloading = False
			self.tbStop.set_sensitive(False)
			return
		
		#Apparently the x-apple-tz header is UTC offset *60 *60.
		self.tz = str(-time.altzone)
		self.opener.addheaders = [('User-agent', self.descView.ua),('Accept-Encoding','gzip'),('X-Apple-Tz',self.tz)]
		htmMode = self.htmlmode.get_active() #the checkbox
		if htmMode:
			self.opener.addheaders = [('User-agent', self.descView.ua),('Accept-Encoding','gzip'),("X-Apple-Tz:",self.tz),("X-Apple-Store-Front","143441-1,12")]
		if self.mobilemode.get_active():
			#as described here http://blogs.oreilly.com/iphone/2008/03/tmi-apples-appstore-protocol-g.html
			self.opener.addheaders = [('User-agent', 'iTunes-iPhone/1.2.0'),('Accept-Encoding','gzip'),('X-Apple-Store-Front:','143441-1,2')]
		#Show that it's loading:
		#self.throbber.show()
		#self.window.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
		self.setLoadDisplay(True)
		
		t = Thread(target=self.loadPageThread, args=(self.opener,url))
		self.downloading = True
		self.tbStop.set_sensitive(True)
		t.start()
		while (self.downloading):
			#Just wait... there's got to be a better way to do this?
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
			response = opener.open(url)
			self.pageType = response.info().getheader('Content-Type','noheader?')
			if self.pageType.startswith("text"):
				text = ""
				next = response.read(100)
				while (next != "" and self.downloading):
					text += next
					next = response.read(100)
				if next == "": #Finished successfully.
					self.downloadError = ""
					self.url = url
					if (response.info().get('Content-Encoding') == 'gzip'):
						orig = len(text)
						f = gzip.GzipFile(fileobj=StringIO(text))
						try:
							text = f.read()
							print "Gzipped response: ",orig,"->",len(text)
						except IOError, e:#bad file
							print e
					self.source = text
				else:
					self.downloadError = "stopped."
			else:
				pass #TODO: Download it
			
			response.close()
			
		except Exception, e:
			self.downloadError = "Download Error:\n"+str(e)
			print e
		self.downloading = False
		self.tbStop.set_sensitive(False)
	
	def update(self):
		""" Updates display based on the current html or xml in self.source """
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
		
		#Parse the page and display:
		print "PARSING"
		parser = Parser(self, self.url, self.pageType, self.source)
		print "Read page,",len(parser.mediaItems),"items, source=",parser.HTML[0:20],"..."
		if (parser.Redirect != ""):
			self.gotoURL(parser.Redirect, True)
		elif len(parser.mediaItems)==1 and parser.HTML=="":
			#Single item description page.
			self.startDownload(parser.mediaItems[0])
		else: #normal page, show it:
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
			
			#Load data:
			self.descView.loadHTML(parser.HTML,self.url)
			print "ITEMS:",len(parser.mediaItems)
			for item in parser.mediaItems:
				self.liststore.append(item)
			self.window.set_title(parser.Title)
			
			#Get the icons for all the rows:
			self.updateListIcons()
			
			#specific item should be selected?
			for i in self.liststore:
					if i[11]==parser.itemId:
						print "selecting item",parser.itemId
						self.treeview.get_selection().select_iter(i.iter)
						self.treeview.scroll_to_cell(i.path,None,False,0,0)
						#self.treeview.grab_focus()
			#Enable podcast-buttons if this is podcast:
			self.tbCopy.set_sensitive(parser.podcast!="")
			self.tbAddPod.set_sensitive(parser.podcast!="")
			self.addpodmenu.set_sensitive(parser.podcast!="")
			
			#No item selected now, disable item buttons.
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
		
	def updateListIcons(self):
		""" Sets the icons in the liststore based on the media type. """
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

class VWin:
	def __init__(self,title,source):
		"""When initialized, this will show a new window with text."""
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
print "TunesViewer 1.3"
prog = TunesViewer()
prog.sock = SingleWindowSocket(url,prog)
#Only run if it isn't already running:
if prog.sock.RUN:
	prog.url = url
	prog.main()
else:
	print "Sending url to already-running window."