#!/usr/bin/env python
"""Harpy is a module for parsing HTTP Archive 1.2.

More information on the HTTP Archive specification can be found here:
http://www.softwareishard.com/blog/har-12-spec/

There are some extensions made to the spec to guarantee that the
original request or response can be perfectly reconstructed from the
object. It should always be the case that a request or response that
is rendered in to an object using Harpy, can be rendered back from the
object to a raw request or response that is exactly the same as the
original. Some libraries are lossy, Harpy is lossless. 

This software is designed to be used for web testing, specifically
security testing. Focus, therefore, has been placed on reproducibility
and quick parsing of large datasets.

One of the design goals of this library is to make usage simple. This
code should work the way you think it would work. There are several
ways to use Harpy and these will be different depending on the goal of
the software using it.

Constructing an object from scratch should be as easy as instantiating
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

Also notice that the `repr` of an object contains the most relevant
information about the object. This is different depending on the
object type, but it will always contain a list of the object's direct
children. If there are no children, the child list will show as
(empty).

A har object can also be initialized from a string of json, a file
that contains json, or a dictionary::

     In [8]: r = Request(r'{"cookies": [], "url": "http://example.com/foobarbaz", ...)
     
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
     Out[14]: 'GET / HTTP/1.1\\r\\nHost: localhost:1234\\r\\nUser-Agent: Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:13.0) Gecko/20100101 Firefox/13.0\\r\\nAccept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\\r\\nAccept-Language: en-us,en;q=0.5\\r\\nAccept-Encoding: gzip, deflate\\r\\nConnection: keep-alive\\r\\n\\r\\n'
     
     In [15]: r = Request()
     
     In [16]: r.devour(raw)
     
     In [17]: r
     Out[17]: <Request to 'http://localhost:1234/': ('cookies', 'url', 'queryString', 'headers', 'method', 'httpVersion')>

These objects can also be rendered back to raw::

      In [18]: r.puke()
      Out[18]: 'GET / HTTP/1.1\\r\\nHost: localhost:1234\\r\\nUser-Agent: Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:13.0) Gecko/20100101 Firefox/13.0\\r\\nAccept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\\r\\nAccept-Language: en-us,en;q=0.5\\r\\nAccept-Encoding: gzip, deflate\\r\\nConnection: keep-alive\\r\\n\\r\\n'

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

It is likewise trivial to search for items, or associate requests and
responses. For example, finding the response code for each url
requested if the url contains 'www.google.com' can be easily done::

    In [21]: [ (e.request.url, e.response.status) for e in hc.log.entries if 'www.google.com' in e.request.url ]
    Out[21]: 
    [(u'http://www.google.com/', 200),
     (u'http://www.google.com/intl/en_ALL/images/srpr/logo1w.png', 200),
     ...
     (u'http://www.google.com/csi?v=foo', 204)]

We can also use comprehensions to generate objects that can be used to
make new requests. The replace method makes this simple. Here is the
example from the replace docstring::

    In [0]: [ r.replace(url='http://foo.com/%d/user' % i)
                for i in xrange(10) ]
    Out[0]: 
    [<Request to 'http://foo.com/0/user': ...
     <Request to 'http://foo.com/1/user': ... 
     <Request to 'http://foo.com/2/user': ... 
     ...
     <Request to 'http://foo.com/9/user': ... ]

BUG WARNING: In Python, timezone information is not populated into
datetime objects by default. All time objects must have a time zone
according to the specification. The pytz module is used to manage
this. All things without timezones will be localized to UTC. This may
be a bug waiting to bite.

As development continues more functionality will be added. Currently
Harpy is one project. In the future Harpy will be split in to
Harpy-core and Harpy-utils. Harpy-core will be only the code necessary
for implementing the HAR specification. Harpy-utils will be a set of
additional modules and scripts that assist in testing, such as request
repeaters and spiders.

It is intended that Harpy be self documenting. All information needed
to use this module should be possible to gain from introspection. If
it ever fails to be easy to use or well documented, please suggest
improvements. If Harpy ever fails to be either lossless please file a
bug report.

"""

