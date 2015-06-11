# -*- coding: utf8 -*-

from __future__ import absolute_import

from .base import BraspagTestCase
from tornado.testing import gen_test
from tornado.httpclient import HTTPError


REQUEST_ID = '782a56e2-2dae-11e2-b3ee-080027d29772'


class GetTransactionDataTest(BraspagTestCase):
    @gen_test
    def test_get_transaction_data_without_transaction_id(self):
        with self.assertRaises(AssertionError):
            response = yield self.braspag.get_transaction_data(
                transaction_id='',
                request_id=REQUEST_ID
            )

    @gen_test
    def test_get_transaction_data_not_found(self):
        with self.assertRaises(HTTPError):
            response = yield self.braspag.get_transaction_data(
                transaction_id='782a56e2-2dae-11e2-b3ee-080027d29772',
                request_id=REQUEST_ID
            )

    @gen_test
    def test_get_transaction_data(self):
        response = yield self.braspag.get_transaction_data(
            transaction_id=u'abec4ae4-3315-45af-9111-ac1eecf7548b',
            request_id=REQUEST_ID
        )

        self.assertTrue(response)
        self.assertEquals(response['Customer']['Identity'], u'12345678900')
        self.assertEquals(response['Customer']['Email'], u'jose123@dasilva.com.br')
        self.assertEquals(response['Payment']['Status'], 1)
        self.assertEquals(response['Payment']['Provider'], u'Simulado')
        self.assertEquals(response['Payment']['Country'], u'BRA')
        self.assertEquals(response['Payment']['CreditCard']['Brand'], u'Undefined')
        self.assertEquals(response['Payment']['CreditCard']['CardNumber'], u'000000******0001')
        self.assertEquals(response['Payment']['CreditCard']['Holder'], u'Jose da Silva')
        self.assertEquals(response['Payment']['CreditCard']['ExpirationDate'], u'05/2018')

