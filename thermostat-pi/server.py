from utility import *

from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

PORT = 80




# web path handlers!

def statusPage(ctx, query):

	page = """
	<html>
	<head>
	<title>Thermostat Status</title>
	<meta http-equiv="refresh" content="60" />
	</head>
	<body>"""

	page +=  '<h3>Thermostat Status Page (' + timestamp() + ')</h3>' + ctx['thermostat'].status()

	page += "</body></html>"

	return {'content': page, 'contenttype': 'text/html; charset=UTF-8'}

def setProp(ctx, query):
	try:
		k,v = query.split('=')
		
		if k == 'temp':
			ctx['thermostat'].updateTemp(float(v))
			return 'Temperature updated to ' + str(v)
		
		return 'Unknown property'

	except ValueError:
		return "Bad query"

def logOutputHandler(ctx, q):
	fh.flush() 
	return plaintextify(open(LOGFILE, 'r').read())

def overrideHandler(ctx, qs):
	if len(qs) != 1:
		return plaintextify('Failsafe override currently: ' + ('on' if ctx['prefs']['failsafeOverride'] else 'off'))
	query = qs[0]
	if query.lower() == 'true':
		ctx['prefs']['failsafeOverride'] = True
		savePrefs(ctx['prefs'])
		return plaintextify('Failsafe override: heat on')
	else:
		ctx['prefs']['failsafeOverride'] = False
		savePrefs(ctx['prefs'])
		return plaintextify('Failsafe override: heat off')

def plaintextify(txt):
	return {'content': txt, 'contenttype': 'text/plain; charset=UTF-8'}


pathHandlers = {
	'': statusPage,
	'set': lambda ctx, q: plaintextify('\n'.join([setProp(ctx, p) for p in q])),
	'data': lambda ctx, q: plaintextify(open('thermostat.csv', 'r').read()),
	'log': logOutputHandler,
	'override': overrideHandler
}

# web server
class RequestHandler(BaseHTTPRequestHandler):

	def parsePath(self):
		print 'parsing path ' + self.path
		get = self.path[1:].split('?')
		if len(get) > 1:
			return (get[0].split('/'), get[1].split('&'))
		else:
			return (get[0].split('/'), [])
	
	def __init__(self, *args):
		BaseHTTPRequestHandler.__init__(self, *args)

	def _set_headers(self, contenttype):
		self.send_response(200)
		self.send_header('Content-type', contenttype)
		self.end_headers()

	def do_GET(self):

		log.debug(self.parsePath())

		try:
			pathelements = self.parsePath()
			currentPath = pathHandlers
			for i in pathelements[0]:
				currentPath = currentPath[i]		

			log.debug("200: Handling path " + self.path)

			data = currentPath(self.server.context, pathelements[1])

			self._set_headers(data['contenttype'])
			self.wfile.write(data['content'])

		except KeyError, TypeError:
			log.info("404: Don't understand path " + self.path)
			self.send_error(404, "Can't handle path " + self.path)

	def do_HEAD(self):
		log.debug("HEAD " + self.path)
		self._set_headers()
		
	def do_POST(self):
		# Doesn't do anything with posted data
		log.debug("POST " + self.path)
		self._set_headers()
		self.wfile.write("<html><body><h1>POST!</h1></body></html>")


def start(thermostat,prefs):
	log.info("Starting server.")
	server = HTTPServer(('', PORT), RequestHandler)
	server.context = {'thermostat': thermostat, 'prefs':prefs}
	server.allow_reuse_address = True
	server.serve_forever()

if __name__ == "__main__":
	# run with dummy data
	prefs = preferences = {
		'units': 'C',
		'setpointMin': 19,
		'setpointMax': 21,
		'failsafeOverride': False
	}
	start(MockThermostat(), prefs)