import json
import copy
from StringIO import StringIO
from socket import inet_pton, AF_INET6, AF_INET #used to validate ip addresses
from socket import error as socket_error #used to validate ip addresses
from urllib2 import urlopen #this should be removed
try:
    from dateutil import parser
except ImportError:
    print ("Please verify that dateutil is installed. On Debian based systems "
           "like Ubuntu this can be  done with `aptitude install "
           "python-dateutil`.")
    raise
try:
    from pytz import timezone, utc
except ImportError:
    print ("Please verify that pytz is installed. The easiest way to "
           "install it is with `easy_install pytz`")
    raise
from datetime import datetime
from time import tzname
from base64 import b64encode, b64decode

##############################################################################
# Static Definitions
###############################################################################

METHODS = ["OPTIONS",
           "GET",
           "HEAD",
           "POST",
           "PUT",
           "DELETE",
           "TRACE",
           "BREW", #added for RFC2324 compliance
           "WHEN", #added for RFC2324 compliance
           "CONNECT", #for proxy, request coming in as this
           "PROPFIND",
           "PROPPATCH",
           "MKCOL",
           "COPY",
           "MOVE",
           "LOCK",
           "UNLOCK",
           "VERSION-CONTROL",
           "REPORT",
           "CHECKOUT",
           "CHECKIN",
           "UNCHECKOUT",
           "MKWORKSPACE",
           "UPDATE",
           "LABEL",
           "MERGE",
           "BASELINE-CONTROL",
           "MKACTIVITY",
           "ORDERPATCH",
           "ACL",
           "PATCH",
           "SEARCH",
           "ARBITRARY"]


###############################################################################
# Exceptions
###############################################################################


class MissingValueExcpetion(Exception):

    def __init__(self, value, in_class):
        self.value = value
        self.in_class = in_class

    def __str__(self):
        return ('Field "{0}" missing from input while trying to instantiate "{1}"'
                .format(
                    self.value,
                    self.in_class))


class ModeNotSupported(Exception):

    def __init__(self, mode):
        self.mode = mode

    def __str__(self):
        return str("Mode %s not supported" % self.mode)


class ValidationError(Exception):

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return str(self.msg)


###############################################################################
# JSON Overrides and Hooks
###############################################################################


class HarEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, MetaHar):
            return dict( (k,v) for k,v in obj.__dict__.iteritems()
                         if k != "_parent" )
        #!!! fix this
        if isinstance(obj, datetime):
            if not obj.tzinfo: #handle zone info not being added by python
                obj = utc.localize(obj) #this is a bug waiting to happen
            return obj.isoformat()
            #according to the spec this needs to be ISO 8601
            #YYY-MM-DDThh:mm:ss.sTZD
        return json.JSONEncoder.default(self, obj)


###############################################################################
# HAR Classes
###############################################################################


