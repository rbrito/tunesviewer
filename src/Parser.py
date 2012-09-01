#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
The main parser to turn iTunesU xml/html into viewable page

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

import gc
import logging
import re
import time

from lxml import etree
import lxml.html

from common import *


def safe(obj):
	"""
	Makes an object safe to add to string, even if it is NoneType.
	"""
	if obj:
		return obj
	else:
		return ""
		
ATOM = "{http://www.w3.org/2005/Atom}feed"

class Parser:
	def __init__(self, url, contentType, source):
		# Initialized each time...
		self.Redirect = "" # URL to redirect to.
		self.Title = ""
		self.HTML = "" # The description-html, top panel.
		self.itemId = "" # The specific item selected.
		self.singleItem = False
		self.NormalPage = False
		self.podcast = ""
		self.bgcolor = ""
		self.mediaItems = [] #List of items to place in Liststore.
		self.tabMatches = []
		self.tabLinks = []
		self.last_text = "" # prevent duplicates from shadow-text.

		self.url = url
		self.contentType = contentType
		self.source = source
		sttime = time.time()
		try: #parse as xml
			# Remove bad XML. See:
			# http://stackoverflow.com/questions/1016910/how-can-i-strip-invalid-xml-characters-from-strings-in-perl
			bad = "[^\x09\x0A\x0D\x20-\xD7FF\xE000-\xFFFD]"
			self.source = re.sub(bad, " ", self.source) # now it should be valid xml.
			dom = etree.fromstring(self.source.replace('xmlns="http://www.apple.com/itms/"', '')) #(this xmlns causes problems with xpath)
			if dom.tag.find("html") > -1:# or dom.tag == "{http://www.w3.org/2005/Atom}feed":
				# Don't want normal pages/atom pages, those are for the web browser!
				raise Exception
			elif dom.tag == "rss" or dom.tag == ATOM: # rss files are added
				self.HTML += "<p>This is a podcast feed, click Add to Podcast manager button on the toolbar to subscribe.</p>"
				items = dom.xpath("//item")
				logging.debug("rss: " + str(len(items)))
				for item in items:
					title = ""
					author = ""
					linkurl = ""
					duration = ""
					url = ""
					description = ""
					pubdate = ""
					for i in item:
						if i.tag == "title":
							title = i.text
						elif i.tag == "author" or i.tag.endswith("author"):
							author = i.text
						elif i.tag == "link":
							linkurl = i.text
						elif i.tag == "description":
							description = i.text
						elif i.tag == "pubDate":
							pubdate = i.text
						elif i.tag == "enclosure":
							url = i.get("url")
						elif i.tag.endswith("duration"):
							duration = i.text
					self.addItem(title,
						     author,
						     duration,
						     type_of(url),
						     description,
						     pubdate,
						     "",
						     linkurl,
						     url,
						     "",
						     "")
			else:
				self.seeXMLElement(dom)
		except Exception as e:
			logging.debug("ERR: " + str(e))
			logging.debug("Parsing as HTML, not as XML.")
			ustart = self.source.find("<body onload=\"return open('")
			if ustart > -1:  # This is a redirect-page.
				newU = self.source[ustart+27:self.source.find("'", ustart+27)]
				self.Redirect = newU
			logging.debug("Parsing HTML")
			self.HTML = self.source
			dom = lxml.html.document_fromstring(self.source.replace('<html xmlns="http://www.apple.com/itms/"', '<html'))
			self.seeHTMLElement(dom)

		items = []
		arr = self.getItemsArray(dom) # get the tracks list element

		keys = dom.xpath("//key") # important parts of document! this is only calculated once to save time
		# Now get location path:
		# location description and links and last location in location bar.
		location = []
		locationLinks = []
		lastloc = ""
		locationelements = dom.xpath("//Path")
		if len(locationelements) > 0:
			for i in locationelements[0]:
				if (type(i).__name__ == '_Element' and i.tag == "PathElement"):
					location.append(i.get("displayName"))
					locationLinks.append(i.text)

		if location == ["iTunes U"]:
			section = dom.xpath("//HBoxView") # looking for first section with location info.
			if len(section) > 0: # may be out of range
				section = section[0]
				for i in section:
					if (type(i).__name__ == '_Element'):
						for j in i:
							if type(j).__name__ == '_Element' and j.tag == "GotoURL":
								location.append(j.text.strip())
								locationLinks.append(j.get("url"))
								logging.debug(j.text.strip() + j.get("url"))
								lastloc = j.get("url")
				if self.textContent(section).find(">") > -1:
					section.getparent().remove(section) # redundant section > section ... info is removed.

		if arr is None:
			ks = dom.xpath("/Document/Protocol/plist/dict/array/dict")
			if len(ks):
				arr = ks
				logging.debug("Special end page after html link?" + str(len(ks)))
				if (len(ks) == 1 and
				    dom.get("disableNavigation") == "true" and
				    dom.get("disableHistory") == "true"):
					self.singleItem = True
		logging.debug("tag " + dom.tag)

		if arr is None: # No tracklisting.
			hasmedia = False
			if len(self.mediaItems) == 0:
				logging.debug("nothing here!")
		else: # add the tracks:
			# TODO: Add XML page's elements to the top panel, so the bottom panel isn't necessary.
			hasmedia = True
			# for each item...
			for i in arr:
				if type(i).__name__ == '_Element' and i.tag == "dict":
					# for each <dict> track info....</dict> get this information:
					name = ""
					artist = ""
					duration = ""
					comments = ""
					rtype = ""
					url = ""
					directurl = ""
					releaseDate = ""
					modifiedDate = ""
					id = ""
					for j in i:
						if j.tag == "key": # get each piece of data:
							if j.text in ["songName", "itemName"]:
								t = j.getnext().text
								if t:
									name = t
							elif j.text == "artistName":
								t = j.getnext().text
								if t:
									artist = t
							elif j.text == "duration":
								t = j.getnext().text
								if t:
									duration = t
							elif j.text in ["comments", "description", "longDescription"]:
								t = j.getnext().text
								if t:
									comments = t
							elif j.text == "url":
								t = j.getnext().text
								if t:
									url = t
							# Added Capital "URL", for the special case end page after html link.
							elif j.text in ["URL", "previewURL", "episodeURL", "preview-url"]:
								t = j.getnext().text
								if t:
									directurl = t
							elif j.text == "explicit":
								el = j.getnext()
								if el.text == "1":
									rtype = "[Explicit] "
								if el.text == "2":
									rtype = "[Clean] "
							elif j.text == "releaseDate":
								t = j.getnext().text
								if t:
									releaseDate = t
							elif j.text == "dateModified":
								t = j.getnext().text
								if t:
									modifiedDate = t
							elif j.text == "itemId":
								t = j.getnext().text
								if t:
									id = t
							elif j.text == "metadata": # for the special case end page after html link
								i.extend(j.getnext().getchildren()) # look inside this <dict><key></key><string></string>... also.
					self.addItem(name,
						     artist,
						     time_convert(duration),
						     type_of(directurl),
						     rtype + comments,
						     self.formatTime(releaseDate),
						     self.formatTime(modifiedDate),
						     url,
						     directurl,
						     "",
						     id)

		# Now put page details in the detail-box on top.
		if dom.tag == "rss":
			out = ""
			image = dom.xpath("/rss/channel/image/url")
			if len(image) > 0:
				# get recommended width, height:
				w, h = None, None
				try:
					w = dom.xpath("/rss/channel/image/width")[0].text
					h = dom.xpath("/rss/channel/image/height")[0].text
				except:
					pass
				self.HTML += self.imgText(image[0].text, h, w)
			#else: # TODO: fix this namespace problem
				#image = dom.xpath("/rss/channel/itunes:image",namespaces={'itunes': 'http://www.itunes.com/DTDs/Podcast-1.0.dtd'})[0]
				#if len(image)>0...
			channel = dom.xpath("/rss/channel")
			if len(channel):
				for i in channel[0]:
					if not(image) and i.tag == "{http://www.itunes.com/dtds/podcast-1.0.dtd}image":
						self.HTML += self.imgText(i.get("href"), None, None)
				for i in channel[0]:
					if i.text and i.text.strip() != "" and isinstance(i.tag, str):
						thisname = "".join(i.tag.replace("{", "}").split("}")[::2]) # remove {....dtd} from tag
						self.HTML += "<b>%s:</b> %s\n<br>" % (thisname, i.text)
				try:
					self.Title = (dom.xpath("/rss/channel/title")[0].text)
				except IndexError as e:
					logging.warn('Error using index ' + str(e))
		else:
			out = " > ".join(location) + "\n"
			self.Title = (out[:-1])
			out = ""
			for i in range(len(location)):
				out += "<a href=\"" + safe(locationLinks[i]) + "\">" + safe(location[i]) + "</a> &gt; "
			out = out[:-6]
			if dom.tag == "html":
				try:
					self.Title = dom.xpath("/html/head/title")[0].text_content()
				except IndexError as e:
					logging.warn('Error extracting title: ' + str(e))
					self.Title = "TunesViewer"
		self.HTML = "<html><body bgcolor=\"" + self.bgcolor + "\">" + self.HTML + "</body></html>"

		# Get Podcast url
		# already have keys = dom.xpath("//key")
		self.podcast = ""
		if len(location) > 0 and location[0] == "Search Results":
			logging.debug("Search page, not podcast.")
		elif dom.tag == "rss" or dom.tag==ATOM:
			self.podcast = self.url
		elif hasmedia:
			for i in keys:
				if i.text == "feedURL":
					self.podcast = i.getnext().text # Get next text node's text.
					logging.debug("Podcast: " + self.podcast)
					break
			if self.podcast == "":
				#Last <pathelement> should have the page podcast url, with some modification.
				self.podcast = lastloc
				if lastloc == "":
					self.podcast = self.url
				if self.podcast.find("/Browse/") > -1:
					self.podcast = self.podcast.replace("/Browse/", "/Feed/")
				elif self.podcast.find("/BrowsePrivately/") > -1:
					self.podcast = self.podcast.replace("/BrowsePrivately/", "/Feed/")
					# If it's a protected podcast, it will have special goto-url:
					pbvs = dom.xpath("//PictureButtonView")
					for pbv in pbvs:
						if pbv.get("alt") == "Subscribe":
							self.podcast = pbv.getparent().get("draggingURL")
				else:
					logging.debug("Not a podcast page.")
		else: # not a podcast page? Check for html podcast feed-url in page:
			#Maybe redundant, with the subscribe links working.
			buttons = dom.xpath("//button")
			if len(buttons):
				isPod = True
				podurl = buttons[len(buttons)-1].get("feed-url") #the last feed-url, see if all feed-urls are this one.
				for b in buttons:
					if (b.get("feed-url") and
					    b.get("feed-url") != podurl): #has feed-url, but it's different.
						isPod = False
				if isPod and podurl: # Every media file has link to same url, so it must be podcast url of this page.
					self.podcast = podurl
				elif (len(buttons) > 1):
					if buttons[0].get("subscribe-podcast-url"):
						if not(buttons[0].get("subscribe-podcast-url").startswith("http://itunes.apple.com/WebObjects/DZR.woa/wa/subscribePodcast?id=")):
							self.podcast = buttons[0].get("subscribe-podcast-url")
					elif buttons[0].get("course-feed-url") and buttons[1].get("course-feed-url") is None:
						# Single "subscribe", not a listing-page.
						self.podcast = buttons[0].get("course-feed-url")

		logging.debug("Parse took " + str(time.time()-sttime) + "s.")

		# Done with this:
		del dom
		# avoid possible memory leak: http://faq.pygtk.org/index.py?req=show&file=faq08.004.htp
		gc.collect()

		if self.url.find("?i="): # link to specific item, select it.
			self.itemId = self.url[self.url.rfind("?i=")+3:]
			self.itemId = self.itemId.split("&")[0]

		logging.debug("Update took " + str(time.time()-sttime) + "seconds")

	def seeXMLElement(self, element):
		"""
		Recursively looks at xml elements.
		"""
		if isinstance(element.tag, str):
			# Good element, check this element:
			if element.get("backColor") and self.bgcolor == "":
				self.bgcolor = element.get("backColor")
			if element.tag == "GotoURL":
				urllink = element.get("url")
				name = self.textContent(element).strip()
				if element.get("draggingName"):
					author = element.get("draggingName")
				else:
					author = ""
				# See if there is text right after it for author.
				nexttext = element.getparent().getparent().getnext()
				match = re.match("Tab [0-9][0-9]* of [0-9][0-9]*", author)
				if match: # Tab handler
					logging.debug("ADDTAB " + match.group(0) + " " + urllink)
					match = author[match.end():]
					self.tabMatches.append(match)
					self.tabLinks.append(urllink)
				else:
					self.HTML += "<a href=\"%s\">" % element.get("url")
					for i in element:
						self.seeXMLElement(i)
					self.HTML += safe(element.text) + "</a>" + safe(element.tail)
			elif element.tag == "FontStyle":
				if element.get("styleName") == "default":
					self.HTML += "<style> * {color: %s; font-family: %s; font-size: %s;}</style>" % \
					(safe(element.get("color")), safe(element.get("font")), safe(element.get("size")))
			elif element.tag == "HBoxView":
				self.HTML += "<!--HBox--><table><tr>"
				for node in element:
					self.HTML += "<td>"
					self.seeXMLElement(node)
					self.HTML += "</td>"
				self.HTML += "</tr></table>"
			elif element.tag == "VBoxView":
				self.HTML += "<!--VBox--><table width='100%'>"
				for node in element:
					self.HTML += "<tr><td>"
					previousLen = len(self.HTML)
					self.seeXMLElement(node)
					if (len(self.HTML) == previousLen):
						self.HTML = self.HTML[:-8] # no empty row.
					else:
						self.HTML += "</td></tr>"
				self.HTML += "</table>"
			elif element.tag == "PictureView":
				if element.get("url"):
					self.HTML += self.imgText(element.get("url"),
								  element.get("height"),
								  element.get("width"))
				else:
					self.HTML += self.imgText(element.get("src"),
								  element.get("height"),
								  element.get("width"))
				for node in element:
					self.seeXMLElement(node)
				self.HTML += "</img>"
			elif element.tag == "OpenURL":
				urllink = element.get("url")
				if urllink and urllink[0:4] != "itms":
					urllink = "WEB" + urllink
				name = self.textContent(element).strip()
				if element.get("draggingName"):
					author = element.get("draggingName")
				else:
					author = ""
				# See if there is text right after it for author.
				nexttext = element.getparent().getparent().getnext()
				# If there's a TextView-node right after, it should be the author-text or college name.
				if nexttext != None and isinstance(nexttext.tag, str) and nexttext.tag == "TextView":
					author = self.textContent(nexttext).strip()
				self.HTML += "<a href=\"%s\">%s" % (urllink, HTmarkup(name, False))
				#if urllink and urllink[0:4]=="itms":
					#lnk = "(Link)"
				#else:
					#lnk = "(Web Link)"
			elif (element.tag == "key" and
			      element.text == "action" and
			      element.getnext() is not None):
				#Page action for redirect.
				#Key-val map is stored in <key>name</key><tag>value(s)</tag>
				keymap = {}
				for node in element.getnext():
					if node.tag == "key" and node.getnext() is not None:
						keymap[node.text] = node.getnext().text
				logging.debug(keymap)
				if ("kind" in keymap and
				    keymap["kind"] in ["Goto", "OpenURL"] and
				    "url" in keymap):
					self.Redirect = keymap["url"]
			elif (element.tag == "key" and
			      element.getnext() is not None and
			      element.text in ["message", "explanation", "customerMessage"]):
				self.HTML += "<p>%s</p>" % element.getnext().text
			elif (element.tag == "key" and
			      element.getnext() is not None and
			      element.text == "subscribe-podcast" and
			      element.getnext().tag == "dict"):
				for node in element.getnext():
					if (node.tag == "key" and
					    node.getnext() is not None and
					    node.text == "feedURL"):
						self.Redirect = node.getnext().text
			elif (element.tag == "key" and
			      element.getnext() is not None and
			      element.text == "kind" and
			      element.getnext().text == "Perform" and
			      element.getnext().getnext() is not None and
			      element.getnext().getnext().text == "url" and
			      element.getnext().getnext().getnext() is not None):
				self.Redirect = element.getnext().getnext().getnext().text
				logging.debug("REDIR" + self.Redirect)
			elif (element.tag == "Test" and
			      (element.get("comparison").startswith("lt") or
			       element.get("comparison") == "less")):
				pass #Ignore older version info, it would cause duplicates.
			elif (element.tag == "string" or
			      (element.getprevious() is not None and
			       element.getprevious().tag == "key" and element.tag != "dict") or
			      element.tag in ["key", "MenuItem", "iTunes", "PathElement", "FontStyleSet"]):
				pass
			else:
				self.HTML += "<%s>" % element.tag
				if element.text and element.text.strip() != "":
					#Workaround for double text that is supposed to be shadow.
					#There is probably a better way to do this?
					if self.last_text.strip() != element.text.strip():
						self.HTML += element.text
						self.last_text = element.text
					else: #same, ignore one.
						self.last_text = ""
				# Recursively see all elements:
				for node in element:
					self.seeXMLElement(node)
				self.HTML += "</%s>%s" % (element.tag, safe(element.tail))

	def seeHTMLElement(self, element):
		if isinstance(element.tag, str): # normal element
			if (element.get("comparison") == "lt" or
			    (element.get("comparison") and
			     element.get("comparison").find("less") > -1)):
				return #Ignore child nodes.
			if element.tag == "tr" and element.get("dnd-clipboard-data"):
				import json
				data = json.loads(element.get("dnd-clipboard-data"))
				itemid = ""
				title = ""
				artist = ""
				duration = ""
				url = ""
				gotou = ""
				price = "0"
				comment = ""
				if ('itemName' in data):
					title = data['itemName']
				if ('artistName' in data):
					artist = data['artistName']
				if ('duration' in data):
					duration = time_convert(data['duration'])
				if ('preview-url' in data):
					url = data['preview-url']
				if ('playlistName' in data):
					comment = data['playlistName']
				if ('url' in data):
					gotou = data['url']
				if ('price' in data):
					price = data['price']
				if ('itemId' in data):
					itemid = data['itemId']
				self.addItem(title,
					     artist,
					     duration,
					     type_of(url),
					     comment,
					     "",
					     "",
					     gotou,
					     url,
					     price,
					     itemid)
			elif (element.get("audio-preview-url") or
			      element.get("video-preview-url") or
			      element.get("episode-url")):
				if element.get("video-preview-url"):
					url = element.get("video-preview-url")
				elif element.get("episode-url"):
					url = element.get("episode-url")
				else:
					url = element.get("audio-preview-url")
				title = ""
				if element.get("preview-title"):
					title = element.get("preview-title")
				elif element.get("item-name"):
					title = element.get("item-name")
				author = ""
				if element.get("preview-artist"):
					author = element.get("preview-artist")
				elif element.get("artist-name"):
					author = element.get("artist-name")
				duration = ""
				if element.get("preview-duration"):
					duration = time_convert(element.get("preview-duration"))
				logging.debug("preview-url adding row")
				self.mediaItems.append([None,
							markup(title, False),
							author,
							duration,
							type_of(url),
							"",
							"",
							"",
							"",
							url,
							"",
							""])
			elif (element.tag == "button" and
			      element.get("anonymous-download-url") and
			      element.get("kind") and
			      (element.get("title") or element.get("item-name"))):#Added for epub feature
				logging.debug("button row adding")
				title = ""
				artist = ""
				if element.get("title"):
					title = element.get("title")
				if element.get("item-name"):
					title = element.get("item-name")
				if element.get("preview-artist"):
					artist = element.get("preview-artist")
				self.addItem(title,
					     artist,
					     "",
					     type_of(element.get("anonymous-download-url")),
					     "",
					     "",
					     "",
					     element.get("anonymous-download-url"),
					     "",
					     "",
					     element.get("adam-id"))
			elif (element.tag == "button" and
			     element.get("episode-url")):
				title = ""
				artist = ""
				url = ""
				itemid=""
				if element.get("aria-label"):
					title = element.get("aria-label")
					if title.startswith("Free Episode, "):
						title = title[14:]
				if element.get("artist-name"):
					artist = element.get("artist-name")
				if element.get("episode-url"):
					url = element.get("episode-url")
				mytype = type_of(url)
				if element.get("disabled") is not None:
					mytype = ".zip" # wrong ext. fix it.
				self.addItem(title,
					     artist,
					     "",
					     mytype,
					     "",
					     "",
					     "",
					     "",
					     url,
					     "",
					     itemid)
			elif element.tag=="script" and element.get("id")=="protocol" and element.get("type")=="text/x-apple-plist":
				print ''.join([etree.tostring(child) for child in element.iterdescendants()])
			else: # go through the childnodes.
				for i in element:
					self.seeHTMLElement(i)

	def getItemsArray(self, dom):
		"""Tries to get the array element of the dom, returns None if it doesn't exist."""
		array = None
		els = dom.xpath("/Document/TrackList/plist/dict/key")#isinstance(i.tag,str) and i.tag == "key" and
		for i in els: #all childnodes:
			if i.text == "items":
				array = i.getnext()
		return array

	def addItem(self, title, author, duration, type, comment, releasedate,
		    datemodified, gotourl, previewurl, price, itemid):
		"""Adds item to media list."""
		self.mediaItems.append([None,
					markup(title, False),
					author,
					duration,
					type,
					comment,
					releasedate,
					datemodified,
					gotourl,
					previewurl,
					price,
					itemid])

	def textContent(self, element):
		"""Gets all text content of the node."""
		out = []
		if type(element).__name__ == "_Element":
			if element.text:
				out.append(element.text)
			for i in element:
				out.append(self.textContent(i))
				if i.tail:
					out.append(i.tail)
		return "".join(out)

	def formatTime(self, text):
		"""Changes the weird DateTTimeZ format found in the xml date-time."""
		return text.replace("T", " ").replace("Z", " ")

	def imgText(self, picurl, height, width):
		"""Returns html for an image, given url, height, width."""
		if height and width:
			return '<img src="%s" height="%s" width="%s">' % (picurl, height, width)
		else:
			return '<img src="%s">' % picurl
