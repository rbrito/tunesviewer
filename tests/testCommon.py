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

import sys
import unittest

sys.path.append('src')
sys.path.append('../src')

from common import *


class TestCommon(unittest.TestCase):
	def testTimeConvert(self):
		self.assertEqual(time_convert(1000), "0:01")
		self.assertEqual(time_convert(1000 * 60), "1:00")
		self.assertEqual(time_convert(1000 * 61), "1:01")
		self.assertEqual(time_convert(1000 * 70), "1:10")
		self.assertEqual(time_convert(1000 * 3599), "59:59")
		self.assertEqual(time_convert(1000 * 3600), "1:00:00")
		self.assertEqual(time_convert(1000 * 3601), "1:00:01")
		self.assertEqual(time_convert(1000 * 3660), "1:01:00")
		self.assertEqual(time_convert(1000 * 3661), "1:01:01")
		self.assertEqual(time_convert(1000 * 7200), "2:00:00")

		self.assertEqual(time_convert('30000.0'), "0:30")

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
		self.assertEqual(safeFilename(good, True), good[6:])  # without /home/.

	def testSuperUnquote(self):
		self.assertEqual(super_unquote('. Automated Testing'),
				 '. Automated Testing')
		self.assertEqual(super_unquote('.%20Automated%20Testing'),
				 '. Automated Testing')
		self.assertEqual(super_unquote('.%2520Automated%2520Testing'),
				 '. Automated Testing')

	def testDesc(self):
		self.assertEqual(desc(1), '1.0 B')
		self.assertEqual(desc(512), '512.0 B')
		self.assertEqual(desc(1023), '1023.0 B')
		self.assertEqual(desc(1024), '1.0 KB')
		self.assertEqual(desc(1025), '1.0 KB')
		self.assertEqual(desc(512 * 1024), '512.0 KB')
		self.assertEqual(desc(1023 * 1024), '1023.0 KB')
		self.assertEqual(desc(1024 * 1024), '1.0 MB')
		self.assertEqual(desc(1025 * 1024), '1.0 MB')
		self.assertEqual(desc(0.5 * 1024 * 1024 * 1024), '512.0 MB')
		self.assertEqual(desc(10000000000000000000),"(way too big)")

	def testTypeOf(self):
		self.assertEqual(type_of("http://a1135.g.akamai.net/f/1135/18227/1h/cchannel.download.akamai.com/18227/podcast/NEWYORK-NY/WAXQ-FM/Secretariat1.mp3?CPROG=PCAST&MARKET=NEWYORK-NY&NG_FORMAT=&SITE_ID=1674&STATION_ID=WAXQ-FM&PCAST_AUTHOR=Q104.3_New_York_City&PCAST_CAT=comedy&PCAST_TITLE=Jim_Kerr_Rock_and_Roll_Morning_Show_Parodies"),".mp3")
		self.assertEqual(type_of("http://a1135.g.akamai.net/f/1135/18227/1h/cchannel.download.akamai.com/18227/podcast/NEWYORK-NY/WAXQ-FM/ACN_NFLFilmsARealSport_-34414.mp3?CPROG=PCAST&MARKET=NEWYORK-NY&NG_FORMAT=&SITE_ID=1674&STATION_ID=WAXQ-FM&PCAST_AUTHOR=Q104.3_New_York_City&PCAST_CAT=comedy&PCAST_TITLE=Jim_Kerr_Rock_and_Roll_Morning_Show_Parodies"),".mp3")
		self.assertEqual(type_of("simplefilename.mp4"),".mp4")

if __name__ == "__main__":
	unittest.main()
