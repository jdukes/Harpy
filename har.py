#!/usr/bin/env python

import json
from StringIO import StringIO
from socket import inet_pton, AF_INET6, AF_INET #used to validate ip addresses
from socket import error as socket_error #used to validate ip addresses
import os #used for testing, get rid of this later
from dateutil import parser
from datetime import datetime

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
        return ('Field "{0}" missing from json while trying to instantiate {1}'
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
        assert type(init_from) in [unicode, str, file, dict], \
               ("A har can only be initialized from a string, "
                "file object, or dict")
        if init_from:
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
        return "<{0} {1} ({2})>".format(
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
        if "pageref" in self.__dict__:
            field_defs["pageref"] = [unicode, str]
        if "serverIPAddress" in self.__dict__:
            field_defs["serverIPAddress"] = [unicode, str]
        if "connection" in self.__dict__:
            field_defs["connection"] = [unicode, str]
        self._check_field_types(field_defs)
        # if "pageref" in self.__dict__:
        #     for entry in self.parent.entries:
        #         if entry.pageref == self.pageref:
        #             raise ValidationError("Entry pageref {0} must be uniq, "
        #                                   "but it is not".format(self.pageref))
        if "serverIPAddress" in self.__dict__:
            try:
                inet_pton(AF_INET6, self.serverIPAddress) #think of the future
            except socket_error:
                try:
                    inet_pton(AF_INET, self.serverIPAddress)
                except socket_error:
                    raise ValidationError("Invalid IP address {0}: "
                                          "Address does not seem to be either "
                                          "IP4 or IP6".format(self.serverIPAddress))
        #if "connection" in self.__dict__:
            #verify is uniq

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
                self.header.sort(key=lambda i: i._sequence)
        if "cookies" in self.__dict__:
            self.cookies = [ Cookie(cookie) for cookie in self.cookies]
            if all('_sequence' in cookie for cookie in self.cookies):
                self.cookie.sort(key=lambda i: i._sequence)

    def __repr__(self):
        return "<Request to '{0}': {1}>".format(
            self.url,self._get_printable_kids())

    def devour(self, req, proto='http', comment=''):
        # Raw request does not have proto info
        headers, body = req.split('\n\n')
        headers = headers.split('\n')
        method, path, httpVersion = headers[0].split()
        url = '%s://%s/%s' % ( proto, host, path)
        headerSize = len(headers)
        bodySize = len(body)
        #post

    def puke(self):
        return self.render()

    def render(self):
        #this may not work...
        r = "%(method)s %(url)s HTTP/%(httpVersion)s\n" % self.__dict__
        if self.headers:
            #these may need to be capitalized. should be fixed in spec.
            r += "\r\n".join( h.name + ": "+ h.value
                            for h in self.headers)
        r += "\r\n"*2
        

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
        return "<Response with code {0} - '{1}': {2}>".format(
            self.status, self.statusText, self._get_printable_kids())

    def _construct(self):
        if "postData" in self.__dict__:
            self.postData = PostData(self.postData)
        if "headers" in self.__dict__:
            self.headers = [ Header(header) for header in self.headers]
        if "cookies" in self.__dict__:
            self.cookies = [ Cookie(cookie) for cookie in self.cookies]


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
        return "<Cookie {0} set to {1}: {2}>".format(
            self.name, self.value, self._get_printable_kids())

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
        if not "value" in __self__:
            self.value = None

#------------------------------------------------------------------------------


class Content(MetaHar):

    def validate(self):
        self._has_fields("size",
                         "mimeType")
        field_defs = {"size":int,
                      "mimeType":[unicode, str]}
        if "compression" in self.__dict__:
            field_types["compression"] = int
        for field in ["text", "encoding", "comment"]:
            if field in self.__dict__:
                field_types[field] = [unicode, str]
        self._check_field_types(field_defs)

    def __repr__(self):
        return "<Content {0}>".format(self.mimeType)


#------------------------------------------------------------------------------


class Cache(MetaHar):

    def validate(self):
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

        #needs  __repr__

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
    fd = open(os.path.expanduser('~/tmp/demo.har'))
    har = HarContainer(fd)
    fd.close()