class MetaHar(object):
    """This is the base class that all HAR objects use. It defines
    default methods and objects."""
    # this needs to be a tree so child objects can validate that they
    # are uniq children

    def __init__(self, init_from=None, parent=None, defaults=True):
        """ Needs documentation
        """
        self._parent = parent
        if init_from:
            assert type(init_from) in [unicode, str, file, dict], \
                   ("A har can only be initialized from a string, "
                    "file object, dict")
            if type(init_from) in [unicode, str, file]:
                if type(init_from) == unicode or type(init_from) == str:
                    fd = StringIO(init_from)
                else:
                    fd = init_from
                self.from_json(fd.read())
                fd.close()
            else:
                self.from_dict(init_from)
        elif defaults:
            self.set_defaults()

    def __iter__(self):
        return (v for k,v in self.__dict__.iteritems()
                 if k != "_parent" and
                 (isinstance(v, MetaHar)
                  or isinstance(v, list)
                  or isinstance(v, unicode)
                  or isinstance(v, str)))

    def __contains__(self, obj):
        return obj in self._get_printable_kids()

    def __str__(self):
        return self.to_json()

    def __repr__(self):
        return "<{0} {1} {2}>".format(
            self.__class__.__name__,
            'name' in self.__dict__ and self.name or "[undefined]",
            self._get_printable_kids())

    def _get_printable_kids(self):
        """Return a tuple of all objects that are children of the
        object on which the method is called.
        """
        return tuple( str(k) for k,v in self.__dict__.iteritems()
                 if (str(k) != "_parent" and
                     (isinstance(v, MetaHar)
                      or isinstance(v, list)
                      or isinstance(v, unicode)
                      or isinstance(v, str)))) or '(empty)'


    def replace(self, **kwarg):
        """Return a copy of the object with a varabile set to a value.

        This is essentially __setattr__ except that it returns an
        instance of the object with the new value when called. This
        method was added to make comprensions easier to write. The
        canonical use case is for sequencing:

        In [0]: [ r.replace(url='http://foo.com/%d/user' % i)
                    for i in xrange(10) ]
        Out[0]: 
        [<Request to 'http://foo.com/0/user': ...
         <Request to 'http://foo.com/1/user': ... 
         <Request to 'http://foo.com/2/user': ... 
        ...
         <Request to 'http://foo.com/9/user': ... ]

        As a request object can always be turned back in to a raw
        request, this is useful for testing by taking a known good
        request and modifying it to observe different results.
        """
        #I imagine this will get really confusing at some point
        new_req = Request(self.to_json())
        for key, value in kwarg.iteritems():
            new_req.__dict__[key] = value
        return new_req

    def get_children(self):
        """Return all objects that are children of the object on which
        the method is called.
        """
        #dunno if I like this method... maybe should be a generator?
        return [ kid for kid in self ] # this comes from
                                       # _get_printable_kids()

    def from_json(self, json_data):
        json_data = json.loads(json_data)
        self.from_dict(json_data) #get first element

    def from_dict(self, json_dict):
        assert type(json_dict) is dict, "from_dict must be passed a dictionary"
        self.__dict__.update(json_dict)
        self.validate()
        self._construct()

    def _construct(self):
        #when constructing child objects, pass self so parent hierachy
        #can exist
        pass

    def set_defaults(self):
        """In general this method sets defaults for objects not
        instantiated via 'init_from' if 'set_defaults' parameter is
        not set to False. It can also be used to reset a har to a
        default state."""
        pass

    def to_json(self):
        #return json.dumps(self, indent=4, cls=HarEncoder)
        ## for now we're going to use line return as a deleniator
        ## later we'll write a json stream parser
        return json.dumps(self, indent=None, cls=HarEncoder)

    def validate(self): #default behavior
        # change this to a couple of class vars
        field_types = {"name":[unicode, str],
                       "value":[unicode, str]}
        self._has_fields(*field_types.keys())
        if "comment" in self.__dict__:
            field_types["comment"] = [unicode, str]
        self._check_field_types(field_types)

    def _has_fields(self, *fields):
        for field in fields:
            if not field in self.__dict__:
                raise MissingValueExcpetion(field, self.__class__.__name__)

    def _check_field_types(self, field_defs):
        for fname, ftype in field_defs.iteritems():
            if type(ftype) == list:
                assert type(self.__dict__[fname]) in ftype, (
                    "{0} filed '{1}' must be one of types: {2}"
                    .format(self.__class__.__name__, fname, ftype))
            else:
                assert type(self.__dict__[fname]) is ftype, (
                    "{0} filed '{1}' must be of type: {2}"
                    .format(self.__class__.__name__, fname, ftype))

#------------------------------------------------------------------------------

