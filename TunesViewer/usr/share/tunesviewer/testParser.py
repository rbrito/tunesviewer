import unittest
import urllib2
from Parser import Parser

# Test the parser class - Requires network!
class TestParser(unittest.TestCase):
	def testParse(self):
		opener = urllib2.build_opener()
		opener.addheaders = [('User-agent', 'iTunes/10.5')]
		url = "http://itunes.apple.com/WebObjects/DZR.woa/wa/viewPodcast?cc=us&id=387961518"
		text = opener.open(url).read()
		parsed = Parser(url,"text/HTML",text)
		assert parsed.Redirect == ''
		assert parsed.Title == 'Food and Sustainable Agriculture'
		assert len(parsed.mediaItems)==7
		print "\n Important: Check this! \n"
		for line in parsed.mediaItems:
			print line
		
		#TODO: Probably should add some more pages to test, especially XML pages...
	
if __name__ == "__main__":
	unittest.main() # run all tests