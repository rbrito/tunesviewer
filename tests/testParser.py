#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
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
import sys
import unittest
import urllib2

sys.path.append('src')
sys.path.append('../src')

from Parser import Parser
from constants import USER_AGENT


# Test the parser class - Requires network!
class TestParser(unittest.TestCase):
	def setUp(self):
		"""
		Take care of the preparation of the tests.
		"""
		self.o = urllib2.build_opener()
		self.o.addheaders = [('User-agent', USER_AGENT)]

	def checkHTML(self,html):
		"""
		Checks html, makes sure important layout tags are matching with end tags.
		"""
		for tag in ["td","tr","div"]:
			#print tag, html.count("<%s>" % tag)+html.count("<%s "), html.count("</%s>" % tag)
			self.assertEqual(html.count("<%s>" % tag)+html.count("<%s "),html.count("</%s>" % tag))
			
	def checkItems(self,mediaItems):
		for line in mediaItems:
			self.assertEqual(len(line[4]), 4) # test 4-char extension.
			self.assertEqual(line[4][0], ".")
			self.assertEqual(len(line[3]), 7) # test h:mm:ss time length.

	def testParseAgriculture(self):
		url = "http://itunes.apple.com/WebObjects/DZR.woa/wa/viewPodcast?cc=us&id=387961518"
		text = self.o.open(url).read()
		parsed_html = Parser(url, "text/HTML", text)

		self.assertEqual(parsed_html.Redirect, '')
		self.assertEqual(parsed_html.Title, 'Food and Sustainable Agriculture')
		self.assertEqual(len(parsed_html.mediaItems), 7)

		# FIXME: The following should be made into proper tests
		for line in parsed_html.mediaItems:
			logging.debug(line)


	def testParseGeorgeFox(self):
		url = "https://deimos.apple.com/WebObjects/Core.woa/BrowsePrivately/georgefox.edu.01651902695"
		text = self.o.open(url).read()
		parsed_html = Parser(url, "text/HTML", text)

		# FIXME: Maybe it could be smarter about finding the title...
		self.assertEqual(parsed_html.Redirect, '')
		self.assertEqual(parsed_html.Title, 'iTunes U > Top Downloads')
		self.assertEqual(len(parsed_html.mediaItems), 0) # Not sure where the bogus element is coming from in the gui...
		self.checkItems(parsed_html.mediaItems)
			
	def testMain(self):
		url = "http://itunes.apple.com/WebObjects/MZStore.woa/wa/viewGrouping?id=27753"
		text = self.o.open(url).read()
		parsed_html = Parser(url, "text/HTML", text)

		# FIXME: Maybe it could be smarter about finding the title...
		self.assertEqual(parsed_html.Redirect, '')
		self.assertEqual(parsed_html.Title, 'iTunes U')
		self.checkItems(parsed_html.mediaItems)


	def testParseFHSU(self):
		url = "http://deimos.apple.com/WebObjects/Core.woa/Browse/fhsu.edu"
		text = self.o.open(url).read()
		parsed_html = Parser(url, "text/HTML", text)

		# FIXME: Maybe it could be smarter about finding the title...
		self.assertEqual(parsed_html.Redirect, '')
		self.assertEqual(parsed_html.Title, 'iTunes U')
		self.assertEqual(len(parsed_html.mediaItems), 0)
		self.checkItems(parsed_html.mediaItems)


	def testParseFHSUPresident(self):
		url = "http://deimos.apple.com/WebObjects/Core.woa/Browse/fhsu.edu.1152205441"
		text = self.o.open(url).read()
		parsed_html = Parser(url, "text/HTML", text)

		# FIXME: Maybe it could be smarter about finding the title...
		self.assertEqual(parsed_html.Redirect, '')
		self.assertEqual(parsed_html.Title,
				 'iTunes U > Fort Hays State University > '
				 'FHSU News > From the President - '
				 'President Hammond')
		self.assertEqual(len(parsed_html.mediaItems), 30)
		# FIXME: The following should be made into proper tests
		for line in parsed_html.mediaItems:
			logging.debug(line)


	def testParseSIUC(self):
		url = "http://deimos3.apple.com/WebObjects/Core.woa/Browse/siuc.edu?ignore.mscache=9669968"
		text = self.o.open(url).read()
		parsed_html = Parser(url, "text/HTML", text)

		# FIXME: Maybe it could be smarter about finding the title...
		self.assertEqual(parsed_html.Redirect, '')
		self.assertEqual(parsed_html.Title, 'iTunes U')
		self.assertEqual(len(parsed_html.mediaItems), 0)
		self.checkHTML(parsed_html.HTML)
		
		self.assertEqual(parsed_html.HTML.count("<td>"),parsed_html.HTML.count("</td>"))
		self.assertEqual(parsed_html.HTML.count("<tr>"),parsed_html.HTML.count("</tr>"))

		# FIXME: The following should be made into proper tests
		self.checkItems(parsed_html.mediaItems)


	def testParseSJSU(self):
		url = "http://deimos3.apple.com/WebObjects/Core.woa/Browse/sjsu.edu?ignore.mscache=3176353"
		text = self.o.open(url).read()
		parsed_html = Parser(url, "text/HTML", text)

		# FIXME: Maybe it could be smarter about finding the title...
		self.assertEqual(parsed_html.Redirect, '')
		self.assertEqual(parsed_html.Title, 'iTunes U')
		self.assertEqual(len(parsed_html.mediaItems), 0)
		self.checkItems(parsed_html.mediaItems)


	def testParseWithTabs(self):
		url = "https://deimos.apple.com/WebObjects/Core.woa/BrowsePrivately/georgefox.edu.1285568794"
		text = self.o.open(url).read()
		parsed_html = Parser(url, "text/HTML", text)

		self.assertEqual(parsed_html.Redirect, '')
		self.assertEqual(parsed_html.Title,
				 'iTunes U > George Fox University > Chapel - Chapel 2012 - 2013')
		# FIXME: Are all tabs shown?
		self.assertEqual(parsed_html.tabMatches,
				 [', Selected. Chapel 2012 - 2013',
				  '. Chapel 2011-2012',
				  '. Shalom 2011-2012',
				  '. Chapel 2010-2011',
				  '. Shalom 2010-2011',
				  '. Other 2010-2011',
				  '. Chapel 2009-2010',
				  '. Shalom 2009-2010',
				  '. Chapel 2008-2009',
				  '. Shalom 2008-2009',
				  '. Chapel 2007 - 2008',
				  '. Chapel 2006-2007',
				  '. Chapel 2005-2006',
				  '. Chapel 2004-2005',
				  '. Chapel 2003-2004',
				  '. Chapel 2002-2003',
				  '. Chapel 2001-2002',
				  '. Chapel 2000-2001'])


	def testWebRedirect(self):
		url = "http://www2.ohlone.edu/cgi-bin/itunespub/itunes_public.pl"
		text = self.o.open(url).read()
		parsed_html = Parser(url, "text/HTML", text)
		assert parsed_html.Redirect.startswith('itmss://deimos.apple.com/WebObjects/Core.woa/BrowsePrivately/ohlone.edu')

	def test_XML_feed(self):
		url = "https://deimos.apple.com/WebObjects/Core.woa/Feed/itunes.stanford.edu-dz.11153667080.011153667082"
		text = self.o.open(url).read()
		parsed_html = Parser(url, "text/xml", text)

		self.assertEqual(parsed_html.Redirect, '')
		self.assertEqual(parsed_html.Title, 'iPad and iPhone Application Development (SD)')
		self.assertEqual(len(parsed_html.mediaItems), 43)
		self.checkItems(parsed_html.mediaItems)

	def testMulticorePage(self):
		url = "http://itunes.apple.com/us/course/multicore-programming-primer/id495066021"
		text = self.o.open(url).read()
		parsed_html = Parser(url, "text/html", text)

		self.assertEqual(parsed_html.Redirect, '')
		self.assertEqual(parsed_html.Title, 'Multicore Programming Primer')
		self.assertEqual(len(parsed_html.mediaItems), 82)
		for line in parsed_html.mediaItems:
			self.assertEqual(len(line[4]), 4) # test 4-char extension.

	def testDumpParsedHTML(self):
		url = "http://deimos3.apple.com/WebObjects/Core.woa/Browse/georgefox.edu.8155705810.08155705816.8223066656?i=1688428005"
		text = self.o.open(url).read()
		parsed_html = Parser(url, "text/HTML", text).HTML
		file("parsed_test.html", "w").write(parsed_html)
		


if __name__ == "__main__":
	unittest.main()
