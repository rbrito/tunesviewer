# -*- coding: utf-8 -*-

import sys
import unittest

sys.path.append('src')
sys.path.append('../src')

from common import *

class TestCommon(unittest.TestCase):
	def testTime_Convert(self):
		self.assertEqual(time_convert(1000), "0:01")
		self.assertEqual(time_convert(1000*60), "1:00")
		self.assertEqual(time_convert(1000*61), "1:01")
		self.assertEqual(time_convert(1000*70), "1:10")
		self.assertEqual(time_convert(1000*3599), "59:59")
		self.assertEqual(time_convert(1000*3600), "1:00:00")
		self.assertEqual(time_convert(1000*3601), "1:00:01")
		self.assertEqual(time_convert(1000*3660), "1:01:00")
		self.assertEqual(time_convert(1000*3661), "1:01:01")
		self.assertEqual(time_convert(1000*7200), "2:00:00")

		self.assertEqual(time_convert("bogus"), "bogus")
		self.assertEqual(time_convert([]), [])

	def testHTML(self):
		self.assertEqual(htmlentitydecode("M&amp;M"), "M&M")
		self.assertEqual(htmlentitydecode("&lt;"), "<")
		self.assertEqual(htmlentitydecode("&#60;"), "<")
		self.assertEqual(htmlentitydecode("dynlists&copy;"), "dynlists©")
		self.assertEqual(htmlentitydecode("dynlists&copy"), "dynlists&copy")

	def testSafeFilename(self):
		basename = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 $%`-_@{}~!#()."
		good = "/home/" + basename
		self.assertEqual(safeFilename("/home/mydirectory/somefile", True), "somefile")
		self.assertEqual(safeFilename(good, True), good[6:]) #without /home/.

	def test_super_unquote(self):
		self.assertEqual(super_unquote('. Automated Testing'),
				 '. Automated Testing')
		self.assertEqual(super_unquote('.%20Automated%20Testing'),
				 '. Automated Testing')
		self.assertEqual(super_unquote('.%2520Automated%2520Testing'),
				 '. Automated Testing')

if __name__ == "__main__":
	# run all tests
	unittest.main()
