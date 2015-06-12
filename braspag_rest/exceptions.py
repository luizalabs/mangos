# -*- encoding: utf-8 -*-

from tornado.httpclient import HTTPError


class BraspagException(Exception):
    """
    Custom exception
    """
    pass


class HTTPTimeoutError(HTTPError):
    """
    Timeout Exception
    """
    pass