class KeyValueHar(MetaHar):

    def validate(self): #default behavior
        field_types = {"name":[unicode, str],
                       "value":[unicode, str]}
        self._has_fields(*field_types.keys())
        if "comment" in self.__dict__:
            field_types["comment"] = [unicode, str]

    def __repr__(self):
        return "<{0} {1}: {2}>".format(
            self.__class__.__name__,
            'name' in self.__dict__ and self.name or "[undefined]",
            'value' in self.__dict__ and self.value or "[undefined]")

    def __eq__(self, other):
        # not sure if this is logical, may need to take it out later
        return other == self.value


#------------------------------------------------------------------------------

class HarContainer(MetaHar):

    def __repr__(self):
        return "<{0}: {1}>".format(
            self.__class__.__name__,
            self._get_printable_kids())

    def _construct(self):
        self.log = Log(self.log, self)

    def validate(self):
        field_types = {"log": dict}
        self._has_fields(*field_types.keys())
        self._check_field_types(field_types)

#------------------------------------------------------------------------------


class Log(MetaHar):

    def validate(self):
        self._has_fields("version", "creator", "entries")
        field_defs = {"version":[unicode, str],
                      "entries":list}
        if self.version is '':
            self.version = "1.1"
        if "pages" in self.__dict__:
            field_defs["pages"] = list
        if "comment" in self.__dict__:
            field_defs["comment"] = [unicode, str]
        self._check_field_types(field_defs)

    def _construct(self):
        self.creator = Creator(self.creator)
        if "browser" in self.__dict__:
            self.browser = Browser(self.browser)
        if "pages" in self.__dict__:
            self.pages = [ Page(page) for page in self.pages]
        self.entries = [ Entry(entry) for entry in self.entries]

    def __repr__(self):
        try:
            return "<HAR {0} Log created by {1} {2}: {3}>".format(
                self.version,
                self.creator.name,
                self.creator.version,
                self._get_printable_kids())
        except AttributeError:
            return "<Log object not fully initilized>"


#------------------------------------------------------------------------------


class Creator(MetaHar):

    def validate(self):
        self._has_fields("name",
                         "version")
        field_defs = {"name": [unicode, str],
                      "version": [unicode, str]}
        if "comment" in self.__dict__:
            field_defs["comment"] = [unicode, str]
        self._check_field_types(field_defs)

    def __repr__(self):
        return "<Created by {0}: {1}>".format(
            self.name, self._get_printable_kids())


#------------------------------------------------------------------------------


class Browser(Creator):

    def __repr__(self):
        return "<Browser  '{0}': {1} >".format(
            self.name, self._get_printable_kids())


#------------------------------------------------------------------------------


class Page(MetaHar):

    def validate(self):
        self._has_fields("startedDateTime",
                         "id",
                         "title",
                         "pageTimings")
        field_defs = {"startedDateTime":[unicode, str],
                      "id":[unicode, str],
                      "title":[unicode, str]}
        if "comment" in self.__dict__:
            field_types["comment"] = [unicode, str]
        self._check_field_types(field_defs)
        #make sure id is uniq

    def _construct(self):
        try:
            self.startedDateTime = parser.parse(self.startedDateTime)
        except Exception, e:
            raise ValidationError("Failed to parse date: {0}".format(e))
        self.pageTimings = PageTimings(self.pageTimings)

    def __repr__(self):
        return "<Page with title '{0}': {1}>".format(
            self.title, self._get_printable_kids())


#------------------------------------------------------------------------------


class PageTimings(MetaHar):

    def validate(self):
        field_defs = {}
        if "onContentLoad" in self.__dict__:
            field_defs["onContentLoad"] = int
        if "onLoad" in self.__dict__:
            field_defs["onLoad"] = int
        if "comment" in self.__dict__:
            field_defs["comment"] = [unicode, str]
        self._check_field_types(field_defs)

    def __repr__(self):
        return "<Page timing : {0}>".format(
            self._get_printable_kids())


#------------------------------------------------------------------------------


