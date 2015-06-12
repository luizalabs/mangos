# -*- encoding: utf-8 -*-

from tornado.httpclient import HTTPError


class BraspagException(Exception):
    """
    Custom exception for Braspag Errors
    """
    def __init__(self, response):
        self.response = response    


class HTTPTimeoutError(HTTPError):
    """
    Timeout Exception
    """
    pass
