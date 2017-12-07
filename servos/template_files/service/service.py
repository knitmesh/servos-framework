# -*- coding: utf-8 -*-
import logging

from servos import ServiceBase, entry, settings
logger = logging.getLogger(__name__)


@entry()
class DemoService(ServiceBase):
    _service_name = 'demoservice'

    def start(self):
        logger.info('starting %s service' % self._service_name)
        super(DemoService, self).start()
        logger.info('%s service started' % self._service_name)

    def stop(self):
        logger.info('stoping %s service' % self._service_name)
        super(DemoService, self).stop()
        logger.info('%s service stoped' % self._service_name)