class Entry(MetaHar):

    def validate(self):
        field_defs = {"startedDateTime":[unicode, str]}
        self._has_fields("startedDateTime",
                         "request",
                         "response",
                         "cache",
                         "timings")
        if "pageref" in self:
            field_defs["pageref"] = [unicode, str]
        if "serverIPAddress" in self:
            field_defs["serverIPAddress"] = [unicode, str]
        if "connection" in self:
            field_defs["connection"] = [unicode, str]
        self._check_field_types(field_defs)
        if "pageref" in self and "_parent" in self.__dict__ and self._parent:
            for entry in self._parent.entries: #write a test case for this
                if entry.pageref == self.pageref:
                    raise ValidationError("Entry pageref {0} must be uniq, "
                                          "but it is not".format(self.pageref))
        if "serverIPAddress" in self:
            try:
                inet_pton(AF_INET6, self.serverIPAddress) #think of the future
            except socket_error:
                try:
                    inet_pton(AF_INET, self.serverIPAddress)
                except socket_error:
                    raise ValidationError("Invalid IP address {0}: "
                                          "Address does not seem to be either "
                                          "IP4 or IP6".format(self.serverIPAddress))

    def _construct(self):
        self.request = Request(self.request)
        self.response = Response(self.response)
        self.cache = Cache(self.cache)
        self.timings = Timings(self.timings)

    def __repr__(self):
        return "<Entry object {0}>".format(self._get_printable_kids())


#------------------------------------------------------------------------------


