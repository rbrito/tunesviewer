import gtk

class FindInPageBox:
	def __init__(self,mainwin):
		self.currentFound = -1
		self.mainwin = mainwin
		self.window = gtk.Dialog("Find in Current Page",None,gtk.DIALOG_DESTROY_WITH_PARENT,(gtk.STOCK_FIND,1,gtk.STOCK_CLOSE,0))
		self.window.set_size_request(250,-1)#change width
		self.window.set_default_response(1)
		self.window.set_icon(self.window.render_icon(gtk.STOCK_FIND, gtk.ICON_SIZE_BUTTON))
		self.window.connect("response",self.response) # Ok/Cancel
		vbox = self.window.get_content_area()
		vbox.pack_start(gtk.Label("Find Text:"))
		self.findText = gtk.Entry()
		self.findText.set_activates_default(True)
		vbox.pack_start(self.findText)
		self.window.connect("delete_event",self.delete_event)
	def delete_event(self, widget, event, data=None):
		self.window.hide()
		return True # Hide, don't close.
	def response(self,obj,value):
		if value == 0:
			self.window.hide()
		elif value == 1:
			#look for this text:
			findT = self.findText.get_text().lower()
			#if self.currentFound >= len(self.mainwin.liststore):
			#	self.currentFound = -1 #start over.
			while(1):
				self.currentFound+=1
				if self.currentFound >= len(self.mainwin.liststore):
					msg = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL, gtk.MESSAGE_INFO, gtk.BUTTONS_OK, "End of page.")
					msg.run()
					msg.destroy()
					self.currentFound = -1 #start at beginning.
					break
				thisrow = self.mainwin.liststore[self.currentFound]
				if str(thisrow[1]).lower().find(findT)>-1 \
					or str(thisrow[2]).lower().find(findT)>-1 \
					or str(thisrow[3]).lower().find(findT)>-1 \
					or str(thisrow[4]).lower().find(findT)>-1 \
					or str(thisrow[5]).lower().find(findT)>-1 \
					or str(thisrow[6]).lower().find(findT)>-1 \
					or str(thisrow[7]).lower().find(findT)>-1:
						print str(thisrow[1]) #this is a match.
						self.mainwin.treeview.get_selection().select_iter(thisrow.iter)
						self.mainwin.treeview.scroll_to_cell(thisrow.path,None,False,0,0)
						break
