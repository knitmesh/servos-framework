# -*- coding: utf-8 -*-
import os
import sys
import logging
import t2cloud.pyini as pyini

import servos.core.dispatch as dispatch
import servos.core.service as service
from servos.utils.localproxy import LocalProxy, Global
from servos.utils.common import pkg, log, import_attr, myimport, norm_path
from servos import ServosError


__service_dirs__ = {}

__global__ = Global()
__global__.settings = pyini.Ini(lazy=True)


class NoSuchMethod(ServosError, AttributeError):
    "Raised if there is no endpoint which exposes the requested method."

    def __init__(self, service, method):
        msg = "Endpoint does not support  method %s" % method
        super(NoSuchMethod, self).__init__(msg)
        self.service = service
        self.method = method


class Finder(object):

    def __init__(self, section):
        self.__objects = {}
        self.__section = section

    def __contains__(self, name):
        if name in self.__objects:
            return True
        if name not in settings[self.__section]:
            return False
        else:
            return True

    def __getattr__(self, name):
        if name in self.__objects:
            return self.__objects[name]
        if name not in settings[self.__section]:
            raise ServosError("Object %s is not existed!" % name)
        obj = import_attr(settings[self.__section].get(name))
        self.__objects[name] = obj
        return obj

    def __setitem__(self, name, value):
        if isinstance(value, (str, unicode)):
            value = import_attr(value)
        self.__objects[name] = value

functions = Finder('FUNCTIONS')


def get_service_dir(service):
    """
    获取服务目录
    """
    path = __service_dirs__.get(service)
    if path is not None:
        return path
    else:
        p = service.split('.')
        try:
            path = pkg.resource_filename(p[0], '')
        except ImportError as e:
            log.error("Can't import service %s", p[0])
            log.exception(e)
            path = ''
        if len(p) > 1:
            path = os.path.join(path, *p[1:])

        __service_dirs__[service] = path
        return path


def get_service_depends(service, existed_services=None, installed_services=None):
    '''
    获取当前服务依赖的服务集合
    :param service:当前服务
    :param existed_services:已经收集过了
    :param installed_services:当前启动的服务
    '''
    installed_services = installed_services or []
    if existed_services is None:
        s = set()
    else:
        s = existed_services

    if service in s:
        raise StopIteration

    configfile = os.path.join(get_service_dir(service), 'settings.ini')
    if os.path.exists(configfile):
        x = pyini.Ini(configfile)
        # 读取配置中的依赖信息
        services = x.get_var('DEPENDS/REQUIRED_SERVICES', [])
        for i in services:
            if i not in s and i not in installed_services:
                # 递归查询
                for j in get_service_depends(i, s, installed_services):
                    yield j
    s.add(service)
    yield service


def get_services(services_dir,
                 settings_file='settings.ini',
                 local_settings_file='local_settings.ini'):
    '''
    收集服务信息
    :param services_dir:服务目录
    :param settings_file:配置文件
    :param local_settings_file:local配置文件
    '''
    inifile = norm_path(os.path.join(services_dir, settings_file))
    services = []
    visited = set()
    installed_services = []
    if not os.path.exists(services_dir):
        return services
    if os.path.exists(inifile):
        x = pyini.Ini(inifile)
        if x:
            installed_services.extend(x.GLOBAL.get('INSTALLED_SERVICES', []))

    local_inifile = norm_path(os.path.join(services_dir, local_settings_file))
    if os.path.exists(local_inifile):
        x = pyini.Ini(local_inifile)
        if x and x.get('GLOBAL'):
            installed_services.extend(x.GLOBAL.get('INSTALLED_SERVICES', []))

    for _service in installed_services:
        services.extend(
            list(get_service_depends(_service, visited, installed_services)))

    if not services and os.path.exists(services_dir):
        for p in os.listdir(services_dir):
            if os.path.isdir(os.path.join(services_dir, p)) and \
                    p not in ['.svn', 'CVS', '.git'] and \
                    not p.startswith('.') and \
                    not p.startswith('_'):
                services.append(p)

    return services