class Request(MetaHar):

    def validate(self):
        field_defs = {"method":[unicode, str], #perhaps these should
                                               #be under _has_fields
                      "url":[unicode, str],
                      "httpVersion":[unicode, str],
                      "headersSize":int,
                      "bodySize":int}
        self._has_fields("method",
                         "url",
                         "httpVersion",
                         "queryString",
                         "headersSize",
                         "bodySize")
        if "comment" in self.__dict__:
            field_defs["comment"] = [unicode, str]
        self._check_field_types(field_defs)

    def _construct(self):
        if "postData" in self.__dict__:
            self.postData = PostData(self.postData)
        if "headers" in self.__dict__:
            self.headers = [ Header(header) for header in self.headers]
            if all('_sequence' in header for header in self.headers):
                self.headers.sort(key=lambda i: i._sequence)
        if "cookies" in self.__dict__:
            self.cookies = [ Cookie(cookie) for cookie in self.cookies]
            if all('_sequence' in cookie for cookie in self.cookies):
                self.cookies.sort(key=lambda i: i._sequence)

    def set_defaults(self):
        self.from_dict({"cookies": [],
                        "url": "http://example.com/",
                        "queryString": [],
                        "headers": [{"name": "Accept", "value": "*/*"},
                                    {"name": "Accept-Language", "value": "en-US"},
                                    {"name": "Accept-Encoding", "value": "gzip"},
                                    {"name": "User-Agent", "value":
                                     ("Harpy (if you see this in your logs,"
                                      "someone made a mistake)")}],
                        "headersSize": 145,
                        "bodySize": -1,
                        "method": "GET",
                        "httpVersion": "HTTP/1.1"})

    def set_header(self, name, value):
        """Sets a header to a specific value. NOTE: This operates by
        rebuilding the header list so if two headers have the same
        name they will both be removed and replaced with the new one
        """
        #this sucks and is a horrible way to do things.
        #also doens't take in to account sequence.. fuck
        #
        #there's a more pythonic way to do this....
        try:
            headers = [ header for header in self.headers
                        if not header.name == name ]
            h = [ header for header in self.headers
                        if header.name == name ][0]
            h.value = value
        except:
            pass
        else:
            h = Header({"name":name,"value":value})
        headers.append(h)

    def __repr__(self):
        return "<Request to '{0}': {1}>".format(
            ("url" in self and self.url) or  "[undefined]",
            self._get_printable_kids())

    def devour(self, req, proto='http', comment='', keep_b64_raw=False):
        # Raw request does not have proto info
        assert len(req.strip()), "Empty request cannot be devoured"
        if keep_b64_raw:
            self._b64_raw_req = b64encode(req) #just to be sure we're
                                               #keeping a copy of the
                                               #raw request by
                                               #default. This is a
                                               #person extension to
                                               #the spec.
                                               #
                                               #This is not default
        req = StringIO(req)
        #!!! this doesn't always happen
        method, path, httpVersion = req.next().strip().split()
        #some people ignore the spec, this needs to be handled.
        self.method = method
        self.httpVersion = httpVersion
        self.bodySize = 0
        self.headers = []
        postData = None
        if method == "POST":
            postData = {"params":[],
                        "mimeType":"",
                        "text":""}
        seq = 0
        for header in req: #make these the same for request and
                           #response... this is stupid
            header = header.strip()
            if not ( header and ": " in header):
                break
            header = dict(zip(["name", "value"], header.split(': ')))
            #length should be calculated for each request unless
            #explicitly set.
            #!!! remember to note this in docs so it's no suprise.
            if header["name"] == "Content-Length":
                self.bodySize = header["value"]
                continue
            if header["name"] == "Content-Type":
                postData["mimeType"] = header["value"]
                continue
            if header["name"] == "Host":
                self.url = '{0}://{1}{2}'.format(proto, header["value"], path)
            header["_sequence"] = seq
            self.headers.append(Header(header))
            seq += 1
        headerSize = req.tell()
        seq = 0
        if postData:
            body = req.read(int(self.bodySize))
            if postData["mimeType"] == "application/x-www-form-urlencoded":
                seq = 0
                for param in body.split('&'):
                    if "=" in param:
                        name, value = param.split('=',1) #= is a valid
                                                         #character in
                                                         #values
                    else:
                        name = param
                        value = ""
                    param = {"name": name, "value": value} # build unit test for empty values
                    param["_sequence"] = seq
                    postData["params"].append(param)
                    seq += 1
            else:
                postData["text"] = body
            self.postData = PostData(postData)

    def render(self):
        """Return a string that should be exactly equal to the
        originally consumed request."""
        return self.puke()

    def puke(self):
        """Return a string that should be exactly equal to the
        original request.

        The 'render' method calls this method, it can be used instead
        if you think your boss might yell at you."""        
        for node in ["url", "httpVersion", "headers"]:
            assert node in self, \
                   "Cannot render request with unspecified {0}".format(node)
        path = '/' + '/'.join(self.url.split("/")[3:]) #this kind of sucks....
        #this really sucks... do this smarter
        r = "{0} {1} {2}\r\n".format(self.method, path, self.httpVersion)
        #!!! not always clear in code where to use self vs self.__dict__
        #!!! need to fix things so always use one or the other, or is clear
        if self.headers:
            #these may need to be capitalized. should be fixed in spec.
            r += "\r\n".join( h.name + ": "+ h.value
                            for h in self.headers)
            r += "\r\n"
        body = ''
        if 'postData' in self and self.postData:
            if not "Content-Type" in self.headers:
                r += "Content-Type: {0}\r\n".format(self.postData.mimeType)    
            joined_params = "&".join( p.name + (p.value and ("="+ p.value))
                                      for p in self.postData.params)
            body = self.postData.text or joined_params
            if not "Content-Length" in self.headers:
                r += "Content-Length: {0}\r\n".format(len(body))
        r += "\r\n"
        r += body
        if body:
            r += "\r\n"
        return r


#------------------------------------------------------------------------------


