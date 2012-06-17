#!/usr/bin/python
#make this RequestGrinder
#have a core Grinder class that can have different Engines

#Instantiate a Grinder with an Engine (blackmamba if possible,
#otherwise urllib2.

#Grinder should support the methods load, grind
#(exec basically), and dump

#Pump class should just be a generator that takes a generator


try:
	from blackmamba import *
except ImportError:
	print ("Request engine is based on blackmamba. "
	       "git clone http://github.com/rootfoo/blackmamba "
	       "and follow installation instructions for this "
	       "functionality to work")
	raise
try:
	from .har import Request, Response, Timings, Entry
	from .utils import mario
except ImportError:
	from harpy.har import Request, Response, Timings, Entry
	from harpy.utils import mario
import sys
from urlparse import urlparse
from datetime import datetime

def process(request, outlist=None):

	try:
		# create the HTTP GET request from the URL
		raw_request = request.puke()
		
		# prepare response for late use
		response = Response()
		_timings = Timings()
		_sequence = None
		if '_sequence' in request:
			_sequence = request._sequence
		
		# but urlparse works too
		urlp = urlparse(request.url)
		host = urlp.hostname.strip()

		if urlp.scheme == 'https':
			default_port = 443
			ssl = True
		else:
			default_port = 80
			ssl = False
		port = urlp.port if urlp.port else default_port

		# if the server IP address has been overridden, use that	
		if '_serverIPAddress' in request:
			host = request._serverIPAddress
	
		# else resolve the hostname
		else:
			# to resolve DNS asynchronously, call resolve() prior to connect()
			_serverIPAddress = yield resolve(host)

		# connect
		start = datetime.now()
		yield connect(host, port)
		_timings.connect = get_time_delta(start)
		

		# write
		start = datetime.now()
		yield write(raw_request)
		_timings.send = get_time_delta(start)
		
		# read
		start = datetime.now()
		raw_response = yield read()
		_timings.wait = get_time_delta(start)

		
		# set bogus recieve timing
		_timings.recieve = 0
		
		# calculate endtime
		end = datetime.now()
		duration = ((end-start).microseconds)/1000

		# do something with Response object
		#print raw_response
		response.devour(raw_response)
		#print response
		if type(outlist) == list:
			
			#entry = E
			outlist.append(response)
		else:
			response._timings = _timings
			
			if _sequence:
				response = _sequence
			response._serverIPAddress = _serverIPAddress
			print response

		# # close the connection
		yield close()

	except SockError as e:
		print e


def get_time_delta(start):
	"""get microseconds since start. start is a datetime object."""
	end = datetime.now()
	duration = ((end-start).microseconds)/1000
	return duration


def make_requests(g):
	return (process(request) for request in g)


def response_generator(g):
	outlist = []
	run(process(request, outlist) for request in g)
	for response in outlist:
		yield response


if __name__=='__main__':

	# Create a generator. List comprehension syntax is nice
	taskgen = make_requests(mario.pull(Request))

	# the debug() is a wrapper for run() which provides verbose error handling  
	debug(taskgen)
	#run(taskgen)


