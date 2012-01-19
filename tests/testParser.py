# -*- coding: utf-8 -*-

import logging
import sys
import unittest
import urllib2

sys.path.append('src')
sys.path.append('../src')

from Parser import Parser


# Test the parser class - Requires network!
class TestParser(unittest.TestCase):
	def setUp(self):
		"""
		Take care of the preparation of the tests.
		"""
		self.o = urllib2.build_opener()
		self.o.addheaders = [('User-agent', 'iTunes/10.5')]


	def testParseAgriculture(self):
		url = "http://itunes.apple.com/WebObjects/DZR.woa/wa/viewPodcast?cc=us&id=387961518"
		text = self.o.open(url).read()
		parsed_html = Parser(url, "text/HTML", text)

		self.assertEqual(parsed_html.Redirect, '')
		self.assertEqual(parsed_html.Title, 'Food and Sustainable Agriculture')
		self.assertEqual(len(parsed_html.mediaItems), 7)

		# FIXME: The following should be made into proper tests
		for line in parsed_html.mediaItems:
			logging.warn(line)


	def testParseFHSU(self):
		url = "http://deimos.apple.com/WebObjects/Core.woa/Browse/fhsu.edu"
		text = self.o.open(url).read()
		parsed_html = Parser(url, "text/HTML", text)

		# FIXME: Maybe it could be smarter about finding the title...
		self.assertEqual(parsed_html.Redirect, '')
		self.assertEqual(parsed_html.Title, 'iTunes U')
		self.assertEqual(len(parsed_html.mediaItems), 0)

		# FIXME: The following should be made into proper tests
		for line in parsed_html.mediaItems:
			logging.warn(line)


	def testPresidentHammond(self):
		url = "http://deimos.apple.com/WebObjects/Core.woa/Browse/fhsu.edu.1152205441"
		text = self.o.open(url).read()
		parsed_html = Parser(url, "text/HTML", text)

		# FIXME: Maybe it could be smarter about finding the title...
		self.assertEqual(parsed_html.Redirect, '')
		self.assertEqual(parsed_html.Title,
				 'iTunes U > Fort Hays State University > '
				 'FHSU News > From the President - '
				 'President Hammond')
		self.assertEqual(len(parsed_html.mediaItems), 28)

		# FIXME: The following should be made into proper tests
		for line in parsed_html.mediaItems:
			logging.warn(line)


	def testTopDownloads(self):
		url = "https://deimos.apple.com/WebObjects/Core.woa/BrowsePrivately/georgefox.edu.01651902695"
		text = self.o.open(url).read()
		parsed_html = Parser(url, "text/xml", text)

		self.assertEqual(parsed_html.Redirect, '')
		self.assertEqual(parsed_html.Title, 'iTunes U > Top Downloads')

		# FIXME: Not sure where the bogus element is coming from in the gui...
		self.assertEqual(len(parsed_html.mediaItems), 0)

		# FIXME: The following should be made into proper tests
		for line in parsed_html.mediaItems:
			logging.warn(line)


	def testParseSIUC(self):
		url = "http://deimos3.apple.com/WebObjects/Core.woa/Browse/siuc.edu?ignore.mscache=9669968"
		text = self.o.open(url).read()
		parsed_html = Parser(url, "text/HTML", text)

		# FIXME: Maybe it could be smarter about finding the title...
		self.assertEqual(parsed_html.Redirect, '')
		self.assertEqual(parsed_html.Title, 'iTunes U')
		self.assertEqual(len(parsed_html.mediaItems), 0)

		# FIXME: The following should be made into proper tests
		for line in parsed_html.mediaItems:
			logging.warn(line)


	def testParseSJSU(self):
		url = "http://deimos3.apple.com/WebObjects/Core.woa/Browse/sjsu.edu?ignore.mscache=3176353"
		text = self.o.open(url).read()
		parsed_html = Parser(url, "text/HTML", text)

		# FIXME: Maybe it could be smarter about finding the title...
		self.assertEqual(parsed_html.Redirect, '')
		self.assertEqual(parsed_html.Title, 'iTunes U')
		self.assertEqual(len(parsed_html.mediaItems), 0)

		# FIXME: The following should be made into proper tests
		for line in parsed_html.mediaItems:
			logging.warn(line)


	def testParseWithTabs(self):
		url = "https://deimos.apple.com/WebObjects/Core.woa/BrowsePrivately/georgefox.edu.1285568794"
		text = self.o.open(url).read()
		parsed_html = Parser(url, "text/HTML", text)

		self.assertEqual(parsed_html.Redirect, '')
		self.assertEqual(parsed_html.Title,
				 'iTunes U > George Fox University > Chapel - Chapel 2011-2012')
		# FIXME: Are all tabs shown?
		self.assertEqual(parsed_html.tabMatches,
				 [', Selected. Chapel 2011-2012',
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
		self.assertEqual(len(parsed_html.mediaItems), 36)

		# FIXME: The following should be made into proper tests
		for line in parsed_html.mediaItems:
			logging.warn(line)



if __name__ == "__main__":
	unittest.main()
