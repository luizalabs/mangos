
from __future__ import absolute_import

import re
import codecs
import os

from tornado.testing import AsyncTestCase
from braspag import BraspagRequest
from .asyncreplay import asyncreplay


MERCHANT_ID = os.environ.get('BRASPAG_MERCHANT_ID', '')
MERCHANT_KEY = os.environ.get('BRASPAG_MERCHANT_KEY', '')
HOMOLOGATION = True


class BraspagTestCase(AsyncTestCase):

    def setUp(self):
        super(BraspagTestCase, self).setUp()
        self.braspag = BraspagRequest(MERCHANT_ID, MERCHANT_KEY, homologation=HOMOLOGATION)

    def _test_name_for_replay_file(self):
        return self.__str__().split(' ')[0]

    def _replay_file_name(self):
        return os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                'recorded',
                self.__class__.__name__,
                "{0}.json".format(self._test_name_for_replay_file())
            )
        )

    def replay(self):
        return asyncreplay(self._replay_file_name())


class RegexpMatcher(object):
    def __init__(self, data_filepath):
        with codecs.open(data_filepath, 'rb', encoding='utf-8') as data_file:
            self.data = data_file.read().strip()

    def __eq__(self, other):
        if not isinstance(other, basestring):
            return False

        if not re.match(self.data, other):
            return False

        return True

    def __unicode__(self):
        return self.data

    def __repr__(self):
        return repr(unicode(self))
