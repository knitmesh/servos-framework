# -*- coding: utf-8 -*-
__all__ = [
    'ServiceBase',
    'entry',
    'ServosError',
    'functions',
    'settings',
    'application',
    'Middleware',
    'dispatch',
    'version',
    'get_services',
    'get_service_dir',
]
version = '0.0.1'

import sys
reload(sys)
sys.setdefaultencoding('utf-8')  #@UndefinedVariable

import eventlet
eventlet.monkey_patch()


class ServosError(Exception):
    pass


class Middleware(object):
    ORDER = 500

    def __init__(self, application, settings):
        self.application = application
        self.settings = settings

import servos.core.dispatch as dispatch
from servos.core.service import ServiceBase
from servos.core.service import entry
from servos.core.simpleframe import (
    functions, settings, application, get_service_dir, get_services)
