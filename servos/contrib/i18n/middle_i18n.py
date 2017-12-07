# -*- coding: utf-8 -*-
import re

from servos import Middleware
from servos.i18n import set_language


def get_language_from_request(request, settings):
    # 语言参数名称
    request_lang_key = settings.get_var('I18N/REQUEST_LANG_KEY')
    if request_lang_key:
        lang = request.get(request_lang_key)
        if lang:
            return lang

    # 默认语言
    return settings.I18N.get('LANGUAGE_CODE')


class I18nMiddle(Middleware):

    def process_request(self, request):
        lang = get_language_from_request(request, self.settings)
        if lang:
            set_language(lang)
