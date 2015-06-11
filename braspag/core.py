# -*- encoding: utf-8 -*-

from __future__ import absolute_import

import json
import uuid
import logging
import urlparse

from .utils import is_valid_guid
from .exceptions import BraspagException
from .exceptions import HTTPTimeoutError

from tornado.httpclient import HTTPRequest
from tornado.httpclient import HTTPError
from tornado import httpclient
from tornado import gen


class BaseRequest(object):
    def __init__(self, merchant_id=None, merchant_key=None, homologation=False, request_timeout=10):
        self.merchant_id = merchant_id
        self.merchant_key = merchant_key

        self.log = logging.getLogger('braspag')
        self.http_client = httpclient.AsyncHTTPClient()

        # timeout
        self.request_timeout = request_timeout

    def headers(self, request_id):
        """default headers to be sent on http requests"""
        return {
            "Content-Type": "application/json",
            "MerchantId": self.merchant_id,
            "MerchantKey": self.merchant_key,
            "RequestId": request_id or unicode(uuid.uuid4())
        }

    def ensure_json(self, payload):
        if not payload:
            return None 

        if isinstance(payload, str):
            return payload

        return json.dumps(payload)

    def _get_url(self, url, resource):
        """Return the full URL for a given resource
        """
        return urlparse.urljoin(url, resource)

    def _get_request(self, url, method, payload, **kwargs):
        """Return an instance of HTTPRequest with optionally custom headers.
        The body is automatically encoded to json if it's not already.
        """
        headers = kwargs.get('headers') or self.headers(kwargs.get('request_id'))

        return HTTPRequest(
            url=url,
            method=method,
            body=self.ensure_json(payload),
            request_timeout=self.request_timeout,
            headers=headers
        )

    @gen.coroutine
    def fetch(self, url, method, payload, **kwargs):
        self.log.warning('Request: %s' % payload)
        try:
            response = yield self.http_client.fetch(self._get_request(url, method, payload, **kwargs))
        except HTTPError as e:
            self.log.error('No response received.')
            raise e.code == 599 and HTTPTimeoutError(e.code, e.message) or HTTPError(e.code, e.message)

        self.log.warning('Response code: %s body: %s' % (response.code, response.body))
        raise gen.Return(response)


class BraspagRequest(BaseRequest):
    """
    Implements Braspag Pagador REST API.
    DOCS: http://apidocs.braspag.com.br
    """

    def __init__(self, merchant_id=None, merchant_key=None, homologation=False, request_timeout=10):
        super(BraspagRequest, self).__init__(merchant_id, merchant_key, request_timeout)
        if homologation:
            self.query_url = 'https://apiqueryhomolog.braspag.com.br'
            self.transaction_url = 'https://apihomolog.braspag.com.br'
        else:
            # pragma: no cover
            self.query_url = 'https://apiquery.braspag.com.br'
            self.transaction_url = 'https://api.braspag.com.br'

    @gen.coroutine
    def _request(self, resource, method, payload, **kwargs):
        """Make the http request to Braspag.
        """
        url = self.transaction_url
        if kwargs.get('query'):
            url = self.query_url
        url = self._get_url(url, resource)

        response = yield self.fetch(url, method, payload, **kwargs)
        raise gen.Return(json.loads(response.body))

    @gen.coroutine
    def get_transaction_data(self, **kwargs):
        """Get the data from a transaction.

        The arguments to be sent to the Braspag REST API must be passed
        as keyword arguments and are:

        :arg transaction_id: The id of the transaction
        """
        assert is_valid_guid(kwargs.get('transaction_id')), 'Invalid Transaction ID'

        resource = '/v2/sales/{0}'.format(kwargs.get('transaction_id', ''))

        response = yield self._request(resource, 'GET', kwargs.get('payload'), query=True, **kwargs)
        raise gen.Return(response)
