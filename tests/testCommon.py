# -*- coding: utf-8 -*-

import sys
import unittest

sys.path.append('src')

from common import *

class TestCommon(unittest.TestCase):
	def testTimeFind(self):
		self.assertEqual(timeFind(1000), "00:01")
		self.assertEqual(timeFind(1000*60), "01:00")

		self.assertEqual(timeFind("bogus"), "bogus")
		self.assertEqual(timeFind([]), [])

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


if __name__ == "__main__":
	# run all tests
	unittest.main()
