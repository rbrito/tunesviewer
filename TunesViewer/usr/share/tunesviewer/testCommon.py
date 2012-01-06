import unittest
from common import *

class TestCommon(unittest.TestCase):
	def testTimeFind(self):
		assert timeFind(1000)=="00:01"
		assert timeFind("bogus")=="bogus"
		assert timeFind(1000*60)=="01:00"
		
	def testHTML(self):
		assert htmlentitydecode("M&amp;M")=="M&M"
		
	def testSafeFilename(self):
		good = "/home/abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 $%`-_@{}~!#()."
		assert safeFilename("/home/mydirectory/somefile",True)=="somefile"
		assert safeFilename(good,True)==good[6:] #without /home/.
		
if __name__ == "__main__":
	unittest.main() # run all tests