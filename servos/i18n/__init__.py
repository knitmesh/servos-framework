# -*- coding: utf-8 -*-
__all__ = ['set_language', 'get_language',
           'gettext_lazy', 'ugettext_lazy', 'pgettext_lazy',
           'gettext', 'ugettext', 'pgettext']

import sys
import py
import six
from t2cloud.translation import TranslatorFactory
from t2cloud.translation._lazy import lazy


class Trans(object):

    def __getattr__(self, real_name):
        from servos import settings
        if settings.USE_I18N:
            from servos.i18n import trans_real as trans
        else:
            from servos.i18n import trans_null as trans
        setattr(self, real_name, getattr(trans, real_name))
        return getattr(trans, real_name)

_trans = Trans()

# The Trans class is no more needed, so remove it from the namespace.
del Trans


def set_language(lang):
    _trans.set_language(lang)


def get_language():
    _trans.get_language()


def gettext(message):
    return _trans.gettext(message)


def ugettext(message):
    return _trans.ugettext(message)


def pgettext(context, message):
    return _trans.pgettext(context, message)

gettext_lazy = lazy(gettext, str)
ugettext_lazy = lazy(ugettext, six.text_type)
pgettext_lazy = lazy(pgettext, six.text_type)
