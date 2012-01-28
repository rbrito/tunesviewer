import gobject
import gtk

class FindInPageBox(gtk.Dialog):

	__gsignals__ = {'find': (gobject.SIGNAL_RUN_FIRST,
				 gobject.TYPE_NONE,
				 (gobject.TYPE_STRING,))}

	def __init__(self):
		gtk.Dialog.__init__(self, "Find in Current Page", None,
				    gtk.DIALOG_DESTROY_WITH_PARENT,
				    (gtk.STOCK_FIND, 1, gtk.STOCK_CLOSE, 0))
		self.currentFound = -1
		self.set_size_request(250, -1) # change width
		self.set_default_response(1)
		self.set_icon(self.render_icon(gtk.STOCK_FIND, gtk.ICON_SIZE_BUTTON))
		self.connect("response", self.response) # Ok/Cancel
		vbox = self.get_content_area()
		vbox.pack_start(gtk.Label("Find Text:"))
		self.findText = gtk.Entry()
		self.findText.set_activates_default(True)
		vbox.pack_start(self.findText)
		self.connect("delete_event", self.delete_event)

	def delete_event(self, widget, event, data=None):
		self.hide()
		return True # Hide, don't close.

	def response(self, obj, value):
		if value == 0:
			self.hide()
		else:
			text = self.findText.get_text().lower()
			self.emit('find', text)
