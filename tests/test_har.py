#!/usr/bin/env python

import unittest
import re

from datetime import datetime
from dateutil import tz, parser
from sys import path

path.append('./')
path.append('../')
import har

class TestHarEncoder(unittest.TestCase):

    def setUp(self):
        self.har_encoder = har.HarEncoder()
        self.iso8601_re = re.compile(
            r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?\+\d{2}:\d{2}')
            
    def test_date_decoding(self):
        good_json = '2009-07-24T19:20:30.45+01:00'
        good_dt = datetime(2009, 07, 24,
                           19, 20, 30, 450000,
                           tz.tzoffset(None, 3600))
        test_json = self.har_encoder.default(good_dt)
        g_match = re.match(self.iso8601_re, good_json)
        t_match = re.match(self.iso8601_re, test_json)
        #This isn't a great test... we should have a better one
        self.assertTrue(g_match)
        self.assertTrue(t_match)

    def test_date_encoding(self):
        good_json = '2009-07-24T19:20:30.45+01:00'
        good_dt = datetime(2009, 07, 24,
                           19, 20, 30, 450000,
                           tz.tzoffset(None, 3600))
        test_dt = parser.parse(good_json)
        self.assertEqual(good_dt, test_dt)

    def test_setting_tz(self):
        no_tz = datetime.now()
        gmt = no_tz.replace(tzinfo= tz.tzoffset(None, 0))
        har.TIMEZONE = tz.tzoffset(None, 0)
        good_json = self.har_encoder.default(gmt)
        test_json = self.har_encoder.default(no_tz)
        self.assertEqual(good_json, test_json)
        

class test__MetaHar(unittest.TestCase):

    def test___init__(self):
        #Should not ever instantiate.
        with self.assertRaises(AssertionError):
            har._MetaHar()

class test__KeyValueHar(unittest.TestCase):

    def test__init__(self):
        #Should not ever instantiate.
        with self.assertRaises(AssertionError):
            har._KeyValueHar()

class TestHarContainer(unittest.TestCase):

    def test_default_init_(self):
        har_container = HarContainer()
        

    def test___init__(self):
        har_container = HarContainer()
        assert False # TODO: implement your test here

    def test___repr__(self):
        # har_container = HarContainer()
        # self.assertEqual(expected, har_container.__repr__())
        assert False # TODO: implement your test here

    def test_validate(self):
        # har_container = HarContainer()
        # self.assertEqual(expected, har_container.validate())
        assert False # TODO: implement your test here

class TestLog(unittest.TestCase):
    def test___repr__(self):
        # log = Log()
        # self.assertEqual(expected, log.__repr__())
        assert False # TODO: implement your test here

    def test_validate(self):
        # log = Log()
        # self.assertEqual(expected, log.validate())
        assert False # TODO: implement your test here

class TestCreator(unittest.TestCase):
    def test___repr__(self):
        # creator = Creator()
        # self.assertEqual(expected, creator.__repr__())
        assert False # TODO: implement your test here

    def test_validate(self):
        # creator = Creator()
        # self.assertEqual(expected, creator.validate())
        assert False # TODO: implement your test here

class TestBrowser(unittest.TestCase):
    def test___repr__(self):
        # browser = Browser()
        # self.assertEqual(expected, browser.__repr__())
        assert False # TODO: implement your test here

class TestPage(unittest.TestCase):
    def test___repr__(self):
        # page = Page()
        # self.assertEqual(expected, page.__repr__())
        assert False # TODO: implement your test here

    def test_validate(self):
        # page = Page()
        # self.assertEqual(expected, page.validate())
        assert False # TODO: implement your test here

class TestPageTimings(unittest.TestCase):
    def test___repr__(self):
        # page_timings = PageTimings()
        # self.assertEqual(expected, page_timings.__repr__())
        assert False # TODO: implement your test here

    def test_validate(self):
        # page_timings = PageTimings()
        # self.assertEqual(expected, page_timings.validate())
        assert False # TODO: implement your test here

class TestEntry(unittest.TestCase):
    def test___repr__(self):
        # entry = Entry()
        # self.assertEqual(expected, entry.__repr__())
        assert False # TODO: implement your test here

    def test_validate(self):
        # entry = Entry()
        # self.assertEqual(expected, entry.validate())
        assert False # TODO: implement your test here

class TestRequest(unittest.TestCase):
    def test___repr__(self):
        # request = Request()
        # self.assertEqual(expected, request.__repr__())
        assert False # TODO: implement your test here

    def test_devour(self):
        # request = Request()
        # self.assertEqual(expected, request.devour(req, proto, comment, keep_b64_raw))
        assert False # TODO: implement your test here

    def test_puke(self):
        # request = Request()
        # self.assertEqual(expected, request.puke())
        assert False # TODO: implement your test here

    def test_render(self):
        # request = Request()
        # self.assertEqual(expected, request.render())
        assert False # TODO: implement your test here

    def test_set_defaults(self):
        # request = Request()
        # self.assertEqual(expected, request.set_defaults())
        assert False # TODO: implement your test here

    def test_set_header(self):
        # request = Request()
        # self.assertEqual(expected, request.set_header(name, value))
        assert False # TODO: implement your test here

    def test_validate(self):
        # request = Request()
        # self.assertEqual(expected, request.validate())
        assert False # TODO: implement your test here

class TestResponse(unittest.TestCase):
    def test___repr__(self):
        # response = Response()
        # self.assertEqual(expected, response.__repr__())
        assert False # TODO: implement your test here

    def test_devour(self):
        # response = Response()
        # self.assertEqual(expected, response.devour(res, proto, comment, keep_b64_raw))
        assert False # TODO: implement your test here

    def test_puke(self):
        # response = Response()
        # self.assertEqual(expected, response.puke())
        assert False # TODO: implement your test here

    def test_render(self):
        # response = Response()
        # self.assertEqual(expected, response.render())
        assert False # TODO: implement your test here

    def test_validate(self):
        # response = Response()
        # self.assertEqual(expected, response.validate())
        assert False # TODO: implement your test here

class TestCookie(unittest.TestCase):
    def test___repr__(self):
        # cookie = Cookie()
        # self.assertEqual(expected, cookie.__repr__())
        assert False # TODO: implement your test here

    def test_devour(self):
        # cookie = Cookie()
        # self.assertEqual(expected, cookie.devour(cookie_string))
        assert False # TODO: implement your test here

    def test_validate(self):
        # cookie = Cookie()
        # self.assertEqual(expected, cookie.validate())
        assert False # TODO: implement your test here

class TestPostData(unittest.TestCase):
    def test_validate(self):
        # post_data = PostData()
        # self.assertEqual(expected, post_data.validate())
        assert False # TODO: implement your test here

class TestParam(unittest.TestCase):
    def test___repr__(self):
        # param = Param()
        # self.assertEqual(expected, param.__repr__())
        assert False # TODO: implement your test here

    def test_validate(self):
        # param = Param()
        # self.assertEqual(expected, param.validate())
        assert False # TODO: implement your test here

class TestContent(unittest.TestCase):
    def test___repr__(self):
        # content = Content()
        # self.assertEqual(expected, content.__repr__())
        assert False # TODO: implement your test here

    def test_validate(self):
        # content = Content()
        # self.assertEqual(expected, content.validate())
        assert False # TODO: implement your test here

class TestCache(unittest.TestCase):
    def test___repr__(self):
        # cache = Cache()
        # self.assertEqual(expected, cache.__repr__())
        assert False # TODO: implement your test here

    def test_validate(self):
        # cache = Cache()
        # self.assertEqual(expected, cache.validate())
        assert False # TODO: implement your test here

class TestRequestCache(unittest.TestCase):
    def test_validate(self):
        # request_cache = RequestCache()
        # self.assertEqual(expected, request_cache.validate())
        assert False # TODO: implement your test here

class TestTimings(unittest.TestCase):
    def test___repr__(self):
        # timings = Timings()
        # self.assertEqual(expected, timings.__repr__())
        assert False # TODO: implement your test here

    def test_validate(self):
        # timings = Timings()
        # self.assertEqual(expected, timings.validate())
        assert False # TODO: implement your test here

class TestTest(unittest.TestCase):
    def test_test(self):
        # self.assertEqual(expected, test())
        assert False # TODO: implement your test here

class TestUsage(unittest.TestCase):
    def test_usage(self):
        # self.assertEqual(expected, usage())
        assert False # TODO: implement your test here

if __name__ == '__main__':
    unittest.main()