class Response(MetaHar):

    def validate(self):
        field_defs = {"status":int,
                      "statusText":[unicode,str],
                      "httpVersion":[unicode,str],
                      "cookies":list,
                      "headers":list,
                      "redirectURL":[unicode,str],
                      "headersSize":int,
                      "bodySize":int}
        self._has_fields("status",
                         "statusText",
                         "httpVersion",
                         "cookies",
                         "headers",
                         "content",
                         "redirectURL",
                         "headersSize",
                         "bodySize")
        if "comment" in self.__dict__:    #there's a better way to do this...
            field_defs["comment"] = [unicode, str]

        self._check_field_types(field_defs)

    def __repr__(self):
        # I need to make the naming thing a function....
        return "<Response with code '{0}' - '{1}': {2}>".format(
            ("status" in self and self.status ) or "[undefined]",
            ("statusText" in self and self.statusText) or "[undefined]",
            self._get_printable_kids())

    def _construct(self):
        if "postData" in self:
            self.postData = PostData(self.postData)
        if "headers" in self:
            self.headers = [ Header(header) for header in self.headers]
        if "cookies" in self:
            self.cookies = [ Cookie(cookie) for cookie in self.cookies]

    def devour(self, res, proto='http', comment='', keep_b64_raw=False):
        # Raw request does not have proto info
        assert len(res.strip()), "Empty response cannot be devoured"
        if keep_b64_raw:
            self._b64_raw_req = b64encode(res) #just to be sure we're
                                               #keeping a copy of the
                                               #raw request by
                                               #default. This is a
                                               #person extension to
                                               #the spec.
        res = StringIO(res)
        line = res.next().strip().split()
        httpVersion = line[0]
        status = line[1]
        statusText  =  " ".join(line[2:])
        self.status = status
        self.statusText = statusText
        self.httpVersion = httpVersion
        self.bodySize = 0
        self.headers = []
        self.cookies = []
        seq = 0
        encoding = None
        content = {"size":0,
                   "mimeType":""}
        for line in res:
            line = line.strip()
            if not ( line and ": " in line):
                break
            header = dict(zip(["name", "value"], line.strip().split(': ')))
            if header["name"] == "Content-Length":
                self.bodySize = header["value"]
                continue
            elif header["name"] == "Content-Type":
                # will need to keep an eye out for content type and encoding
                content["mimeType"] = header["value"]
                continue
            elif header["name"] == "Content-Encoding":
                encoding = content["encoding"] = header["value"]
            elif header["name"] == "Host":
                self.url = '{0}://{1}{2}'.format(proto, header["value"], path)
            elif header["name"] == "Location":
                self.redirectURL = header["value"]
            elif header["name"] == "Set-Cookie":
                cookie = Cookie()
                cookie.devour(line.strip())
                self.cookies.append(cookie)
            header["_sequence"] = seq
            self.headers.append(Header(header))
            seq += 1
        self.headerSize = res.tell()
        content["text"] = res.read(int(self.bodySize))
        try:
            content["text"] = content["text"].encode('utf8')
        except UnicodeDecodeError:
            content["text"] = b64encode(content["text"])
            if encoding:
                content["encoding"] =  encoding + "; base64"
            else:
                content["encoding"] =  "base64"
        self.content = Content(content)

    def render(self):
        return self.puke()

    def puke(self):
        pass #!!! need to implement


#------------------------------------------------------------------------------


class Cookie(MetaHar):

    def validate(self): #default behavior
        field_types = {"name":[unicode, str],
                       "value":[unicode, str]}
        self._has_fields(*field_types.keys())
        for field in ["comment", "path", "domain", "expires"]:
            if field in self.__dict__:
                field_types[field] = [unicode, str]
        for field in ["httpOnly", "secure"]:
            if field in self.__dict__:
                field_types[field] = bool
        self._check_field_types(field_types)

    def _construct(self):
        if "expires" in self:
            try:
                self.expires = parser.parse(self.expires)
            except Exception, e:
                raise ValidationError("Failed to parse date: {0}".format(e))

    def __repr__(self):
        return "<Cookie '{0}' set to '{1}': {2}>".format(
            ("name" in self and self.name) or "[undefined]",
            ("name" in self and self.value) or "[undefined]",
            self._get_printable_kids())

    def devour(self, cookie_string):
        #need a unit test for this
        header, cookie = cookie_string.split(': ')
        assert header == 'Set-Cookie', \
               "Cookies must be devoured one at a time."
        values = cookie.split('; ')
        self.name, self.value = values[0].split('=', 1)
        if len(values) == 1:
            return
        for attr in values[1:]:
            if '=' in attr:
                name, value = attr.split('=',1)
                self.__dict__[name.lower()] = value
            else:
                if attr == "Secure":
                    self.secure = True
                elif attr  == "HttpOnly":
                    self.httpOnly = True
            

