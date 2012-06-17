Harpy is a module for parsing HTTP Archive 1.2.

More information on the HTTP Archive specification can be found here:
http://www.softwareishard.com/blog/har-12-spec/

There are some extensions made to the spec to gaurantee that the
original request or response can be perfectly reconstructed from the
object. It should always be the case that a request or response that
is rendered in to an object using Harpy, can be rendered back from the
object to a raw request or response that is exactly the same as the
original. Some libraries are lossy, Harpy is lossless. 

This software is designed to be used for web testing, specifically
security testing. Focus, therefore, has been placed on reproducability
and quick parsing of large datasets.

One of the design goals of this library is to make usage simple. This
code should work the way you think it would work. There are several
ways to use Harpy and these will be different depending on the goal of
the software using it.

Constucting an object from scratch should be as easy as instantiating
the object::

    In [0]: hc = HarContainer()
    
    In [1]: print hc
    {}
    
    In [2]: hc
    Out[2]: <HarContainer: (empty)>

Some objects have default values which are pre-set::

    In [3]: r = Request()
    
    In [4]: r
    Out[4]: <Request to 'http://example.com/': ('cookies', 'url', 'queryString', 'headers', 'method', 'httpVersion')>

To not set default values on object creation disable default settings::

    In [5]: r = Request(defaults=False)
    
    In [6]: r
    Out[6]: <Request to '[undefined]': (empty)>
    
    In [7]: print r
    {}

A har object can also be initialized from a string of json, a file
that contains json, or a dictionary::

     In [8]: r = Request(r'{"cookies": [], "url": "http://example.com/foobarbaz", "queryString": [], "headers": [{"name": "Accept", "value": "*/*"}, {"name": "Accept-Language", "value": "en-US"}, {"name": "Accept-Encoding", "value": "gzip"}, {"name": "User-Agent", "value": "Harpy (if you see this in your logs,someone made a mistake)"}], "headersSize": 145, "httpVersion": "HTTP/1.1", "method": "GET", "bodySize": -1}')
     
     In [9]: r
     Out[9]: <Request to 'http://example.com/foobarbaz': ('cookies', 'url', 'queryString', 'headers', 'httpVersion', 'method')>
     
     In [10]: hc = HarContainer(urlopen('http://demo.ajaxperformance.com/har/google.har').read())
     
     In [11]: hc
     Out[11]: <HarContainer: ('log',)>
     
     In [12]: hc = HarContainer(open('./google.har'))
     
     In [13]: hc.log.entries[0].request
     Out[13]: <Request to 'http://www.google.com/': ('cookies', 'url', 'queryString', 'headers', 'httpVersion', 'method')>

Some objects, such as requests and responses, can consumed from raw::

     In [14]: raw
     Out[14]: 'GET / HTTP/1.1\r\nHost: localhost:1234\r\nUser-Agent: Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:13.0) Gecko/20100101 Firefox/13.0\r\nAccept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\nAccept-Language: en-us,en;q=0.5\r\nAccept-Encoding: gzip, deflate\r\nConnection: keep-alive\r\n\r\n'
     
     In [15]: r = Request()
     
     In [16]: r.devour(raw)
     
     In [17]: r
     Out[17]: <Request to 'http://localhost:1234/': ('cookies', 'url', 'queryString', 'headers', 'method', 'httpVersion')>

These objects can also be rendered back to raw::

      In [18]: r.puke()
      Out[18]: 'GET / HTTP/1.1\r\nHost: localhost:1234\r\nUser-Agent: Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:13.0) Gecko/20100101 Firefox/13.0\r\nAccept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\nAccept-Language: en-us,en;q=0.5\r\nAccept-Encoding: gzip, deflate\r\nConnection: keep-alive\r\n\r\n'

For polite people there's an alias::

    In [19]: help(Request.render)
    Help on method render in module __main__:
    
    render(self) unbound __main__.Request method
        Return a string that should be exactly equal to the
	original request.

This code is also intended to work well in comprehensions. For
example, it's trivial to write a list comprehension to get a list of
all URLs requested in a HAR::

    In [20]: [ e.request.url for e in hc.log.entries ]
    Out[20]: 
    [u'http://www.google.com/',
     u'http://www.google.com/intl/en_ALL/images/srpr/logo1w.png',
     u'http://www.google.com/images/srpr/nav_logo13.png',
     ...
     u'http://www.google.com/csi?v=foo']

It is likewise trivial to search for items, or associte requests and
responeses. For example, finding the response code for each url
requested if the url contains 'www.google.com' can be easily done::

    In [21]: [ (e.request.url, e.response.status) for e in hc.log.entries if 'www.google.com' in e.request.url ]
    Out[21]: 
    [(u'http://www.google.com/', 200),
     (u'http://www.google.com/intl/en_ALL/images/srpr/logo1w.png', 200),
     ...
     (u'http://www.google.com/csi?v=foo', 204)]

We can also use comprehensions to generate objects that can be used to
make new requests. The with_val method makes this simple. Here is the
example from the with_val docstring::

    In [0]: [ r.with_val(url='http://foo.com/%d/user' % i)
                for i in xrange(10) ]
    Out[0]: 
    [<Request to 'http://foo.com/0/user': ...
     <Request to 'http://foo.com/1/user': ... 
     <Request to 'http://foo.com/2/user': ... 
     ...
     <Request to 'http://foo.com/9/user': ... ]

As development continues more functionality will be added. Currently
Harpy is one project. In the future Harpy will be split in to
Harpy-core and Harpy-utils. Harpy-core will be only the coe necessary
for implementing the HAR specification. Harpy-utils will be a set of
additional modules and scripts that assist in testing, such as request
repeaters and spiders.

It is intended that Harpy be self documenting. All information needed
to use this module should be possible to gain from introspection. If
it ever fails to be easy to use or well documented, please suggest
improvements. If Harpy ever fails to be either lossless please file a
bug report.



requires python-dateutil

-------------------------------------------------------------------------------

There's a lot of manual parsing of queries, params, etc. This seems
like a stupid way to parse shit. I looked around a bit and didn't see
a library that did this already. I'll look around again later.

