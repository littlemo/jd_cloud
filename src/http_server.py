# -*- coding: utf-8 -*-

__author__ = 'Moore.Huang'

import httplib
import json
import time


class HTTPServer():
    def __init__(self, address=('apismart.jd.com', httplib.HTTPS_PORT)):
        self.host, self.port = address
        self.__conn = None

    TIME_FORMAT = '%Y-%m-%dT%H:%M:%S+0800'
    H_HOST = 'Host'
    H_KEY = 'JD-Key'
    H_CODE_KEY = 'code'
    B_DEVICE_ID = 'device_id'
    B_PRODUCT_ID = 'product_id'

    def __connect_https(self):
        if self.__conn is not None:
            self.disconnect_https()
        self.__conn = httplib.HTTPSConnection(self.host, self.port)

    def disconnect_https(self):
        if self.__conn is None:
            print 'Err: conn is None!'
            return False
        self.__conn.close()
        self.__conn = None
        return True

    def get_headers(self, host, key):
        return {self.H_HOST: host, self.H_KEY: key}

    def run_https_req(self, method, url, headers, body=None):
        if headers is None:
            print 'Err: headers is None!'
            return None

        self.__connect_https()
        if self.__conn is None:
            print 'Err: create __conn failed!'
            return None

        try:
            self.__conn.request(method, url, headers=headers, body=json.dumps(body))
        except KeyError:
            print 'Err: json.dumps |', body
            return False
        except httplib.CannotSendRequest, e:
            print 'Err: CannotSendRequest |', e
            return False
        return True

    def get_response(self):
        if self.__conn is None:
            print 'Err: __conn is None!'
            return None

        try:
            res = self.__conn.getresponse()
        except httplib.BadStatusLine:
            print 'Err: https recv package!'
            return None

        if res.status != httplib.OK:
            print 'Err: HTTPS response.status [%s]' % res.status
            self.disconnect_https()
            return None
        return res

    def get_time_str(self):
        return time.strftime(self.TIME_FORMAT, time.localtime())