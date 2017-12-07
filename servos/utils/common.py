import os
import re
import logging
import inspect
import sys

log = logging


def safe_import(path):
    module = path.split('.')
    g = __import__(module[0], fromlist=['*'])
    s = [module[0]]
    for i in module[1:]:
        mod = g
        if hasattr(mod, i):
            g = getattr(mod, i)
        else:
            s.append(i)
            g = __import__('.'.join(s), fromlist=['*'])
    return mod, g


def import_mod_attr(path):
    """
    Import string format module, e.g. 'servos.utils.sorteddict' or an object
    return module object and object
    """
    if isinstance(path, (str, unicode)):
        v = path.split(':')
        if len(v) == 1:
            module, func = path.rsplit('.', 1)
        else:
            module, func = v
        mod = __import__(module, fromlist=['*'])
        f = mod
        for x in func.split('.'):
            f = getattr(f, x)
    else:
        f = path
        mod = inspect.getmodule(path)
    return mod, f


def import_attr(func):
    mod, f = import_mod_attr(func)
    return f


def myimport(module):
    mod = __import__(module, fromlist=['*'])
    return mod


class MyPkg(object):

    @staticmethod
    def resource_filename(module, path):
        mod = myimport(module)
        p = os.path.dirname(mod.__file__)
        if path:
            return os.path.join(p, path)
        else:
            return p

    @staticmethod
    def resource_listdir(module, path):
        d = MyPkg.resource_filename(module, path)
        return os.listdir(d)

    @staticmethod
    def resource_isdir(module, path):
        d = MyPkg.resource_filename(module, path)
        return os.path.isdir(d)

try:
    import pkg_resources as pkg
except:
    pkg = MyPkg


def norm_path(path):
    return os.path.normpath(os.path.abspath(path))

r_expand_path = re.compile('\$\[(\w+)\]')


def expand_path(path):
    """
    Auto search some variables defined in path string, such as:
        $[PROJECT]/files
        $[service_name]/files
    for $[PROJECT] will be replaced with servos application services_dir directory
    and others will be treated as a normal python package, so servos will
    use pkg_resources to get the path of the package

    """
    from servos import application

    def replace(m):
        txt = m.groups()[0]
        if txt == 'PROJECT':
            return application.services_dir
        else:
            return pkg.resource_filename(txt, '')
    return re.sub(r_expand_path, replace, path)


def check_services_dir(services_dir):
    if not os.path.exists(services_dir):
        print >>sys.stderr, "[Error] Can't find the services_dir [%s], please check it out" % services_dir
        sys.exit(1)


def is_pyfile_exist(dir, pymodule):
    path = os.path.join(dir, '%s.py' % pymodule)
    if not os.path.exists(path):
        path = os.path.join(dir, '%s.pyc' % pymodule)
        if not os.path.exists(path):
            path = os.path.join(dir, '%s.pyo' % pymodule)
            if not os.path.exists(path):
                return False
    return True


def extract_file(module, path, dist, verbose=False, replace=True):
    outf = os.path.join(dist, os.path.basename(path))
    import shutil

    inf = pkg.resource_filename(module, path)
    sfile = os.path.basename(inf)
    if os.path.isdir(dist):
        dfile = os.path.join(dist, sfile)
    else:
        dfile = dist
    f = os.path.exists(dfile)
    if replace or not f:
        shutil.copy2(inf, dfile)
        if verbose:
            print 'Copy %s to %s' % (inf, dfile)


def extract_dirs(mod, path, dst, verbose=False, exclude=None, exclude_ext=None, recursion=True, replace=True):
    """
    mod name
    path mod path
    dst output directory
    resursion True will extract all sub module of mod
    """
    default_exclude = ['.svn', '_svn', '.git']
    default_exclude_ext = ['.pyc', '.pyo', '.bak', '.tmp']
    exclude = exclude or []
    exclude_ext = exclude_ext or []
    if not os.path.exists(dst):
        os.makedirs(dst)
        if verbose:
            print 'Make directory %s' % dst
    for r in pkg.resource_listdir(mod, path):
        if r in exclude or r in default_exclude:
            continue
        fpath = os.path.join(path, r)
        if pkg.resource_isdir(mod, fpath):
            if recursion:
                extract_dirs(mod, fpath, os.path.join(
                    dst, r), verbose, exclude, exclude_ext, recursion, replace)
        else:
            ext = os.path.splitext(fpath)[1]
            if ext in exclude_ext or ext in default_exclude_ext:
                continue
            extract_file(mod, fpath, dst, verbose, replace)
