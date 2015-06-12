# -*- coding: utf8 -*-

from __future__ import absolute_import

from .base import BraspagTestCase
from tornado.testing import gen_test
from tornado.httpclient import HTTPError


REQUEST_ID = u'782a56e2-2dae-11e2-b3ee-080027d29772'


class GetTransactionDataTest(BraspagTestCase):
    @gen_test
    def test_get_transaction_data_without_transaction_id(self):
        with self.assertRaises(AssertionError):
            yield self.braspag.get_transaction_data(
                transaction_id='',
                request_id=REQUEST_ID
            )

    @gen_test
    def test_get_transaction_data_not_found(self):
        with self.assertRaises(HTTPError):
            yield self.braspag.get_transaction_data(
                transaction_id='782a56e2-2dae-11e2-b3ee-080027d29772',
                request_id=REQUEST_ID
            )

    @gen_test
    def test_get_transaction_data(self):
        response = yield self.braspag.get_transaction_data(
            transaction_id=u'abec4ae4-3315-45af-9111-ac1eecf7548b',
            request_id=REQUEST_ID
        )

        transaction = response['transaction']

        self.assertTrue(response['success'])
        self.assertEquals(transaction['status'], 1)
        self.assertEquals(transaction['payment_method'], u'Simulado')
        self.assertEquals(transaction['country'], u'BRA')
        self.assertEquals(transaction['payment_method_name'], u'Undefined')
        self.assertEquals(transaction['holder_name'], u'Jose da Silva')
        self.assertEquals(transaction['expiration_date'], u'05/2018')
        self.assertEquals(
            transaction['masked_credit_card_number'],
            u'000000******0001'
        )
