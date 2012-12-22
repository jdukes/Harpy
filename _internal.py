#!/usr/bin/env python

import json
from StringIO import StringIO
from datetime import datetime
try:
    from dateutil import tz
except ImportError:
    print ("Please verify that dateutil is installed. On Debian based systems "
           "like Ubuntu this can be  done with `aptitude install "
           "python-dateutil` or `easy_install dateutil`.")
    raise

now = datetime.now #we imported datetime already, we only use now() in har.py

##############################################################################
# Constants
###############################################################################
TIMEZONE = tz.tzlocal()


###############################################################################
# Exceptions
###############################################################################


class MissingValue(Exception):

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


###############################################################################
# HAR Meta Classes
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
                  or isinstance(v, dict)
                  or isinstance(v, int)
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
        try:
            return self.__getattribute__(name)
        except AttributeError:
            return default

    def _get_printable_kids(self):
        """Return a tuple of all objects that are children of the
        object on which the method is called.

        """
        return tuple(str(k) for k, v in self.__dict__.iteritems()
                 if (str(k) != "_parent" and
                     (isinstance(v, _MetaHar) # !!! this is aweful
                      or isinstance(v, list)  # all of this
                      or isinstance(v, unicode)
                      or isinstance(v, dict)  # needs to go
                      or isinstance(v, int)
                      or isinstance(v, str)))) or '(empty)'

    def replace(self, **kwarg):
        """Return a copy of the object with a varabile set to a value.

        This is essentially __setattr__ except that it returns an
        instance of the object with the new value when called. This
        method was added to make comprensions easier to write. The
        textbook use case is for sequencing:

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
                raise ValidationError(e.message) #depricated, fix

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
