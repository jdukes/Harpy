#!/usr/bin/env python

from har import Request

req = Request('{"cookies": [], "url": "http://www.google.com/", "queryString": [], "headers": [{"name": "Accept", "value": "application/x-ms-application, image/jpeg, application/xaml+xml, image/gif, image/pjpeg, application/x-ms-xbap, application/x-shockwave-flash, application/msword, */*"}, {"name": "Accept-Language", "value": "en-US"}, {"name": "Accept-Encoding", "value": "gzip, deflate"}, {"name": "User-Agent", "value": "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; GomezAgent 3.0)"}], "headersSize": 335, "bodySize": -1, "method": "GET", "httpVersion": "HTTP/1.1"}')

print req
