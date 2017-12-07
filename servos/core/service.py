# -*- coding: utf-8 -*-
import signal
import os
import inspect
import logging
from oslo_service import threadgroup, systemd
from oslo_service.service import ServiceBase as OsloServiceBase
from oslo_service.service import Launcher, SignalHandler, SignalExit, Services
from oslo_service.service import _is_sighup_and_daemon
from servos import dispatch

logger = logging.getLogger('servos.core.service')

# 保存实例化的服务对象
__services__ = []


def _check_service_base(service):
    if not isinstance(service, ServiceBase):
        raise TypeError("Service %(service)s must an instance of %(base)s!"
                        % {'service': service, 'base': ServiceBase})


class ServiceBase(OsloServiceBase):
    """Service object for binaries running on hosts."""

    def __init__(self, threads=1000):
        self.tg = threadgroup.ThreadGroup(threads)

    def reset(self):
        """Reset a service in case it received a SIGHUP."""

    def start(self):
        """Start a service."""

    def stop(self, graceful=False):
        """Stop a service.

        :param graceful: indicates whether to wait for all threads to finish
               or terminate them instantly
        """
        self.tg.stop(graceful)

    def wait(self):
        """Wait for a service to shut down."""
        self.tg.wait()


class ServiceLauncher(Launcher):
    """Runs one or more service in a parent process."""

    def __init__(self, conf):
        """Constructor.
        """
        self.conf = conf
        self.services = Services()
#         self.backdoor_port = (
#             eventlet_backdoor.initialize_if_enabled(self.conf))
        self.signal_handler = SignalHandler()

    def launch_service(self, service, workers=1):
        """Load and start the given service.

        :param service: The service you would like to start, must be an
                        instance of :class:`servos.core.service.ServiceBase`
        :param workers: This param makes this method compatible with
                        ProcessLauncher.launch_service. It must be None, 1 or
                        omitted.
        :returns: None

        """
        if workers is not None and workers != 1:
            raise ValueError("Launcher asked to start multiple workers")
        _check_service_base(service)
        self.services.add(service)

    def stop(self):
        """Stop all services which are currently running.
        """
        self.services.stop()

    def restart(self):
        """restart service.
        """
        self.services.restart()

    def _graceful_shutdown(self, *args):
        self.signal_handler.clear()
        if (self.conf.graceful_shutdown_timeout and
                self.signal_handler.is_signal_supported('SIGALRM')):
            signal.alarm(self.conf.graceful_shutdown_timeout)
        self.stop()

    def _reload_service(self, *args):
        self.signal_handler.clear()
        raise SignalExit(signal.SIGHUP)

    def _fast_exit(self, *args):
        logger.info('Caught SIGINT signal, instantaneous exiting')
        os._exit(1)

    def _on_timeout_exit(self, *args):
        logger.info('Graceful shutdown timeout exceeded, '
                    'instantaneous exiting')
        os._exit(1)

    def handle_signal(self):
        """Set self._handle_signal as a signal handler."""
        self.signal_handler.add_handler('SIGTERM', self._graceful_shutdown)
        self.signal_handler.add_handler('SIGINT', self._fast_exit)
        self.signal_handler.add_handler('SIGHUP', self._reload_service)
        self.signal_handler.add_handler('SIGALRM', self._on_timeout_exit)

    def _wait_for_exit_or_signal(self):
        status = None
        signo = 0

        try:
            super(ServiceLauncher, self).wait()
        except SignalExit as exc:
            signame = self.signal_handler.signals_to_name[exc.signo]
            logger.info('Caught %s, exiting', signame)
            status = exc.code
            signo = exc.signo
        except SystemExit as exc:
            self.stop()
            status = exc.code
        except Exception:
            self.stop()
        return status, signo

    def wait(self):
        """Wait for a service to terminate and restart it on SIGHUP.

        :returns: termination status
        """
        systemd.notify_once()
        self.signal_handler.clear()
        while True:
            self.handle_signal()
            status, signo = self._wait_for_exit_or_signal()
            if not _is_sighup_and_daemon(signo):
                break
            self.restart()

        super(ServiceLauncher, self).wait()
        return status


def entry(name=None, * params, **kparams):
    '''
    服务入口装饰器
    args：
        name:服务别名
    '''
    global __services__

    def _init(cls, * args, **kwargs):
        if not callable(cls):
            raise Exception("entry should be callable")

        if inspect.isclass(cls):
            _name = name or cls._service_name or cls.__name__

        cls._service_name = _name
        __services__.append(cls())

        return cls

    return _init


class AccessPolicy(object):
    """权限检查。默认以下划线（ _ ）开始的函数不对外暴露。
    """

    def is_allowed(self, endpoint, method):
        # 加入扩展点，可以对权限检查进行扩展
        re = dispatch.get(self, 'access_policy_check', endpoint, method)
        if re == dispatch.NoneValue:
            return re
        else:
            return not method.startswith('_')
