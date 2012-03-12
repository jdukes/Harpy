#!/usr/bin/env python

import json
import re #may not use this
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
###############################################################################
# JSON Overrides and Hooks
###############################################################################


class HarEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, MetaHar):
            return dict( (k,v) for k,v in obj.__dict__.iteritems()
                         if k != "_parent" )
        if isinstance(obj, datetime):
            return str(datetime) #this isn't quite right, needs to be fixed
        return json.JSONEncoder.default(self, obj)

#def as_har(dict):
    


###############################################################################
# HAR Classes
###############################################################################


class MetaHar(object):
    """This is the base class that all HAR objects use. It defines
    default methods and objects."""
    # this needs to be a tree so child objects can validate that they
    # are uniq children
    
    def __init__(self, init_dict=None, parent=None):
        self._parent = parent
        if init_dict:
            self.from_dict(init_dict)
    
    def __str__(self):
        return self.to_json()

    def __repr__(self):
        return "<{0} {1}>".format(
            self.__class__.__name__,
            'name' in self.__dict__ and self.name or "[undefined]")

    def children(self):
        """children() -> list

        Return all objects that are children of the object on which
        the method is called.
        """
        return [ k for k,v in self.__dict__.iteritems()
                 if k[0] != "_" and 
                 (isinstance(v, MetaHar)
                  or isinstance(v, list)) ]

    def from_har_file(self, filename):
        fd = open(filename, 'r')
        self.from_json(fd.read())
        fd.close()

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
        return json.dumps(self, indent=4, cls=HarEncoder)

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

class Har(MetaHar):

    def __repr__(self):
        return "<{0}>".format(
            self.__class__.__name__)            

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
            return "<Log object version {0} created by {1} {2}>".format(
                self.version,
                self.creator.name,
                self.creator.version)
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
        return "<Creator object {0}>".format(self.name)


#------------------------------------------------------------------------------


class Browser(Creator):

    def __repr__(self):
        return "<Browser object {0}>".format(self.name)


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
        return "<Page with title {0}>".format(self.title)


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
        return "<Page timing object>"


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
        return "<Entry object>" 


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

    def __repr__(self):
        return "<Request to {0}>".format(self.url)

    def from_raw_req(self, req, proto='http', comment=''):
        # Raw request does not have proto info
        headers, body = req.split('\n\n')
        headers = headers.split('\n')
        method, path, httpVersion = headers[0].split()
        url = '%s://%s/%s' % ( proto, host, path)
        headerSize = len(headers)
        bodySize = len(body)
        #post

    def to_raw_req(self):
        #this may not work...
        r = "%(method)s %(url)s HTTP/%(httpVersion)s\n" % self.__dict__
        if self.headers:
            #these may need to be capitalized.
            r += "\n".join( "%(name)s: %(value)s" % h
                            for h in self.headers)
            r += "\n"
        if self.cookies:
            r += "Cookies: " + "&".join( "%(name)s: %(value)s" % c
                                         for c in self.cookies)
        
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
        return "<Response with code {0}:{1}>".format(self.status, self.statusText)


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
        try:
            self.expires = parser.parse(self.expires)
        except Exception, e:
            raise ValidationError("Failed to parse date: {0}".format(e))

    def __repr__(self):
        return "<Cookie {0} set to {1}>".format(self.name, self.value)

#------------------------------------------------------------------------------


class Header(MetaHar):
    pass


#------------------------------------------------------------------------------


class QueryString(MetaHar):
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


#------------------------------------------------------------------------------


class Param(MetaHar):

    def validate(self): #default behavior
        field_types = {"name":[unicode, str]}
        self._has_fields(*field_types.keys())
        for field in ["value", "fileName", "contentType", "comment"]:
            if field in self.__dict__:
                field_types[field] = [unicode, str]
        self._check_field_types(field_types)


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
                self.__dict__.__setitem__(field) = RequestCache(
                    self.__dict__.get(field))
    
    def __repr__(self):
        return "<Cache>"

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
        return "<Timings>" #fix
    

###############################################################################
# Main
###############################################################################


if __name__ == "__main__":
    har = Har()
    #har.from_har_file(os.path.expanduser('~/tmp/demo.har'))
    har.from_har_file(os.path.expanduser('./demo.har'))

