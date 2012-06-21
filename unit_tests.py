#!/usr/bin/env python
"""This module sets up unit tests for harpy.

"""

import har
import unittest


################################################################################
# Functional Tests
################################################################################
    

class EncoderTests(unittest.TestCase):

    def test_encode_har_object(self):
        assert False, "Not Implemented"

    def test_encode_date(self):
        #localization is not clear in spec
        assert False, "Not Implemented"

    def test_handle_invalid_date(self):
        #format is not clear enough
        assert False, "Not Implemented"


class InstantiationTests(unittest.TestCase):

    def test_MetaHar(self):
        """Should not ever instantiate.
        """
        with self.assertRaises(AssertionError):
            har._MetaHar()

    def test_KeyValueHar(self):
        """Should not ever instantiate.
        """
        with self.assertRaises(AssertionError):
            har._KeyValueHar()

    def test_HarContainer(self):
        hc = har.HarContainer()

class ValidatationTests(unittest.TestCase):

    #finish...
    def test_MissingValueException(self):
        assert False, "Not Implemented"

    def test_ValidataionError(self):
        assert False, "Not Implemented"


class SerializationTests(unittest.TestCase):

    def test_raw_request(self):
        assert False, "Not Implemented"

    def test_raw_response(self):
        assert False, "Not Implemented"

    def test_json_request(self):
        assert False, "Not Implemented"

    def test_json_response(self):
        assert False, "Not Implemented"
    

if __name__ == '__main__':
    unittest.main()
