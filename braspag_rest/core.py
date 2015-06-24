# -*- encoding: utf-8 -*-

from __future__ import absolute_import

import json
import uuid
import logging

import six

try:
    import urlparse
except ImportError:
    from urllib.parse import urlparse, urljoin

from datetime import datetime

from .utils import is_valid_guid
from .exceptions import BraspagException
from .exceptions import HTTPTimeoutError

from tornado.httpclient import HTTPRequest
from tornado.httpclient import HTTPError
from tornado import httpclient
from tornado import gen


class BaseRequest(object):
    def __init__(self, merchant_id=None, merchant_key=None, homologation=False,
                 request_timeout=10):
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
        """
        Return the full URL for a given resource
        """
        if six.PY2:
            return urlparse.urljoin(url, resource)
        else:
            return urljoin(url, resource)

    def _get_request(self, url, method, payload, **kwargs):
        """Return an instance of HTTPRequest with optionally custom headers.
        The body is automatically encoded to json if it's not already.
        """
        headers = kwargs.get('headers') or self.headers(
            kwargs.get('request_id')
        )

        return HTTPRequest(
            url=url,
            method=method,
            body=self.ensure_json(payload),
            request_timeout=self.request_timeout,
            headers=headers
        )

    def format_errors(self, errors):
        errors = [{
            'code': e['Code'],
            'message': e['Message']
        } for e in errors]

        return {
            'success': False,
            'errors': errors
        }

    @gen.coroutine
    def fetch(self, url, method, payload, **kwargs):
        self.log.warning('Request: %s' % payload)
        try:
            response = yield self.http_client.fetch(
                self._get_request(url, method, payload, **kwargs)
            )
        except HTTPError as e:
            if e.code == 599:
                raise HTTPTimeoutError(e.code, e.message)
            if e.code == 400:
                raise BraspagException(e.response)

            raise

        self.log.warning(
            'Response code: {} body: {}'.format(
                response.code, response.body
            )
        )
        raise gen.Return(response)


class BraspagRequest(BaseRequest):
    """
    Implements Braspag Pagador REST API.
    DOCS: http://apidocs.braspag.com.br
    """

    def __init__(self, merchant_id=None, merchant_key=None, homologation=False,
                 request_timeout=10):
        super(BraspagRequest, self).__init__(merchant_id, merchant_key,
                                             request_timeout)
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
        if six.PY2:
            raise gen.Return(json.loads(response.body))
        else:
            raise gen.Return(json.loads(response.body.decode()))

    @gen.coroutine
    def get_transaction_data(self, **kwargs):
        """Get the data from a transaction.

        The arguments to be sent to the Braspag REST API must be passed
        as keyword arguments and are:

        :arg transaction_id: The id of the transaction
        """
        trasaction_id = kwargs.get('transaction_id')
        assert is_valid_guid(trasaction_id), 'Invalid Transaction ID'

        resource = '/v2/sales/{0}'.format(kwargs.get('transaction_id', ''))

        try:
            response = yield self._request(
                resource,
                'GET',
                kwargs.get('payload'),
                query=True,
                **kwargs
            )
        except BraspagException as e:
            error_body = json.loads(e.response.body)
            raise gen.Return(self.format_errors(error_body))

        response = BraspagResponse.format_get_transaction_data(response)
        raise gen.Return(response)


class BraspagResponse(object):
    @classmethod
    def format_transactions(cls, braspag_transactions):
        transactions = []

        if not isinstance(braspag_transactions, list):
            braspag_transactions = [braspag_transactions]

        for transaction in braspag_transactions:
            data = {
                'status': int(transaction.get('Status')),
                'braspag_transaction_id': transaction.get('PaymentId'),
                'acquirer_transaction_id': transaction.get(
                    'AcquirerTransactionId'
                ),
                'authorization_code': transaction.get('AuthorizationCode'),
                'proof_of_sale': transaction.get('ProofOfSale'),
            }

            credit_card = transaction.get('CreditCard', {})

            if 'Amount' in transaction:
                data['amount'] = int(transaction.get('Amount'))

            if 'VoidedAmount' in transaction:
                data['voided_amount'] = int(transaction.get('VoidedAmount'))

            if 'CardNumber' in credit_card:
                data['masked_credit_card_number'] = credit_card.get(
                    'CardNumber'
                )

            if 'Brand' in credit_card:
                data['payment_method_name'] = credit_card.get('Brand')

            if 'Holder' in credit_card:
                data['holder_name'] = credit_card.get('Holder')

            if 'ExpirationDate' in credit_card:
                data['expiration_date'] = credit_card.get('ExpirationDate')

            if 'ReturnCode' in transaction:
                data['return_code'] = transaction.get('ReturnCode')

            if 'ReturnMessage' in transaction:
                data['return_message'] = transaction.get('ReturnMessage')

            if 'Provider' in transaction:
                data['payment_method'] = transaction.get('Provider')

            if 'Capture' in transaction:
                data['capture'] = transaction.get('Capture')

            if 'Authenticate' in transaction:
                data['autenticate'] = transaction.get('Authenticate')

            if 'Type' in transaction:
                data['transaction_type'] = transaction.get('Type')

            if 'Installments' in transaction:
                data['installments'] = int(transaction.get('Installments'))

            if 'Country' in transaction:
                data['country'] = transaction.get('Country')

            if 'ServiceTaxAmount' in transaction:
                data['service_tax_amount'] = int(
                    transaction.get('ServiceTaxAmount')
                )

            if 'ReceivedDate' in transaction:
                data['received_date'] = datetime.strptime(
                    transaction.get('ReceivedDate'), '%Y-%m-%d %H:%M:%S'
                )

            if 'Interest' in transaction:
                data['interest'] = transaction.get('Interest')

            if 'ReasonCode' in transaction:
                data['reason_code'] = transaction.get('ReasonCode')

            if 'ReasonMessage' in transaction:
                data['reason_message'] = transaction.get('ReasonMessage')

            if 'ProviderReturnCode' in transaction:
                data['acquirer_return_code'] = transaction.get(
                    'ProviderReturnCode'
                )

            if 'ProviderReturnMessage' in transaction:
                data['acquirer_return_message'] = transaction.get(
                    'ProviderReturnMessage'
                )

            transactions.append(data)

        return transactions

    @classmethod
    def format_get_transaction_data(cls, response):
        data = {
            'success': True,
            'order_id': response.get('MerchantOrderId'),
        }

        data['transaction'] = cls.format_transactions(
            response.get('Payment')
        )[0]
        return data
