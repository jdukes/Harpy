#!/usr/bin/env python

# well fuck.
# 1) decide if validation logic be a private method of the metaclass,
# or should it be moved to helper functions...
# 2) move datetime validation to be a function or method.


import json
import re #may not use this
from socket import inet_pton, AF_INET6, AF_INET #used to validate ip addresses
from socket import error as socket_error #used to validate ip addresses
import os #used for testing, get rid of this later
from dateutil import parser


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

#
##############################################################################
# Helper Functions
###############################################################################

#------------------------------------------------------------------------------
# validation helpers
#------------------------------------------------------------------------------

# do I put something here, or not??

#------------------------------------------------------------------------------
# other helpers
#------------------------------------------------------------------------------

def har_from_request():
    pass


def har_from_response():
    pass


def har_from_file(name):
    fd = open(name, 'r')
    json_data = json.loads(fd.read())
    log = Log(json_data["log"])
    return log

def har_from_stream():
    pass


#def res_from_urllib():

#def req_to_urllib():

###############################################################################
# HAR Classes
###############################################################################

class MetaHar(object):
    """This is the base class that all HAR objects use. It defines
    default methods and objects."""
    # this needs to be a tree so child objects can validate that they
    # are uniq children
    
    def __init__(self, json_obj, parent=None):
        self._parent = parent
        assert type(json_obj) is dict, \
               "HAR objects must be created from a dictionary"
        self._json = json_obj
        self._validate()
        self._construct()

    def _construct(self):
        #when constructing child objects, pass self so parent hierachy
        #can exist
        pass
    
    def __getattr__(self, name):
        if name in self.__dict__:
            return object.__getattribute__(self, name)
        elif name in self._json:
            return self._json[name]

    def __contains__(self, name):
        return name in self._json

    def __getitem__(self, name):
        return self._json[name]

    def __str__(self):
        return self.to_json()

    def __repr__(self):
        #getet returns none if not found, allowing for this short circuit. 
        return "<{0} {1}>".format(self.__class__.__name__,
                                  self.name or self.title)

    def to_json(self):
        return json.dumps(self._json)
 
    def _validate(self): #default behavior
        field_types = {"name":[unicode, str],
                       "value":[unicode, str]}
        self._has_fields("name",
                         "value")
        if "comment" in self:
            field_types["comment"] = [unicode, str]
        self._fields_of_type(field_types)

    def _has_fields(self, *fields):
        for field in fields:
            if not field in self._json:
                raise MissingValueExcpetion(field, self.__class__.__name__)

    def _fields_of_type(self, **field_defs):
        for fname, ftype in field_defs:
            if ftype == list:
                assert type(self[fname]) in ftype, (
                    "{0} filed '{1}' must be one of types: {2}"
                    .format(self.__class__.__name__, fname, ftype))
            else:
                assert type(self[fname]) is ftype, (
                    "{0} filed '{1}' must be of type: {2}"
                    .format(self.__class__.__name__, fname, ftype))
                                
                
#------------------------------------------------------------------------------


class Log(MetaHar):

    def _validate(self):
        self._has_fields("version", "creator", "entries")
        field_defs = {"version":[unicode, str],
                      "entries":list}
        if self.version is '':
            self.version = "1.1"
        if "pages" in self:
            field_defs["pages"] = list
        if "comment" in self:
            field_defs["comment"] = [unicode, str]
        self._fields_of_type(field_defs)

    def _construct(self):
        self.creator = Creator(self.creator)
        if "browser" in self:
            self.browser = Browser(self.browser)
        if "pages" in self:
            self.pages = [ Page(page) for page in self.pages]
        self.entries = [ Entry(entry) for entry in self.entries]

    def __repr__(self):
        return "<Log object version {0} created by {1} {2}>".format(
            self.version,
            self.creator.name,
            self.creator.version)
            

#------------------------------------------------------------------------------


class Creator(MetaHar):

    def _validate(self):
        self._has_fields("name",
                         "version")
        field_defs = {"name": [unicode, str],
                      "version": [unicode, str]}
        if "comment" in self:
            field_defs["comment"] = [unicode, str]
        self.__fields_of_type(field_defs)

    def __repr__(self):
        return "<Creator object {0}>".format(self.name)


#------------------------------------------------------------------------------


class Browser(Creator):

    def __repr__(self):
        return "<Browser object {0}>".format(self.name)


#------------------------------------------------------------------------------


class Page(MetaHar):

    def _validate(self):
        self._has_fields("startedDateTime",
                         "id",
                         "title",
                         "pageTimings")
        field_defs = {"startedDateTime":[unicode, str],
                      "id":[unicode, str],
                      "title":[unicode, str]}
        if "comment" in self:
            field_types["comment"] = [unicode, str]
        self._fields_of_type(field_defs)
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

    def _validate(self):
        field_defs = {}
        if "onContentLoad" in self:
            field_defs["onContentLoad"] = int
        if "onLoad" in self:
            field_defs["onLoad"] = int
        if "comment" in self:
            field_defs["comment"] = [unicode, str]
        self._fields_of_type(field_defs)

    def __repr__(self):
        return "<Page timing object>"


#------------------------------------------------------------------------------


class Entry(MetaHar):

    def _validate(self):
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
        self._fields_of_type(field_defs)
        # if "pageref" in self:
        #     for entry in self.parent.entries:
        #         if entry.pageref == self.pageref:
        #             raise ValidationError("Entry pageref {0} must be uniq, "
        #                                   "but it is not".format(self.pageref))
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
        #if "connection" in self:
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

    def _validate(self):
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
        if "comment" in self:
            field_defs["comment"] = [unicode, str]
        self._fields_of_type(field_defs)

    def _construct(self):
        if "postData" in self:
            self.postData = Postdata(self.postData)

    def __repr__(self):
        return "<Request to {0}>".format(self.url)


#------------------------------------------------------------------------------


class Response(MetaHar):

    def _validate(self):
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
        if "comment" in self:    #there's a better way to do this...
            field_defs["comment"] = [unicode, str]

        self._fields_of_type(field_defs)

    def __repr__(self):
        return "<Response with code {0}:{1}>".format(self.status, self.statusText)


#------------------------------------------------------------------------------

#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# left off here
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# finish validation

class Cookie(MetaHar):
    pass

#------------------------------------------------------------------------------


class Header(MetaHar):
    pass


#------------------------------------------------------------------------------


class QueryString(MetaHar):
    pass


#------------------------------------------------------------------------------


class Param(MetaHar):
    pass
    

#------------------------------------------------------------------------------


class Content(MetaHar):

    def _validate(self):
        self._has_fields("size",
                         "mimeType")
        field_defs = {"size":int,
                      "mimeType":[unicode, str]}
        self._fields_of_type(field_defs)

    def __repr__(self):
        return "<Content {0}>".format(self.mimeType)


#------------------------------------------------------------------------------


class Cache(MetaHar):

    #needs more
    
    def __repr__(self):
        return "<Cache>"

#------------------------------------------------------------------------------


class Timings(MetaHar):

    def _validate(self):
        self._has_fields("send",
                         "wait",
                         "recieve")
        field_defs = {"send":int,
                      "wait":int,
                      "recieve":int}
        self._fields_of_type(field_defs)

    def __repr__(self):
        return "<Timings>" #fix
    

###############################################################################
# Main
###############################################################################


if __name__ == "__main__":
    pass
    #log = har_from_file(os.path.expanduser('~/tmp/www.google.com.bad.har'))

