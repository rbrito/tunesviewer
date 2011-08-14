import re, gc, time
from common import *
from lxml import etree

class Parser:
	
	def __init__(self,mainwin,url,source):
		#Initialized each time...
		self.Redirect = "" # URL to redirect to.
		self.Title = ""
		self.HTML = "" # The description-html, top panel.
		self.itemId = "" # The specific item selected.
		self.NormalPage = False
		self.podcast = ""
		self.mediaItems = [] #List of items to place in Liststore.
		#If only one item and no page description, this is a download link, download it.
		
		self.mainwin = mainwin
		self.source = source
		self.url = url
		sttime = time.time()
		try:
			#remove bad xml (see http://stackoverflow.com/questions/1016910/how-can-i-strip-invalid-xml-characters-from-strings-in-perl)
			bad = "[^\x09\x0A\x0D\x20-\xD7FF\xE000-\xFFFD]"#\x10000-\x10FFFF]"
			self.source = re.sub(bad," ",self.source) # now it should be valid xml.
			dom = etree.fromstring(self.source.replace('xmlns="http://www.apple.com/itms/"',''))#(this xmlns causes problems with xpath)
			#Some pages may have root element {http://www.w3.org/1999/xhtml}html
			if dom.tag.find("html")>-1 or dom.tag=="{http://www.w3.org/2005/Atom}feed":
				#Don't want normal pages/atom pages, those are for the web browser!
				raise Exception
		except Exception, e:
			print "Not XML - ERR", e
			if (self.source.lower().find('<html')>-1):
				print "Parsing HTML"
				self.HTML = self.source;
				import lxml.html
				dom = lxml.html.document_fromstring(self.source.replace('<html xmlns="http://www.apple.com/itms/"','<html'))
			#elif (self.source != ""): # There is data, but invalid data.
				#self.NormalPage = True
				# This breaks some pages, endless redirects.
				
				#msg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_YES_NO,
				#		"This seems to be a page that should open with a web browser:\n%s\nDo you want to view it?" % self.url)
				#if msg.run()==gtk.RESPONSE_YES:
				#	openDefault(self.url)
				#self.descView.loadHTML("(This page should be opened in a web browser)","about:")
				#HTMLSet = True
				#msg.destroy()
				#return
			else:
				print "unknown source:",self.source
				return
		self.removeOldData(dom)
		
		items = []
		arr = self.getItemsArray(dom) # get the tracks list element
		
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
				if self.textContent(section).find(">")>-1:
					section.getparent().remove(section) # redundant section > section ... info is removed.
		
		#initialize last-seen variables to nothing, then recursively look at every element, starting with documentElement:
		self.last_el_link = ""
		self.last_el_pic = ""
		self.last_text = ""
		self.addingD = False
		self.bgcolor = ""
		if dom.tag=="html":
			self.seeHTMLElement(dom)
		else:
			#XML parsing still needs work
			self.seeXMLElement(dom,False)
		
		if arr == None:
			ks = dom.xpath("/Document/Protocol/plist/dict/array/dict")
			if len(ks):
				arr = ks
				print "Special end page after html link?"
				
		print "tag",dom.tag
		if dom.tag=="rss": #rss files are added
			self.HTML += "<p>This is a podcast feed, click Add to Podcast manager button on the toolbar to subscribe.</p>"
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
				self.addItem(title,author,duration,typeof(url),description,pubdate,"",linkurl,url,"","")
		
		if arr == None: #No tracklisting.
			hasmedia=False
			if len(self.mediaItems)==0: #blank.
				print "nothing here!"
				for i in keys:
					if i.text == "url" or i.text == "feedURL":
						el = i.getnext()
						url = el.text
						#Redirect page, add link:
						self.HTML += "<br><a href=\"%s\">(%s redirect)</a>" % (url,i.text)
						self.Redirect = url
					elif i.text=="explanation" or i.text=="message":
						self.HTML += self.textContent(i.getnext())+"\n"
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
					self.addItem(name,artist,timeFind(duration), typeof(directurl),rtype+comments,self.formatTime(releaseDate),self.formatTime(modifiedDate), url,directurl,"",id)
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
				self.HTML += self.imgText(image[0].text, h, w)
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
					self.Title = (dom.xpath("/rss/channel/title")[0].text)
				except IndexError,e:
					pass
		else:
			out = " > ".join(location)+"\n"
			self.Title = (out[:-1])
			out = ""
			for i in range(len(location)):
				out += "<a href=\""+locationLinks[i]+"\">"+location[i]+"</a> &gt; "
			out = out [:-6]
			if dom.tag == "html":
				self.Title = dom.xpath("/html/head/title")[0].text_content()
		
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
			#Maybe redundant, with the subscribe links working.
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
					if not(buttons[0].get("subscribe-podcast-url").startswith("http://itunes.apple.com/WebObjects/DZR.woa/wa/subscribePodcast?id=")):
						self.podcast = buttons[0].get("subscribe-podcast-url")
		
		print "Parse took",time.time()-sttime,"s."
		
		#pics = dom.xpath("//PictureView")
		#if len(pics)>0: #get main picture for this page... Messy code, need a better way to do this, the Java Android-Tunesviewer parser is much better.
				#num = 0
				#while (num<len(pics) and (( pics[num].get("height")=="550") or ( (pics[num].get("alt")=="Explicit" or pics[num].get("alt")=="Clean")))):
					#num+=1 # skip this one
				#if num<len(pics): # didn't go off end of list
					#h = pics[num].get("height")
					#w = pics[num].get("width")
					#pic = pics[num].get("url")
					#HTMLImage = self.imgText(pic, h, w)
		
		
		#Done with this:
		del dom
		# avoid possible memory leak: http://faq.pygtk.org/index.py?req=show&file=faq08.004.htp
		gc.collect()
		
		if self.url.find("?i="): # link to specific item, select it.
			self.itemId = self.url[self.url.rfind("?i=")+3:]
			self.itemId = self.itemId.split("&")[0]
			
		#test console:
		#while True:
		#		print eval(raw_input(">"))
		
		print "update took:",(time.time() - sttime),"seconds"
		#if not(HTMLSet):
		#	self.mainwin.descView.loadHTML("<html><style>img {float:left; margin-right:6px; -webkit-box-shadow: 0 3px 5px #999999;}</style><body bgcolor=\""+self.bgcolor+"\">"+HTMLImage+out.replace("\n","<br>")+"<p>"+self.Description.replace("\n","<br>")+"</body></html>","about:");

	def seeXMLElement(self,element,isheading):
		""" Recursively looks at xml elements. """
		if isinstance(element.tag,str):
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
						author = self.textContent(nexttext).strip()
					if name != "":
						#text link. Does it have picture?
						arturl = ""
						if self.last_el_link == urllink:
							arturl = self.last_el_pic
							#(last pic was the icon for this, it will be added:)
							self.Description += "<img src=\"%s\" width=%s height=%s>" % (self.last_el_pic, self.config.imagesizeN, self.config.imagesizeN)
						self.Description += "<a href=\"%s\">%s</a><br>" % (urllink, HTmarkup(name,isheading));
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
				#if urllink and urllink[0:4]!="itms":
					#urllink = "WEB://"+urllink
				name = self.textContent(element).strip()
				if element.get("draggingName"):
					author = element.get("draggingName")
				else:
					author = ""
				#See if there is text right after it for author.
				nexttext = element.getparent().getparent().getnext()
				# If there's a TextView-node right after, it should be the author-text or college name.
				if nexttext != None and isinstance(nexttext.tag,str) and nexttext.tag == "TextView":
					author = self.textContent(nexttext).strip()
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
					#if True:# self.addingD: # put in description (top box)
					self.Description += "\n%s\n<br>" % text.strip()
					self.last_text = text.strip()
				if goto != None:
					for i in element:
						if isinstance(i.tag,str):
							self.seeXMLElement(i,isheading)
			else:
				#sometimes podcast ratings are in hboxview alt, get the text alts.
				if element.tag == "HBoxView" and element.get("alt"): #and element.getAttribute("alt").lower()!=element.getAttribute("alt").upper():
					self.Description += HTmarkup(element.get("alt"),False)
				
				# Recursively do this to all elements:
				for node in element:
					self.seeXMLElement(node,isheading)
		elif type(element).__name__=='_Comment': #element.nodeType == element.COMMENT_NODE:
			# Set it to add the description to self.Description when it is between these comment nodes:
			if element.text.find("BEGIN description")>-1:
				self.addingD = True
			elif element.text.find("END description")>-1:
				self.addingD = False
	
	def seeHTMLElement(self,element):
		if isinstance(element.tag,str): # normal element
			if element.tag=="tr" and element.get("class") and (element.get("class").find("track-preview")>-1 or element.get("class").find("podcast-episode")>-1 or element.get("class").find("song")>-1 or element.get("class").find("video")>-1):
				#You'll find the info in the rows using the inspector (right click, inspect).
				title=""; exp=""; itemid=""; artist = ""; time=""; url = ""; comment = ""; releaseDate=""; gotou = ""; price=""
				if element.get("adam-id"):
					itemid=element.get("adam-id")
				if element.get("preview-title"):
					title = element.get("preview-title")
				if element.get("preview-artist"):
					artist = element.get("preview-artist")
				if element.get("duration"):
					time = timeFind(element.get("duration"))
				if element.get("rating-riaa") and element.get("rating-riaa")!="0":
					exp = "[Explicit] "
				if element.get("audio-preview-url"):
					url = element.get("audio-preview-url")
				elif element.get("video-preview-url"):
					url = element.get("video-preview-url")
				type = typeof(url)
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
						if cl.find("price")>-1:
							price = val
				self.mediaItems.append([None,markup(title,False),artist,time,type,exp+comment,releaseDate,"",gotou,url,price,itemid])
			elif element.get("audio-preview-url") or element.get("video-preview-url"): #Ping audio/vid.
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
				self.mediaItems.append([None,markup(title,False),author,duration,typeof(url),"","","","",url,"",""])
			elif element.tag=="button" and element.get("anonymous-download-url") and element.get("title"):#Added for epub feature
				self.mediaItems.append([None,markup(element.get("title"),False),element.get("item-name"),"",typeof(element.get("anonymous-download-url")),"","","",element.get("anonymous-download-url"),"","",""])#Special 
			else: # go through the childnodes.
				for i in element:
					self.seeHTMLElement(i)
	
	def getItemsArray(self,dom):
		""" Tries to get the array element of the dom, returns None if it doesn't exist. """
		array = None
		els = dom.xpath("/Document/TrackList/plist/dict/key")#isinstance(i.tag,str) and i.tag == "key" and 
		for i in els: #all childnodes:
			if (i.text=="items"):
				array = i.getnext()
		return array
	
	def removeOldData(self,dom):
		"""
		Removes xml nodes like <Test comparison="lt" value="7.1" property="iTunes version">
		Including these would make many duplicates.
		
		This function is unnecessary, we'll just ignore during recursive parsing, in the future."""
		tests = dom.xpath("//Test") # get all <test> elements
		for i in tests:
			if (i.get("comparison")=="lt" or (i.get("comparison") and i.get("comparison").find("less")>-1)):
				i.getparent().remove(i)
	
	def addItem(self,title,author,duration,type,comment,releasedate,datemodified, gotourl, previewurl, price, itemid):
		"Adds item to list."
		self.mediaItems.append([None,markup(title,False),author,duration,type,comment,releasedate,datemodified,gotourl,previewurl,price,itemid])
	
	
	def getTextByClass(self,element,classtext):
		if element.get("class") == classtext:
			return element.text_content()
		else:
			out = ""
			for i in element:
				out += self.getTextByClass(i,classtext)
			return out
	
	def textContent(self,element):
		""" Gets all text content of the node. """
		#out = element.text
		#for i in element.itertext(): # includes comment nodes... :(
		#	out += i
		#return out
		out = []
		if type(element).__name__=="_Element":
			if element.text:
				out.append( element.text )
			for i in element:
				out.append(self.textContent(i))
				if i.tail:
					out.append(i.tail)
		return "".join(out)
		
	def searchLink(self,element):
		""" Given an element, finds all text in it and the link in it (if any). """
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
	
	def hasAlink(self,element):
		if isinstance(element.tag,str):
			if element.tag=="a":
				return True
			else:
				for i in element:
					if self.hasAlink(i):
						return True
				return False
	
	def formatTime(self,text):
		""" Changes the weird DateTTimeZ format found in the xml date-time. """
		return text.replace("T"," ").replace("Z"," ")
	
	def getImgUrl(self,element): # find the image
		if isinstance(element.tag,str) and element.tag == "img":
			return element.get("src")
		else:
			for i in element:
				out = self.getImgUrl(i)
				if out:
					return out
			return ""
	
	def imgText(self,picurl,height,width):
		if height and width:
			return '<img src="%s" height="%s" width="%s">' % (picurl, height, width)
		else:
			return '<img src="%s">' % picurl
	