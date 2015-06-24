# -*- encoding: utf-8 -*-
import six
import string


def is_valid_guid(guid):
    VALID_CHARS = string.hexdigits + '-'
    VALID_PARTS_LEN = [8, 4, 4, 4, 12]

    if not isinstance(guid, six.string_types):
        guid = unicode(guid)

    if not all(c in VALID_CHARS for c in guid):
        return False

    guid_parts_len = [len(part) for part in guid.split('-')]
    if guid_parts_len != VALID_PARTS_LEN:
        return False

    return True


def mask_credit_card_number(card):
    card = str(card)
    asterisks = len(card) - 10
    return u'{0}{1}{2}'.format(card[:6], '*' * asterisks, card[-4:])
