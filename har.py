#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

    In [1]: hc
    Out[1]: <HarContainer: ('log',)>

    In [2]: print hc
    {"log": {"version": "1.2", "creator":
             {"version": "$Id$", "name": "Harpy"}, "entries": []}}

All objects have default values which are pre-set::

    In [3]: r = Request()

    In [4]: r
    Out[4]: <Request to 'http://example.com/': ('cookies', 'url',
                'queryString', 'headers', 'method', 'httpVersion')>

To not set default values on object creation disable default settings::

    In [5]: r = Request(empty=True)

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

     In [8]: r = Request(r'{"cookies": [], "url":
                          "http://example.com/foobarbaz", ...)

     In [9]: r
     Out[9]: <Request to 'http://example.com/foobarbaz':
                 ('cookies', 'url', 'queryString', 'headers',
                  'httpVersion', 'method')>

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
      Out[18]: 'GET / HTTP/1.1\\r\\nHost: localhost:1234\\r\\nUser-Agent: ...

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

    In [21]: [ (e.request.url, e.response.status) for e in hc.log.entries
               if 'www.google.com' in e.request.url ]
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
according to the specification. The dateutil module is used to manage
this. All things without timezones will be localized to the user's
time. This can be configured by changing har.TIMEZONE. This may be a
bug waiting to bite.

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
from StringIO import StringIO
from socket import inet_pton, AF_INET6, AF_INET #used to validate ip addresses
from socket import error as socket_error #used to validate ip addresses
from httplib import HTTPMessage #overridden for parsing headers
from urllib2 import urlopen #this should be removed

try:
    from dateutil import parser, tz
except ImportError:
    print ("Please verify that dateutil is installed. On Debian based systems "
           "like Ubuntu this can be  done with `aptitude install "
           "python-dateutil` or `easy_install dateutil`.")
    raise
from datetime import datetime

##############################################################################
# Constants
###############################################################################

__version__ = "$Id$"

TIMEZONE = tz.tzlocal()

###############################################################################
# Exceptions
###############################################################################


class MissingValueException(Exception):

    def __init__(self, value, in_class):
        self.value = value
        self.in_class = in_class

    def __str__(self):
        return (('Field "{0}" missing from input '
                'while trying to instantiate "{1}"').format(
                    self.value,
                    self.in_class))


class ValidationError(Exception):

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return str(self.msg)


class InvalidChild(Exception):
    """This exception should be raised when an invalid child is added to
    a parent.
    """
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return str(self.msg)


###############################################################################
# Interface Functions and Classes
###############################################################################


def _localize_datetime(dto):
    if not dto.tzinfo: #handle zone info not being added by python
        dto = dto.replace(tzinfo=TIMEZONE)
    return dto
    #according to the spec this needs to be ISO 8601
    #YYYY-MM-DDThh:mm:ss.sTZD


class HarEncoder(json.JSONEncoder):
    """json Encoder override.

    This takes care of correctly encoding time objects into json.

    """

    def default(self, obj):
        if isinstance(obj, _MetaHar):
            return dict((k, v) for k, v in obj.__dict__.iteritems()
                         if k != "_parent")
        if isinstance(obj, datetime):
            obj = _localize_datetime(obj)
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)


class HARMessage(HTTPMessage):
    """Class used to parse headers."""

    def __init__(self, fp, seekable = 1):
        self.sequence = 0
        self.har_headers = []
        HTTPMessage.__init__(self, fp, seekable)

    def addheader(self, key, value):
        HTTPMessage.addheader(self, key, value)
        header = {"name":  key,
                  "value": value,
                  "_sequence": self.sequence}
        self.har_headers.append(Header(header))
        self.sequence += 1

    def get_har_headers(self):
        return self.har_headers

###############################################################################
# HAR Classes
###############################################################################


