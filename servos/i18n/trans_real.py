# -*- coding: utf-8 -*-
import os

from servos import application
from servos import get_service_dir
from servos import settings
from servos.utils.common import pkg, expand_path
from t2cloud.translation import TranslatorFactory

DEFAULT_LANGUAGE = settings.get_var('I18N/LANGUAGE_CODE', None)

path = pkg.resource_filename('servos', '')
localedir = (
    # 各服务路径
    [get_service_dir(service_name) for service_name in application.services] +
    # 框架路径
    [path]
)

tf = TranslatorFactory(localedir)

if DEFAULT_LANGUAGE:
    tf.activate(DEFAULT_LANGUAGE)


def set_language(lang):
    tf.activate(lang)


def get_language():
    tf.get_current_language()


def gettext(message):
    return tf._do_translate(message, 'gettext')


def ugettext(message):
    return tf._do_translate(message, 'ugettext')


def pgettext(context, message):
    return tf._pgettext(context, message)