#------------------------------------------------------------------------------


class Header(KeyValueHar):
    pass


#------------------------------------------------------------------------------


class QueryString(KeyValueHar):
    pass


#------------------------------------------------------------------------------


class PostData(MetaHar):

        def validate(self):
            field_types = {"mimeType":[unicode, str],
                           "params":list,
                           "text":[unicode, str]}
            self._has_fields(*field_types.keys())
            if "comment" in self.__dict__:
                field_types["comment"] = [unicode, str]
            self._check_field_types(field_types)

        def _construct(self):
            if "params" in self.__dict__:
                self.params = [ Param(param) for param in self.params]
                if all('_sequence' in param for param in self.params):
                    self.params.sort(key=lambda i: i._sequence)


#------------------------------------------------------------------------------


class Param(KeyValueHar):

    def validate(self): #default behavior
        field_types = {"name":[unicode, str]}
        self._has_fields(*field_types.keys())
        for field in ["value", "fileName", "contentType", "comment"]:
            if field in self.__dict__:
                field_types[field] = [unicode, str]
        self._check_field_types(field_types)

    def _construct(self):
        if not "value" in self:
            self.value = None

    def __repr__(self):
        return "<{0} {1}: {2}>".format(
            self.__class__.__name__,
            'name' in self.__dict__ and self.name or "[undefined]",
            self._get_printable_kids())


#------------------------------------------------------------------------------


class Content(MetaHar):

    def validate(self):
        self._has_fields("size",
                         "mimeType")
        field_types = {"size":int,
                      "mimeType":[unicode, str]}
        if "compression" in self.__dict__:
            field_types["compression"] = int
        for field in ["text", "encoding", "comment"]:
            if field in self.__dict__:
                field_types[field] = [unicode, str]
        self._check_field_types(field_types)

    def __repr__(self):
        return "<Content {0}>".format(self.mimeType)


#------------------------------------------------------------------------------


class Cache(MetaHar):

    def validate(self):
        field_types={}
        if "comment" in self.__dict__:
            field_types["comment"] = [unicode, str]
        self._check_field_types(field_types)

    def _construct(self):
        for field in ["beforeRequest", "afterRequest"]:
            if field in self.__dict__:
                self.__dict__[field] = RequestCache(
                    self.__dict__.get(field)) #what am I doing.....

    def __repr__(self):
        return "<Cache: {0}>".format(
            self._get_printable_kids())

#------------------------------------------------------------------------------

class RequestCache(MetaHar):

    def validate(self):
        field_types = {"lastAccess":[unicode, str],
                       "eTag":[unicode, str],
                       "hitCount": int}
        self._has_fields(*field_types.keys())
        if "expires" in self.__dict__:
            field_types["expires"] = [unicode, str]
        if "comment" in self.__dict__:
            field_types["comment"] = [unicode, str]
        self._check_field_types(field_types)

        #!!!needs  __repr__

#------------------------------------------------------------------------------

class Timings(MetaHar):

    def validate(self):
        field_defs = {"send":int,
                      "wait":int,
                      "receive":int}
        self._has_fields(*field_defs.keys())
        self._check_field_types(field_defs)

    def __repr__(self):
        return "<Timings: {0}>".format(
            self._get_printable_kids())


###############################################################################
# Main
###############################################################################


if __name__ == "__main__":
    from sys import argv
    if len(argv) > 1:
        if argv[1] == "docs":
            print __doc__
            exit(0)
    for i in ['http://demo.ajaxperformance.com/har/espn.har',
              'http://demo.ajaxperformance.com/har/google.har']:
        try:
            hc = HarContainer(urlopen(i).read())
            print "Successfully loaded har %s from %s" % (repr(hc), i)
        except Exception, e:
            print "failed to load har from %s" % i
            print e

