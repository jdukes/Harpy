#!/usr/bin/env python
# todo: write unit tests
#       run lint/pep8 checks

import json
from StringIO import StringIO
from socket import inet_pton, AF_INET6, AF_INET #used to validate ip addresses
from socket import error as socket_error #used to validate ip addresses
from urllib2 import urlopen
from dateutil import parser
from datetime import datetime
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
        if isinstance(obj, datetime):
            return str(datetime) #!!!this isn't quite right, needs to be fixed
        return json.JSONEncoder.default(self, obj)


###############################################################################
# stream deserializer (pipe handler)
###############################################################################


#def mario(


###############################################################################
# HAR Classes
###############################################################################


class MetaHar(object):
    """This is the base class that all HAR objects use. It defines
    default methods and objects."""
    # this needs to be a tree so child objects can validate that they
    # are uniq children

    def __init__(self, init_from=None, parent=None):
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
        """_get_printable_kids() -> list

        Return all objects that are children of the object on which
        the method is called.
        """
        return tuple( str(k) for k,v in self.__dict__.iteritems()
                 if (str(k) != "_parent" and
                     (isinstance(v, MetaHar)
                      or isinstance(v, list)
                      or isinstance(v, unicode)
                      or isinstance(v, str)))) or '(empty)'


    def get_children(self):
        """get_children() -> list

        Return all objects that are children of the object on which
        the method is called.
        """
        #dunno if I like this method... maybe should be a generator?
        return [ v for k,v in self ]

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
        self._has_fields("log")
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

    def __repr__(self):
        return "<Request to '{0}': {1}>".format(
            ("url" in self and self.url) or  "[undefined]",
            self._get_printable_kids())

    def devour(self, req, proto='http', comment='', keep_b64_raw=True):
        # Raw request does not have proto info
        if keep_b64_raw:
            self._b64_raw_req = b64encode(req) #just to be sure we're
                                               #keeping a copy of the
                                               #raw request by
                                               #default. This is a
                                               #person extension to
                                               #the spec.
        req = StringIO(req)
        method, path, httpVersion = req.next().strip().split()
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
        for header in req:
            header = header.strip()
            if not header:
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
            print header
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
                        name, value = param.split('=')
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
        return self.puke()

    def puke(self):
        for node in ["url", "httpVersion", "headers"]:
            assert node in self, \
                   "Cannot render request with unspecified {0}".format(node)
        path = '/' + '/'.join(self.url.split("/")[3:]) #this kind of sucks....
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

    def devour(self, res, proto='http', comment='', keep_b64_raw=True):
        # Raw request does not have proto info
        if keep_b64_raw:
            self._b64_raw_req = b64encode(req) #just to be sure we're
                                               #keeping a copy of the
                                               #raw request by
                                               #default. This is a
                                               #person extension to
                                               #the spec.
        res = StringIO(res)
        httpVersion, status, statusText  = res.next().strip().split()
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
            if not line:
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
                encoding = content["encoding"] = "base64" # for right now if we see something that's encoded we'll base64 it so it's portable
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
        if encoding:
            content["text"] = b64encode(content["text"])
        self.content = Content(content)

    def render(self):
        return self.puke()

    def puke(self):
        pass


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
        self.name, self.value = values[0].split('=')
        if len(values) == 1:
            return
        for attr in values[1:]:
            if '=' in attr:
                name, value = attr.split('=')
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
        self._has_fields("send",
                         "wait",
                         "receive")
        field_defs = {"send":int,
                      "wait":int,
                      "receive":int}

        self._check_field_types(field_defs)

    def __repr__(self):
        return "<Timings: {0}>".format(
            self._get_printable_kids())


###############################################################################
# Main
###############################################################################


if __name__ == "__main__":
    #har = HarContainer(urlopen('http://demo.ajaxperformance.com/har/espn.har').read())
    #har = HarContainer(urlopen('http://demo.ajaxperformance.com/har/google.har').read())
    hc = HarContainer(open('/home/jdukes/tmp/demo.har').read())

