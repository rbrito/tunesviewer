# -*- coding: utf-8 -*-

import logging
import sys
import unittest
import urllib2

sys.path.append('src')

from Parser import Parser

# Test the parser class - Requires network!
class TestParser(unittest.TestCase):
	def setUp(self):
		"""
		Take care of the preparation of the tests.
		"""
		self.o = urllib2.build_opener()
		self.o.addheaders = [('User-agent', 'iTunes/10.5')]

	# TODO: Add some more pages to test (especially XML pages)
	def testParseAgriculture(self):
		url = "http://itunes.apple.com/WebObjects/DZR.woa/wa/viewPodcast?cc=us&id=387961518"
		text = self.o.open(url).read()
		parsed_html = Parser(url, "text/HTML", text)

		self.assertEqual(parsed_html.Redirect, '')
		self.assertEqual(parsed_html.Title, 'Food and Sustainable Agriculture')
		self.assertEqual(len(parsed_html.mediaItems), 7)

		# The following should be made into proper tests
		for line in parsed_html.mediaItems:
			logging.warn(line)

if __name__ == "__main__":
	# run all tests
	unittest.main()