class _MetaHar(object):
    """This is the base class that all HAR objects use. It defines
    default methods and objects."""
    # this needs to be a tree so child objects can validate that they
    # are uniq children

    def __init__(self, init_from=None, parent=None, empty=False):
        #it should be possible to init without validataion
        """ This is the _MetaHar object. It is used as the meta class
        for other objects. It should never be instantiated directly.

        """
        assert not self.__class__ in [_MetaHar, _KeyValueHar], (
            "This is a meta class used to type other classes. "
            "To use this class create a new object that extends it")
        self._parent = parent
        if init_from:
            #!!! there might be a better way to do this
            assert type(init_from) in [unicode, str, file, dict], (
                "A har can only be initialized from a string, file "
                "object, dict")
            if type(init_from) in [unicode, str, file]:
                if type(init_from) is unicode or type(init_from) is str:
                    fd = StringIO(init_from)
                else:
                    fd = init_from
                self.from_json(fd.read())
                fd.close()
            else:
                self.from_dict(init_from)
        elif not empty:
            self.set_defaults()

    def __iter__(self):
        return (v for k, v in self.__dict__.iteritems()
                 if k != "_parent" and
                 (isinstance(v, _MetaHar)
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
            self.__dict__.get('name', "[undefined]"),
            self._get_printable_kids())

    def _get(self, name, default='[uninitialized]'):
        """Internal method to return a default value.
        """
        return (name in self and
                self.__getattribute__(name)) or default

    def _get_printable_kids(self):
        """Return a tuple of all objects that are children of the
        object on which the method is called.

        """
        return tuple(str(k) for k, v in self.__dict__.iteritems()
                 if (str(k) != "_parent" and
                     (isinstance(v, _MetaHar)
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
        return [kid for kid in self] # this comes from
                                       # _get_printable_kids()

    def from_json(self, json_data):
        json_data = json.loads(json_data)
        self.from_dict(json_data) #get first element

    def from_dict(self, json_dict):
        assert type(json_dict) is dict, "from_dict must be passed a dictionary"
        self.__dict__.update(json_dict)
        self.validate_input()
        self._construct()

    def _construct(self):
        #when constructing child objects, pass self so parent hierachy
        #can exist
        pass

    def set_defaults(self):
        """This method sets defaults for objects not instantiated via
        'init_from' if 'empty' parameter is set to False (default). It can
        also be used to reset a har to a default state."""
        pass

    def to_json(self):
        #return json.dumps(self, indent=4, cls=HarEncoder)
        ## for now we're going to use line return as a deleniator
        ## later we'll write a json stream parser
        return json.dumps(self, indent=None, cls=HarEncoder)

    def validate_input(self): #default behavior
        # change this to a couple of class vars
        field_types = {"name": [unicode, str],
                       "value": [unicode, str]}
        self._has_fields(*field_types.keys())
        if "comment" in self.__dict__:
            field_types["comment"] = [unicode, str]
        self._check_field_types(field_types)

    def _has_fields(self, *fields):
        for field in fields:
            if not field in self.__dict__:
                raise MissingValueException(field, self.__class__.__name__)

    def _check_field_types(self, field_defs):
        for fname, ftype in field_defs.iteritems():
            try:
                if type(ftype) == list:
                    assert type(self.__dict__[fname]) in ftype, (
                        "{0} failed '{1}' must be one of types: {2}"
                        .format(self.__class__.__name__, fname, ftype))
                else:
                    assert type(self.__dict__[fname]) is ftype, (
                        "{0} failed '{1}' must be of type: {2}"
                        .format(self.__class__.__name__, fname, ftype))
            except Exception, e:
                raise ValidationError(e.message)

    def _check_empty(self, fields):
        if not type(fields) is list:
            fields = [fields]
        for field in fields:
            if not self.__dict__[field]:
                raise ValidationError(
                    "{0} failed '{1}' must not be empty"
                    .format(self.__class__.__name__, field))


#------------------------------------------------------------------------------


class _KeyValueHar(_MetaHar):

    def validate_input(self): #default behavior
        field_types = {"name": [unicode, str],
                       "value": [unicode, str]}
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


class HarContainer(_MetaHar):

    def __repr__(self):
        return "<{0}: {1}>".format(
            self.__class__.__name__,
            self._get_printable_kids())

    def _construct(self):
        self.log = Log(self.log, self)

    def set_defaults(self):
        """This method sets defaults for objects not instantiated via
        'init_from' if 'empty' parameter is set to False (default). It can
        also be used to reset a har to a default state."""
        self.log = Log()

    def validate_input(self):
        field_types = {"log": dict}
        self._has_fields(*field_types.keys())
        self._check_field_types(field_types)
        self._check_empty("log")


#------------------------------------------------------------------------------


class Log(_MetaHar):

    def validate_input(self):
        self._has_fields("version", "creator", "entries")
        field_defs = {"version": [unicode, str],
                      "entries": list}
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
            self.pages = [Page(page) for page in self.pages]
        self.entries = [Entry(entry) for entry in self.entries]

    def set_defaults(self):
        """This method sets defaults for objects not instantiated via
        'init_from' if 'empty' parameter is set to False (default). It can
        also be used to reset a har to a default state.

        """
        self.version = "1.2"
        self.creator = Creator()
        self.entries = []

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


class Creator(_MetaHar):

    def validate_input(self):
        self._has_fields("name",
                         "version")
        field_defs = {"name": [unicode, str],
                      "version": [unicode, str]}
        if "comment" in self.__dict__:
            field_defs["comment"] = [unicode, str]
        self._check_field_types(field_defs)

    def set_defaults(self):
        """This method sets defaults for objects not instantiated via
        'init_from' if 'empty' parameter is set to False (default). It can
        also be used to reset a har to a default state.

        """
        self.version = __version__
        self.name = "Harpy"

    def __repr__(self):
        return "<Created by {0}: {1}>".format(
            self._get("name"),
            self._get_printable_kids())


#------------------------------------------------------------------------------


class Browser(Creator):

    def __repr__(self):
        return "<Browser '{0}': {1} >".format(
            self._get("name"), self._get_printable_kids())


#------------------------------------------------------------------------------


class Page(_MetaHar):

    def validate_input(self):
        self._has_fields("startedDateTime",
                         "id",
                         "title",
                         "pageTimings")
        field_defs = {"startedDateTime": [unicode, str],
                      "id": [unicode, str],
                      "title": [unicode, str]}
        if "comment" in self.__dict__:
            field_types["comment"] = [unicode, str]
        self._check_field_types(field_defs)
        #make sure id is uniq

    def _construct(self):
        try:
            self.startedDateTime = parser.parse(self.startedDateTime)
        except Exception, err:
            raise ValidationError("Failed to parse date: {0}".format(err))
        self.pageTimings = PageTimings(self.pageTimings)

    def set_defaults(self):
        """This method sets defaults for objects not instantiated via
        'init_from' if 'empty' parameter is set to False (default). It can
        also be used to reset a har to a default state.

        """
        self.startedDateTime = _localize_datetime(datetime.now())
        self.id = None #this will need to be added later
        # id is not very clear in the spec... 
        self.title = "[Title could not be determined]"
        #title cannot be set to a valid default
        #invalid html could result in this.
        self.pageTimings = PageTimings()

    def __repr__(self):
        return "<Page with title '{0}': {1}>".format(
            self._get("title", '[undefined]'),
            self._get_printable_kids())


#------------------------------------------------------------------------------


class PageTimings(_MetaHar):

    def validate_input(self):
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


class Entry(_MetaHar):

    def validate_input(self):
        field_defs = {"startedDateTime": [unicode, str]}
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
        if "pageref" in self and "_parent" in self and self._parent:
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
                                          "IP4 or IP6".format(
                                              self.serverIPAddress))

    def _construct(self):
        self.request = Request(self.request)
        self.response = Response(self.response)
        self.cache = Cache(self.cache)
        self.timings = Timings(self.timings)

    def __repr__(self):
        return "<Entry object {0}>".format(self._get_printable_kids())

    # def set_defaults(self):
    #     """This method sets defaults for objects not instantiated via
    #     'init_from' if 'empty' parameter is set to False (default). It can
    #     also be used to reset a har to a default state.

    #     """
    #     self.startedDateTime = _localize_datetime(datetime.now())
    #     #ok, this isn't right... 
    #     self.request = Request()
    #     self.response = Response()


#------------------------------------------------------------------------------


class Request(_MetaHar):

    def validate_input(self):
        field_defs = {"method": [unicode, str], #perhaps these should
                                               #be under _has_fields
                      "url": [unicode, str],
                      "httpVersion": [unicode, str],
                      "headersSize": int,
                      "bodySize": int}
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
        """This method sets defaults for objects not instantiated via
        'init_from' if 'empty' parameter is set to False (default). It can
        also be used to reset a har to a default state.

        """
        self.from_dict({"cookies": [],
                        "url": "http://example.com/",
                        "queryString": [],
                        "headers": [{"name": "Accept", "value": "*/*"},
                                    {"name": "Accept-Language",
                                     "value": "en-US"},
                                    {"name": "Accept-Encoding",
                                     "value": "gzip"},
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
            h = Header({"name": name, "value": value})
        headers.append(h)

    def __repr__(self):
        return "<Request to '{0}': {1}>".format(
            self._get("url"),
            self._get_printable_kids())

    def devour(self, req, proto='http', comment='', keep_b64_raw=False):
        # Raw request does not have proto info
        assert len(req.strip()), "Empty request cannot be devoured"
        if keep_b64_raw:
            self._b64_raw_req = req.encode('base64') #just to be sure we're
                                                     #keeping a copy
                                                     #of the raw
                                                     #request by
                                                     #default. This is
                                                     #a person
                                                     #extension to the
                                                     #spec.
                                                     #
                                                     #This is not default
        req = StringIO(req)
        #!!! this doesn't always happen
        method, path, httpVersion = req.next().strip().split()
        #some people ignore the spec, this needs to be handled.
        self.method = method
        self.httpVersion = httpVersion
        self.bodySize = 0
        harmessage = HARMessage(req)
        self.headers = harmessage.get_har_headers()
        postData = None
        if method == "POST":
            postData = {"params": [],
                        "mimeType": "",
                        "text": ""}
            self.bodySize = harmessage.get('Content-Length')
            postData["mimeType"]  = harmessage.get('Content-Type')
        host = harmessage.get("Host")
        self.url = '{0}://{1}{2}'.format(proto, host, path)
        headerSize = req.tell()
        seq = 0
        if postData:
            body = req.read(int(self.bodySize))
            if postData["mimeType"] == "application/x-www-form-urlencoded":
                seq = 0
                for param in body.split('&'):
                    if "=" in param:
                        name, value = param.split('=', 1) #= is a valid
                                                          #character in
                                                          #values
                    else:
                        name = param
                        value = ""
                    param = {"name": name, "value": value}
                    # build unit test for empty values
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
        if you think your boss might yell at you.

        """
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


class Response(_MetaHar):

    def validate_input(self):
        field_defs = {"status": int,
                      "statusText": [unicode,str],
                      "httpVersion": [unicode,str],
                      "cookies": list,
                      "headers": list,
                      "redirectURL": [unicode,str],
                      "headersSize": int,
                      "bodySize": int}
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
            self._get("status"),
            self._get("statusText"),
            self._get_printable_kids())

    def _construct(self):
        if "postData" in self:
            self.postData = PostData(self.postData)
        if "headers" in self:
            self.headers = [ Header(header) for header in self.headers]
        if "cookies" in self:
            self.cookies = [ Cookie(cookie) for cookie in self.cookies]

    def devour(self, res, proto='http', comment='', keep_b64_raw=False):
        # Raw response does not have proto info
        assert len(res.strip()), "Empty response cannot be devoured"
        if keep_b64_raw:
            self._b64_raw_req = res.encode('base64') #just to be sure we're
                                                     #keeping a copy of the
                                                     #raw response by
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
        content = {"size": 0,
                   "mimeType": ""}
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
            content["text"] = content["text"].encode('base64')
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


class Cookie(_MetaHar):

    def validate_input(self): #default behavior
        field_types = {"name": [unicode, str],
                       "value": [unicode, str]}
        self._has_fields(*field_types.keys())
        for field in ["comment", "path", "domain", "expires"]:
            if field in self.__dict__:
                field_types[field] = [unicode, str]
        for field in ["httpOnly", "secure"]:
            if field in self.__dict__:
                field_types[field] = bool
        # Handle fields which can be null, or not set.
        for field in ["expires"]:
            if field in self.__dict__:
                field_types[field] = [unicode, str, type(None)]
        self._check_field_types(field_types)

    def _construct(self):
        if "expires" in self:
            try:
                self.expires = parser.parse(self.expires)
            except Exception, err:
                raise ValidationError("Failed to parse date: {0}".format(err))

    def __repr__(self):
        return "<Cookie '{0}' set to '{1}': {2}>".format(
            self._get("name"),
            self._get("value"),
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
                name, value = attr.split('=', 1)
                self.__dict__[name.lower()] = value
            else:
                if attr == "Secure":
                    self.secure = True
                elif attr  == "HttpOnly":
                    self.httpOnly = True


#------------------------------------------------------------------------------


class Header(_KeyValueHar):
    pass


#------------------------------------------------------------------------------


class QueryString(_KeyValueHar):
    pass


#------------------------------------------------------------------------------


class PostData(_MetaHar):

    def validate_input(self):
        field_types = {"mimeType": [unicode, str],
                       "params": list,
                       "text": [unicode, str]}
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


class Param(_KeyValueHar):

    def validate_input(self): #default behavior
        field_types = {"name": [unicode, str]}
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


class Content(_MetaHar):

    def validate_input(self):
        self._has_fields("size",
                         "mimeType")
        field_types = {"size": int,
                      "mimeType": [unicode, str]}
        if "compression" in self.__dict__:
            field_types["compression"] = int
        for field in ["text", "encoding", "comment"]:
            if field in self.__dict__:
                field_types[field] = [unicode, str]
        self._check_field_types(field_types)

    def __repr__(self):
        return "<Content {0}>".format(self.mimeType)


#------------------------------------------------------------------------------


class Cache(_MetaHar):

    def validate_input(self):
        field_types = {}
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

class RequestCache(_MetaHar):

    def validate_input(self):
        field_types = {"lastAccess": [unicode, str],
                       "eTag": [unicode, str],
                       "hitCount": int}
        self._has_fields(*field_types.keys())
        if "expires" in self.__dict__:
            field_types["expires"] = [unicode, str]
        if "comment" in self.__dict__:
            field_types["comment"] = [unicode, str]
        self._check_field_types(field_types)

        #!!!needs  __repr__

#------------------------------------------------------------------------------

class Timings(_MetaHar):

    def validate_input(self):
        field_defs = {"send": int,
                      "wait": int,
                      "receive": int}
        self._has_fields(*field_defs.keys())
        self._check_field_types(field_defs)

    def __repr__(self):
        return "<Timings: {0}>".format(
            self._get_printable_kids())


###############################################################################
# Interface Functions and Classes
###############################################################################


def test():
    for i in ['http://demo.ajaxperformance.com/har/espn.har',
              'http://demo.ajaxperformance.com/har/google.har']:
        try:
            req = urlopen(i)
            #req.headers['content-type'].split('charset=')[-1]
            content = req.read()
            hc = HarContainer(content)
            print "Successfully loaded har %s from %s" % (repr(hc), i)
        except Exception, err:
            print "failed to load har from %s" % i
            print err

def usage(progn):
    use = "usage: %s (docs|test)\n\n" % progn
    use += "Either print out documentation for this module or run a test."
    return use

if __name__ == "__main__":
    from sys import argv
    if len(argv) > 1:
        if argv[1] == "docs":
            print __doc__
        elif argv[1] == "test":
            test()
    else:
        print usage(argv[0])

# Local variables:
# eval: (add-hook 'after-save-hook '(lambda () (shell-command "pep8 har.py > lint")) nil t)
# end:
