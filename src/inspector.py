# Copyright (C) 2008 Jan Alonzo <jmalonzo@unpluggable.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import logging

from gi.repository import WebKit2
from gi.repository import Gtk as gtk

class Inspector(gtk.Window):
    def __init__ (self, inspector):
        """
        Initialize the WebInspector class.
        """
        gtk.Window.__init__(self)
        self._web_inspector = inspector

        self.connect("delete-event", self._close_window_cb)


    def _inspect_web_view_cb(self, inspector, web_view):
        """
        Called when the 'inspect' menu item is activated.
        """
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.props.hscrollbar_policy = gtk.PolicyType.AUTOMATIC
        scrolled_window.props.vscrollbar_policy = gtk.PolicyType.AUTOMATIC
        webview = WebKit2.WebView()
        scrolled_window.add(webview)
        scrolled_window.show_all()

        self.add(scrolled_window)

        ##  Modified to make window bigger, and add title  ##
        self.set_default_size(650, 400)
        self.set_title("Webkit Inspector")

        return webview


    def _show_window_cb(self, inspector):
        """
        Called when the inspector window should be displayed.
        """
        self.present()
        return True


    def _attach_window_cb(self, inspector):
        """
        Called when the inspector should be displayed in the same window as
        the WebView being inspected.
        """
        logging.debug("Inspector window attached.")
        return False


    def _detach_window_cb(self, inspector):
        """
        Called when the inspector should appear in a separate window.
        """
        logging.debug("Inspector window detached.")
        return False


    def _close_window_cb(self, inspector, web_view):
        """
        Called when the inspector window should be closed.
        """
        logging.debug("Inspector window closed.")
        self.hide()
        return True


    def _finished_cb(self, inspector):
        """
        Called when inspection is done.
        """
        logging.debug("Inspector finished.")
        self._web_inspector = 0
        self.destroy()
        return False
