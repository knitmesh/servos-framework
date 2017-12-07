#!/usr/bin/env python
from optparse import make_option
import inspect
import logging
import os
import sys

from servos.core import simpleframe
from servos.core.commands import Command, CommandManager


__commands__ = {}

log = logging.getLogger('servos.console')


def get_commands(global_options):
    global __commands__

    def check(c):
        return (inspect.isclass(c) and
                issubclass(c, Command) and
                c is not Command and
                c is not CommandManager)

    def find_mod_commands(mod):
        for name in dir(mod):
            c = getattr(mod, name)
            if check(c):
                register_command(c)

    def collect_commands():
        from servos import get_services, get_service_dir
        from servos.utils.common import is_pyfile_exist

        services = get_services(
            global_options.services_dir,
            settings_file=global_options.settings,
            local_settings_file=global_options.local_settings)
        for f in services:
            path = get_service_dir(f)
            if is_pyfile_exist(path, 'commands'):
                m = '%s.commands' % f
                mod = __import__(m, fromlist=['*'])

                find_mod_commands(mod)

    collect_commands()
    return __commands__


def register_command(kclass):
    global __commands__
    __commands__[kclass.name] = kclass


def install_config(services_dir):
    from servos.utils import pyini
    # user can configure custom PYTHONPATH, so that servos can add these paths
    # to sys.path, and user can manage third party or public services in a separate
    # directory
    config_filename = os.path.join(services_dir, 'config.ini')
    if os.path.exists(config_filename):
        c = pyini.Ini(config_filename)
        paths = c.GLOBAL.get('PYTHONPATH', [])
        if paths:
            for p in reversed(paths):
                p = os.path.abspath(os.path.normpath(p))
                if p not in sys.path:
                    sys.path.insert(0, p)


def make_application(services_dir='services',
                     settings_file=None,
                     local_settings_file=None,
                     default_settings=None,
                     start=True,
                     dispatcher_cls=None,
                     dispatcher_kwargs=None,
                     reuse=True,
                     verbose=False):
    """
    Make an application object
    """
    # is reuse, then create application only one
    if reuse and hasattr(simpleframe.__global__, 'application') and \
            simpleframe.__global__.application:
        return simpleframe.__global__.application

    # process settings and local_settings
    settings_file = settings_file or os.environ.get('SETTINGS', 'settings.ini')
    local_settings_file = local_settings_file or os.environ.get(
        'LOCAL_SETTINGS', 'local_settings.ini')

    dispatcher_cls = dispatcher_cls or simpleframe.Dispatcher
    dispatcher_kwargs = dispatcher_kwargs or {}

    services_dir = os.path.normpath(services_dir)

    if services_dir not in sys.path:
        sys.path.insert(0, services_dir)

    install_config(services_dir)

    application = dispatcher_cls(services_dir=services_dir,
                                 settings_file=settings_file,
                                 local_settings_file=local_settings_file,
                                 start=start,
                                 default_settings=default_settings,
                                 **dispatcher_kwargs)

    if verbose:
        log.info(' * settings file is "%s"' % settings_file)
        log.info(' * local settings file is "%s"' % local_settings_file)

    return application


def make_simple_application(services_dir='services',
                            settings_file=None,
                            local_settings_file=None,
                            default_settings=None,
                            start=True,
                            dispatcher_cls=None,
                            dispatcher_kwargs=None,
                            reuse=True,
                            ):

    return make_application(services_dir=services_dir,
                            settings_file=settings_file,
                            local_settings_file=local_settings_file,
                            start=False,
                            default_settings=default_settings,
                            dispatcher_cls=dispatcher_cls,
                            dispatcher_kwargs=dispatcher_kwargs,
                            reuse=reuse)


class MakeProjectCommand(Command):
    name = 'makeproject'
    help = 'Create a new project directory according the project name'
    args = 'project_name'
    check_services_dirs = False

    def handle(self, options, global_options, *args):
        from servos.utils.common import extract_dirs

        if not args:
            project_name = ''
            while not project_name:
                project_name = raw_input('Please enter project name:')
        else:
            project_name = args[0]

        ans = '-1'
        if os.path.exists(project_name):
            if global_options.yes:
                ans = 'y'
            while ans not in ('y', 'n'):
                ans = raw_input(
                    'The project directory has been existed, do you want to overwrite it?(y/n)[n]')
                if not ans:
                    ans = 'n'
        else:
            ans = 'y'
        if ans == 'y':
            extract_dirs('servos', 'template_files/project',
                         project_name, verbose=global_options.verbose)

            # rename .gitignore.template to .gitignore
            os.rename(os.path.join(project_name, '.gitignore.template'), os.path.join(
                project_name, '.gitignore'))

register_command(MakeProjectCommand)


class MakeServiceCommand(Command):
    name = 'makeservice'
    args = 'servicename'
    help = 'Create a new service according the servicename parameter.'
    check_services_dirs = False

    def handle(self, options, global_options, *args):
        from servos.utils.common import extract_dirs

        if not args:
            service_name = ''
            while not service_name:
                service_name = raw_input('Please enter service name:')
            services = [service_name]
        else:
            services = args

        for service_name in services:
            ans = '-1'
            service_path = service_name.replace('.', '//')
            if os.path.exists('services'):
                path = os.path.join('services', service_path)
            else:
                path = service_path

            if os.path.exists(path):
                if global_options.yes:
                    ans = 'y'
                while ans not in ('y', 'n'):
                    ans = raw_input(
                        'The service directory has been existed, do you want to overwrite it?(y/n)[n]')
                    if not ans:
                        ans = 'n'
            else:
                ans = 'y'
            if ans == 'y':
                extract_dirs(
                    'servos', 'template_files/service', path, verbose=global_options.verbose)

