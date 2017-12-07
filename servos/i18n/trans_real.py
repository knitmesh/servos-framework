# -*- coding: utf-8 -*-
from servos import application
from servos import get_service_dir
from servos import settings
from servos.utils.common import pkg

DEFAULT_LANGUAGE = settings.get_var('I18N/LANGUAGE_CODE', None)

path = pkg.resource_filename('servos', '')
localedir = (
    # 各服务路径
    [get_service_dir(service_name) for service_name in application.services] +
    # 框架路径
    [path]
)