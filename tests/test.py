from Parser import Parser
import urllib2

url ="http://deimos3.apple.com/WebObjects/Core.woa/Browse/georgefox.edu.8155705810.08155705816.8223066656?i=1688428005"

o = urllib2.build_opener()
o.addheaders = [('User-agent', 'iTunes/10.5')]
parsed_html = Parser(url, "text/HTML", o.open(url).read()).HTML
file("output.htm","w").write(parsed_html)