register_command(MakeServiceCommand)


class MakeCmdCommand(Command):
    name = 'makecmd'
    help = 'Created a commands.py to the services or current directory.'
    args = '[servicename, servicename, ...]'
    check_services = False
    check_services_dirs = False

    def handle(self, options, global_options, *args):
        from servos.utils.common import extract_dirs
        from servos import get_service_dir

        if not args:
            extract_dirs(
                'servos', 'template_files/command', '.', verbose=global_options.verbose)
        else:
            for f in args:
                p = get_service_dir(f)
                extract_dirs(
                    'servos', 'template_files/command', p, verbose=global_options.verbose)

register_command(MakeCmdCommand)


class InstallCommand(Command):
    name = 'install'
    help = 'install [servicename,...] extra modules listed in requirements.txt'
    args = '[servicename]'
    option_list = (
        make_option('-r', '--requirement', dest='requirement',
                    default='requirements.txt',
                    help='Global requirements file, default is "%default".'),
    )

    def handle(self, options, global_options, *args):
        from servos.core.simpleframe import get_service_dir

        # check pip or setuptools
        try:
            import pip
        except:
            print "Error: can't import pip module, please install it first"
            sys.exit(1)

        services = args or self.get_services(global_options)

        def get_requirements():
            for service in services:
                path = get_service_dir(service)
                r_file = os.path.join(path, 'requirements.txt')
                if os.path.exists(r_file):
                    yield r_file
            r_file = os.path.join(
                global_options.services_dir, options.requirement)
            if os.path.exists(r_file):
                yield r_file

        for r_file in get_requirements():
            if global_options.verbose:
                print "Processing... %s" % r_file
            os.system('pip install -r %s' % r_file)

register_command(InstallCommand)


class FindCommand(Command):
    name = 'find'
    help = 'Find objects in servos, such as: config option etc.'
    args = ''
    check_services_dirs = True
    option_list = (
        make_option('-o', '--option', dest='option',
                    help='Find ini option defined in which settings.ini.'),
    )

    def handle(self, options, global_options, *args):
        #         self.get_application(global_options)
        if options.option:
            self._find_option(global_options, options.option)
        else:
            self._find_option(global_options, args[0])

    def _find_option(self, global_options, option):
        self.get_application(global_options)
        from servos import settings
        from servos.core.simpleframe import collect_settings
        from servos.utils.pyini import Ini

        print '------ Combined value of [%s] ------' % option
        print settings.get_var(option)

        print '------ Detail   value of [%s] ------' % option
        sec_flag = '/' not in option
        if not sec_flag:
            section, key = option.split('/')

        for f in collect_settings(
                global_options.services_dir,
                settings_file=global_options.settings,
                local_settings_file=global_options.local_settings):
            x = Ini(f, raw=True)
            if sec_flag:
                if option in x:
                    print x[option]
            else:
                if section in x:
                    if key in x[section]:
                        v = x[section][key]
                        print "%s %s%s" % (str(v), key, v.value())

register_command(FindCommand)


class RunserverCommand(Command):
    name = 'runserver'
    help = 'Start a new development server.'
    args = ''
    option_list = (
        make_option('-b', '--background', dest='background', action='store_true', default=False,
                    help='If run in background. Default is False.'),
    )

    def handle(self, options, global_options, *args):

        if options.background:
            daemonize()

        make_application(services_dir=global_options.services_dir,
                         settings_file=global_options.settings,
                         local_settings_file=global_options.local_settings,
                         verbose=global_options.verbose)

register_command(RunserverCommand)


def daemonize():
    """
    do the UNIX double-fork magic, see Stevens' "Advanced
    Programming in the UNIX Environment" for details (ISBN 0201563177)
    http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
    """
    try:
        pid = os.fork()
        if pid > 0:
            # exit first parent
            sys.exit(0)
    except OSError, e:
        sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
        sys.exit(1)

    os.setsid()

    # do second fork
    try:
        pid = os.fork()
        if pid > 0:
            # exit from second parent
            sys.exit(0)
    except OSError, e:
        sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
        sys.exit(1)

    # redirect standard file descriptors
    sys.stdout.flush()
    sys.stderr.flush()
    si = file("/dev/null", 'r')
    so = file("/dev/null", 'a+')
    se = file("/dev/null", 'a+', 0)
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())


def call(args=None):
    from servos.core.commands import execute_command_line

    def callback(global_options):
        services_dir = global_options.services_dir or os.path.join(
            os.getcwd(), 'services')
        if os.path.exists(services_dir) and services_dir not in sys.path:
            sys.path.insert(0, services_dir)

        install_config(services_dir)

    if isinstance(args, (unicode, str)):
        import shlex
        args = shlex.split(args)

    execute_command_line(args or sys.argv, get_commands, 'servos', callback)


def main():
    call()

if __name__ == '__main__':
    main()