def collect_settings(services_dir, settings_file='settings.ini',
                     local_settings_file='local_settings.ini', default_settings=None):
    '''
    收集配置文件，命令行使用
    :param services_dir:
    :param settings_file:
    :param local_settings_file:
    :param default_settings:
    '''

    services = get_services(services_dir,
                            settings_file=settings_file,
                            local_settings_file=local_settings_file)
    settings_file = os.path.join(services_dir, settings_file)
    local_settings_file = os.path.join(services_dir, local_settings_file)
    settings = []
    default_settings_file = pkg.resource_filename(
        'servos.core', 'default_settings.ini')
    settings.insert(0, default_settings_file)
    for p in services:
        # deal with settings
        inifile = os.path.join(get_service_dir(p), 'settings.ini')
        if os.path.exists(inifile):
            settings.append(inifile)

    if os.path.exists(settings_file):
        settings.append(settings_file)

    if os.path.exists(local_settings_file):
        settings.append(local_settings_file)
    return settings


class Dispatcher(object):
    installed = False

    def __init__(self,
                 services_dir='services',
                 start=True,
                 default_settings=None,
                 settings_file='settings.ini',
                 local_settings_file='local_settings.ini'):

        __global__.application = self
        self.debug = False
        self.default_settings = default_settings or {}
        self.settings_file = settings_file
        self.local_settings_file = local_settings_file
        self.service_manager = service.ServiceLauncher(settings)
        self.access_policy = service.AccessPolicy()
        if not Dispatcher.installed:
            self.init(services_dir)
            dispatch.call(self, 'startup_installed')

        if start:
            dispatch.call(self, 'startup')
            self.service_manager.wait()

    def init(self, services_dir):
        Dispatcher.services_dir = norm_path(services_dir)
        # 处理获得所有需要的服务
        Dispatcher.services = get_services(self.services_dir,
                                           self.settings_file,
                                           self.local_settings_file)
        # 收集服务信息（服务和配置文件路径）
        Dispatcher.modules = self.collect_modules()

        # 收集配置信息
        self.install_settings(self.modules['settings'])

        # 安装全局对象
        self.install_global_objects()

        # 安装扩展调用
        self.install_binds()

        dispatch.call(self, 'after_init_settings')

        Dispatcher.settings = settings
        self.debug = settings.GLOBAL.get('DEBUG', False)

        # 设置日志
        self.set_log()

        # 安装服务
        self.init_services()
        self.install_services(self.modules['services'])

        dispatch.call(self, 'after_init_services')
        # 安装middleware
        Dispatcher.middlewares = self.install_middlewares()

        # 设置状态，服务安装完成
        Dispatcher.installed = True

    def set_log(self):

        s = self.settings

        def _get_level(level):
            return getattr(logging, level.upper())

        # get basic configuration
        config = {}
        for k, v in s.LOG.items():
            if k in ['format', 'datefmt', 'filename', 'filemode']:
                config[k] = v

        if s.get_var('LOG/level'):
            config['level'] = _get_level(s.get_var('LOG/level'))
        logging.basicConfig(**config)

        if config.get('filename'):
            Handler = 'logging.FileHandler'
            if config.get('filemode'):
                _args = (config.get('filename'), config.get('filemode'))
            else:
                _args = (config.get('filename'),)
        else:
            Handler = 'logging.StreamHandler'
            _args = ()

        # process formatters
        formatters = {}
        for f, v in s.get_var('LOG.Formatters', {}).items():
            formatters[f] = logging.Formatter(v)

        # process handlers
        handlers = {}
        for h, v in s.get_var('LOG.Handlers', {}).items():
            handler_cls = v.get('class', Handler)
            handler_args = v.get('args', _args)

            handler = import_attr(handler_cls)(*handler_args)
            if v.get('level'):
                handler.setLevel(_get_level(v.get('level')))

            format = v.get('format')
            if format in formatters:
                handler.setFormatter(formatters[format])
            elif format:
                fmt = logging.Formatter(format)
                handler.setFormatter(fmt)

            handlers[h] = handler

        # process loggers
        for logger_name, v in s.get_var('LOG.Loggers', {}).items():
            if logger_name == 'ROOT':
                log = logging.getLogger('')
            else:
                log = logging.getLogger(logger_name)

            if v.get('level'):
                log.setLevel(_get_level(v.get('level')))
            if 'propagate' in v:
                log.propagate = v.get('propagate')
            if 'handlers' in v:
                for h in v['handlers']:
                    if h in handlers:
                        log.addHandler(handlers[h])
                    else:
                        raise ServosError("Log Handler %s is not defined yet!")
            elif 'format' in v:
                if v['format'] not in formatters:
                    fmt = logging.Formatter(v['format'])
                else:
                    fmt = formatters[v['format']]
                _handler = import_attr(Handler)(*_args)
                _handler.setFormatter(fmt)
                log.addHandler(_handler)

    def collect_modules(self, check_service=True):
        '''
        收集服务信息
        :param check_service:
        '''
        modules = {}
        _services = set()
        _settings = []

        # 核心配置文件，最先加载
        inifile = pkg.resource_filename('servos.core', 'default_settings.ini')
        _settings.insert(0, inifile)

        def enum_services(service_path, service_name, subfolder=None, pattern=None):
            if not os.path.exists(service_path):
                log.error("Can't found the service %s path, "
                          "please check if the path is right",
                          service_name)
                return

            for f in os.listdir(service_path):
                fname, ext = os.path.splitext(f)
                if os.path.isfile(os.path.join(service_path, f)) and \
                        ext in ['.py', '.pyc', '.pyo'] and \
                        fname != '__init__':
                    if pattern:
                        import fnmatch
                        if not fnmatch.fnmatch(f, pattern):
                            continue
                    if subfolder:
                        _services.add(
                            '.'.join([service_name, subfolder, fname]))
                    else:
                        _services.add('.'.join([service_name, fname]))

        for p in self.services:
            path = get_service_dir(p)
            # deal with services
            if check_service:
                service_path = os.path.join(path, 'services')
                if os.path.exists(service_path) and os.path.isdir(service_path):
                    enum_services(service_path, p, 'services')
                else:
                    enum_services(path, p, pattern='service*')
            # deal with settings
            inifile = os.path.join(get_service_dir(p), 'settings.ini')

            if os.path.exists(inifile):
                _settings.append(inifile)

        set_ini = os.path.join(self.services_dir, self.settings_file)
        if os.path.exists(set_ini):
            _settings.append(set_ini)

        # local配置文件，最后被加载
        local_set_ini = os.path.join(
            self.services_dir, self.local_settings_file)
        if os.path.exists(local_set_ini):
            _settings.append(local_set_ini)

        modules['services'] = list(_services)
        modules['settings'] = _settings
        return modules

    def install_services(self, services):
        '''
        加载服务。加载具体服务类的文件
        :param services:
        '''
        for s in services:
            try:
                myimport(s)
            except Exception as e:
                log.exception(e)

        for _service in service.__services__:
            if isinstance(_service, service.ServiceBase):
                self.service_manager.launch_service(_service)
            else:
                pass

    def init_services(self):
        '''
        初始化加载服务。主要是执行__init__中代码
        '''
        for p in self.services:
            try:
                myimport(p)
            except ImportError, e:
                pass
            except BaseException, e:
                log.exception(e)

    def install_settings(self, s):
        '''
        加载配置信息。否遭settings对象
        :param s:
        '''
        for v in s:
            settings.read(v)
        settings.update(self.default_settings)
        settings.freeze()

        # process FILESYSTEM_ENCODING
        if not settings.GLOBAL.FILESYSTEM_ENCODING:
            settings.GLOBAL.FILESYSTEM_ENCODING = sys.getfilesystemencoding(
            ) or settings.GLOBAL.DEFAULT_ENCODING

    def install_global_objects(self):
        """
        根据[GLOBAL_OBJECTS]中的配置，向servos模块中注入对象。
        其他模块可以直接使用import来获取。例如：
        from servos import test_obj
        """
        import servos
        for k, v in settings.GLOBAL_OBJECTS.items():
            setattr(servos, k, import_attr(v))

    def install_binds(self):
        '''
        安装扩展。
        # process DISPATCH hooks
        # BINDS format
        # func = topic              #bind_name will be the same with function
        # bind_name = topic, func
        # bind_name = topic, func, {args}
        '''
        d = settings.get('BINDS', {})
        for bind_name, args in d.items():
            if not args:
                continue
            is_wrong = False
            if isinstance(args, (tuple, list)):
                if len(args) == 2:
                    dispatch.bind(args[0])(args[1])
                elif len(args) == 3:
                    if not isinstance(args[2], dict):
                        is_wrong = True
                    else:
                        dispatch.bind(args[0], **args[2])(args[1])
                else:
                    is_wrong = True
            elif isinstance(args, (str, unicode)):
                dispatch.bind(args)(bind_name)
            else:
                is_wrong = True
            if is_wrong:
                log.error(
                    'BINDS definition should be "function=topic" or '
                    '"bind_name=topic, function" or '
                    '"bind_name=topic, function, {"args":value1,...}"')
                raise ServosError(
                    'BINDS definition [%s=%r] is not right' % (bind_name, args))

    def install_middlewares(self):
        return self.sort_middlewares(settings.get('MIDDLEWARES', {}).values())

    def sort_middlewares(self, middlewares):
        # middleware process
        # middleware can be defined as
        # middleware_name = middleware_class_path[, order]
        # middleware_name = <empty> will be skip
        m = []
        for v in middlewares:
            if not v:
                continue

            order = None
            if isinstance(v, (list, tuple)):
                if len(v) > 2:
                    raise ServosError(
                        'Middleware %r difinition is not right' % v)
                middleware_path = v[0]
                if len(v) == 2:
                    order = v[1]
            else:
                middleware_path = v
            cls = import_attr(middleware_path)

            if order is None:
                order = getattr(cls, 'ORDER', 500)
            m.append((order, cls))

        m.sort(cmp=lambda x, y: cmp(x[0], y[0]))

        return [x[1] for x in m]

    def internal_error(self, e):
        '''
        处理异常
        '''
        log.exception(e)
        return e

    def dispatch(self, incoming):
        '''
        执行服务调用
        :param incoming:调用信息。字典对象。
                        应包含:
                            service：要调用服务名
                            method：要调用的方法名
                            args：参数。字典类型

        '''

        middlewares = self.middlewares

        try:

            response = None
            _inss = {}
            for cls in middlewares:
                if hasattr(cls, 'process_request'):
                    ins = cls(self, settings)
                    _inss[cls] = ins
                    response = ins.process_request(incoming)
                    if response is not None:
                        break

            if response is None:
                try:

                    for _service in service.__services__:

                        service_name = incoming['service']
                        method = incoming['method']
                        args = incoming['args']

                        # todo: 可以增加服务接口版本的过滤
                        if not (_service._service_name == service_name):
                            continue

                        if hasattr(_service, method):
                            # 权限验证
                            if self.access_policy.is_allowed(_service, method):
                                response = self._do_dispatch(
                                    _service, method, args)
                            break
                    else:
                        raise NoSuchMethod(service_name, method)

                except Exception, e:
                    for cls in reversed(middlewares):
                        if hasattr(cls, 'process_exception'):
                            ins = _inss.get(cls)
                            if not ins:
                                ins = cls(self, settings)
                            response = ins.process_exception(incoming, e)
                            if response:
                                break
                    raise

            for cls in reversed(middlewares):
                if hasattr(cls, 'process_response'):
                    ins = _inss.get(cls)
                    if not ins:
                        ins = cls(self, settings)
                    response = ins.process_response(incoming, response)

        except Exception as e:
            if not self.settings.get_var('GLOBAL/DEBUG'):
                response = self.internal_error(e)
            else:
                #                log.exception(e)
                raise

        return response

    def _do_dispatch(self, service, method, args):
        func = getattr(service, method)
        result = func(**args)
        return result

    def __call__(self, incoming):
        return self.dispatch(incoming)


settings = LocalProxy(__global__, 'settings', pyini.Ini)
application = LocalProxy(__global__, 'application', Dispatcher)
