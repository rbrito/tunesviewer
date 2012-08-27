#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A subclass of Webkit Webview, injects javascript into page.

 Copyright (C) 2009 - 2012 Luke Bryan
               2011 - 2012 Rogério Theodoro de Brito
               and other contributors.

 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.
"""

import logging
import os

import webkit

from constants import USER_AGENT
from inspector import Inspector
from common import openDefault, type_of

class WebKitView(webkit.WebView):
	"""
	The main browser view. Shows the page, or a description of the
	podcast page.

	Instantiated as Tunesviewer.descView.
	"""
	def __init__(self, opener):
		"""
		In this code, we set user-agent of this webkit view based on
		code from:

		http://nullege.com/codes/show/src%40p%40r%40PrisPy-HEAD%40PrisPy.py/33/webkit.WebView/python
		"""
		self.opener = opener
		webkit.WebView.__init__(self)
		self.set_highlight_text_matches(True)
		settings = self.get_settings()
		self.ua = settings.get_property('user-agent')
		if self.ua.find("AppleWebKit") > -1:
			# Without this, javascript will give many javascript
			# errors on item mouseover, TypeError: Result of
			# expression 'a' [null] is not an object.  in
			# its.webkitVersion
			self.ua = USER_AGENT+' ' + self.ua[self.ua.find("AppleWebKit"):]
		else:
			self.ua = USER_AGENT
		settings.set_property('user-agent', self.ua)
		
		# These might possibly improve dns response?
		settings.set_property('enable-dns-prefetching', False)
		settings.set_property('enable-site-specific-quirks',True)
		
		# Enable inspector:
		settings.set_property("enable-developer-extras", True)
		self._inspector = Inspector(self.get_web_inspector())
		self.set_settings(settings)

		# These signals are documented in webkit.WebView.__doc__
		self.connect("load-finished", self.webKitLoaded)
		self.connect("navigation-policy-decision-requested", self.webkitGo)
		self.connect("new-window-policy-decision-requested", self.newWin) #requires webkit 1.1.4
		self.connect("download-requested", self.downloadReq)
		current = os.path.dirname(os.path.realpath(__file__))
		self.injectJavascript = file(os.path.join(current, "Javascript.js"),
					     "r").read()

	def webKitLoaded(self, view, frame):
		"""
		Onload code.
		Note that this is run many times.
		"""
		pass
	
	def newWin(self, view, frame, request, nav_action, policy_decision):
		"""
		Calls the default browser on external link requests.
		"""
		openDefault(request.get_uri())
		# According to the documentation: http://webkitgtk.org/reference/webkitgtk/stable/webkitgtk-webkitwebview.html#WebKitWebView-new-window-policy-decision-requested
		# call ignore on the policy decision, then return true (that is, we handled it).
		policy_decision.ignore()
		return True

	def downloadReq(self, view, download):
		"""
		Signal called on right click, save-something.
		"""
		uri = download.get_uri()
		self.opener.downloadFile(uri,"unknown","",type_of(uri),uri,uri)

	def loadHTML(self, html_string, url_to_load):
		"""
		Loads an string containing HTML content from html_string
		into the webview.
		"""
		self.webkitLoading = True
		self.load_html_string(html_string.replace("<head>","<head><script>%s</script>" % self.injectJavascript), url_to_load)
		self.webkitLoading = False

	def webkitGo(self, view, frame, net_req, nav_act, pol_dec):
		logging.debug("webkit-request.")
		logging.debug(str(net_req))
		if not self.webkitLoading:
			# Don't load in browser, let this program download/convert it...
			logging.debug("Noload")
			logging.debug(net_req.get_uri())
			self.opener.gotoURL(net_req.get_uri(), True)
			return True
