# -*- coding: utf-8 -*-
from servos import settings
import six


def force_text(s, encoding='utf-8', strings_only=False, errors='strict'):
    #     return six.text_type(s)
    if isinstance(s, six.text_type):
        return s
    try:
        if not isinstance(s, six.string_types):
            if hasattr(s, '__unicode__'):
                s = six.text_type(s)
            else:
                s = six.text_type(bytes(s), encoding, errors)
        else:
            # Note: We use .decode() here, instead of six.text_type(s, encoding,
            # errors), so that if s is a SafeBytes, it ends up being a
            # SafeText at the end.
            s = s.decode(encoding, errors)
    except UnicodeDecodeError as e:
        if not isinstance(s, Exception):
            raise e
        else:
            # If we get to here, the caller has passed in an Exception
            # subclass populated with non-ASCII bytestring data without a
            # working unicode method. Try to handle this without raising a
            # further exception by individually forcing the exception args
            # to unicode.
            s = ' '.join(force_text(arg, encoding, strings_only, errors)
                         for arg in s)
    return s


set_language = lambda x: None
get_language = lambda: None


def gettext(message):
    return message


def ugettext(message):
    return force_text(gettext(message))


def pgettext(context, message):
    return ugettext(message)
