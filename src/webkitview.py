import logging
import os

import webkit
from constants import USER_AGENT

from inspector import Inspector

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
		# Enable inspector:
		settings.set_property("enable-developer-extras", True)
		self._inspector = Inspector(self.get_web_inspector())
		self.set_settings(settings)

		# These signals are documented in webkit.WebView.__doc__
		self.connect("load-finished", self.webKitLoaded)
		self.connect("navigation-policy-decision-requested", self.webkitGo)
		current = os.path.dirname(os.path.realpath(__file__))
		self.injectJavascript = file(os.path.join(current, "Javascript.js"),
					     "r").read()

	def webKitLoaded(self, view, frame):
		"""
		Onload code.
		Note that this is run many times.
		"""
		# Javascript.js is executed on this page.
		self.execute_script(self.injectJavascript)

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

	#def webkitReqStart(self, webView, webFrame, webResource, NetReq, NetResp):
	#	pass
