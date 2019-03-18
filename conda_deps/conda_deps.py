'''
conda_deps.py - translate dependencies into a conda recipe
==========================================================

Purpose
-------

.. The goal of this script is to generate a conda yaml environment file
as a result of the dependencies found in source code. Initially, this
script will scan Python code only, but it would be great to have it
working for other programming languages as well.

This script takes the path to a Python script, which contains import
statements like:

    import numpy
    import scipy

The result will be a yaml file like:

    name: testenv

    channels:
    - conda-forge
    - bioconda
    - defaults

    dependencies:
    - numpy
    - scipy

Usage
-----

.. python conda_deps.py </path/to/file.py>

References
----------

https://docs.python.org/3/library/ast.html#module-ast
http://bit.ly/2rDf5xu
http://bit.ly/2r0Uv9t
https://github.com/titusjan/astviewer

'''

import sys

# first things first
# are you using Py3?
if (sys.version_info < (3, 0, 0)):
    raise OSError('''You are using Python {}.{}.{}\n'''
                  '''This script only works with Python 3, sorry!'''
                  .format(sys.version_info.major,
                          sys.version_info.minor,
                          sys.version_info.micro))
    sys.exit(-1)

import os
import shutil
import importlib.util
import re
import ast
import argparse
import json
import logging

# modules part of the Python Standard Library
PY_STD = {'sys',
          'builtins',
          'xml'}

# Python files located inside the folder to scan
PY_LOCAL = []

# load translations for Python deps from default json file
(py_deps_folder, py_deps_file) = os.path.split(__file__)
if len(py_deps_folder) == 0:
    PY_DEPS = json.load(open('python_deps.json'))
else:
    PY_DEPS = json.load(open('{}/python_deps.json'.format(py_deps_folder)))


def config_logging(debug):
    '''
       Auxiliary function to configure logging
    '''
    # https://realpython.com/python-logging/
    # https://bit.ly/2VHKM44
    logFormatter = logging.Formatter(
        "# %(asctime)s [%(levelname)-5.5s]  %(message)s")
    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.INFO)
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    rootLogger.addHandler(consoleHandler)
    if debug:
        rootLogger.setLevel(logging.DEBUG)


def is_import(node):
    '''
       Auxiliary function to get import statements from
       a .py file
    '''

    result = None

    if isinstance(node, ast.Import) and \
            hasattr(node, 'names') and \
            hasattr(node.names[0], 'name'):
        result = node.names[0].name

    elif isinstance(node, ast.ImportFrom) and \
            hasattr(node, 'module'):
        result = node.module

    return result


# References:
# https://bit.ly/2BXcW3l
# https://docs.python.org/3/library/importlib.html
def is_python_std(name):
    '''
       Auxiliary function to test if a module is part
       of Python's standard library or not
    '''

    if name in PY_STD:
        logging.debug('{} is part of Python Standard Library'.format(name))
        return True

    result = False

    #python_path = os.path.dirname(sys.executable)
    module_path = None

    try:
        module_path = importlib.util.find_spec(name).origin
    except BaseException:
        pass

    logging.debug('Module Name: {}'.format(name))
    #logging.debug('Python Path: {}'.format(python_path))
    logging.debug('Module Path: {}'.format(module_path))

    if module_path is not None:
        result = ('site-packages' not in module_path and \
            'dist-packages' not in module_path)
            #python_path in module_path

    logging.debug(
        'Is {} part of Python Standard Library? {}'.format(
            name, result))

    return result


def get_local_imports(folder):
    '''
       When scanning a folder, the import might refer
       to a Python file inside the folder itself
    '''

    result = []

    if os.path.isdir(folder) and os.access(folder, os.R_OK):
        for dirpath, dirs, files in os.walk(folder):
            for d in dirs:
                result.append(d)
            for f in files:
                if f.endswith(".py"):
                    result.append(os.path.splitext(f)[0])
    return result


def cleanup_import(name):
    '''
       Auxiliary function to extract the main module name
       from import statements (e.g. matplotlib.pyplot -> matplotlib)
    '''

    result = re.match(r"(\w+)(\S*)", name)
    return result.group(1)


def translate_import(name):
    '''
       Auxiliary function to translate the module name
       into its conda package (e.g. cgat -> cgat-apps)

       The translation assumes that by default a package
       will be named the same as its import (e.g. numpy).
       When that's not the case, we convert it using the
       translation detailed in the file "python_deps.json"

       python_deps.json will be growing over time as
       we find more cases where the package name and the
       import name differs
    '''

    result = PY_DEPS.get(name, name)

    return result


def scan_imports(filename):
    '''
       Auxiliary function to get imports from a single file
    '''
    # check input is correct
    if not os.access(filename, os.R_OK):
        raise IOError("File {} can't be read\n".format(filename))

    logging.debug('Scanning file: {}'.format(filename))

    deps = set()

    # parse script with Python's AST module:
    # https://docs.python.org/3/library/ast.html#module-ast
    try:
        with open(filename) as f:
            tree = ast.parse(f.read())

        # inspired by
        # http://bit.ly/2rDf5xu
        # http://bit.ly/2r0Uv9t
        # really helpful, used astviewer (installed in a conda-env) to inspect examples
        # https://github.com/titusjan/astviewer
        for node in ast.walk(tree):
            module = is_import(node)
            if module is not None and not is_python_std(module):
                module = cleanup_import(module)
                module = translate_import(module)
                if module != "ignore" and module not in PY_LOCAL:
                    deps.add(module)

    except BaseException:
        logging.warning("Could not parse file: {}".format(filename))

    return deps


def check_python_deps(filename, exclude_folder):
    '''
       Auxiliary function to detect whether input is a file or a folder
       and operate accordingly
    '''

    # check input is correct
    if not os.access(filename, os.R_OK):
        raise IOError("File {} can't be read\n".format(filename))

    # list of files to scan
    scan_this = []

    if os.path.isdir(filename):
        # scan all python files in the folder
        for dirpath, dirs, files in os.walk(filename):
            for d in dirs.copy():
                full_dir = os.path.abspath(os.path.join(dirpath, d))
                if full_dir in exclude_folder:
                    dirs.remove(d)
                    logging.debug("not going down {}".format(full_dir))
            for f in files:
                if f.endswith(".py"):
                    scan_this.append(os.path.join(dirpath, f))
    else:
        # case of single file
        scan_this.append(filename)

    # set of dependencies
    all_deps = set()

    # scan all files
    for f in scan_this:
        deps = scan_imports(f)
        all_deps.update(deps)

    return all_deps


def print_conda_env(deps, envname="myenv",
                    envchannels=["conda-forge", "bioconda", "defaults"]):
    '''
       Print conda environment file
    '''

    if len(deps) == 0:
        print("\nNo dependencies found.\n")
        return

    print("\nname: {}".format(envname))

    print("\nchannels:")
    for c in envchannels:
        print(" - {}".format(c))
    print("\ndependencies:")
    print(" - python")
    for d in sorted(deps):
        print(" - {}".format(d))


def main(argv=None):
    """script main.
    parses command line options in sys.argv, unless *argv* is given.
    """

    if argv is None:
        argv = sys.argv

    # setup command line parser
    parser = argparse.ArgumentParser(
        description='Translate Python dependencies into a conda environment file.')

    parser.add_argument("filename", help="Path to Python file")
    parser.add_argument("--debug",
                        help="Print debugging info",
                        action="store_true",
                        default=False)
    parser.add_argument("--exclude-folder",
                        help="Path to a folder to exclude",
                        action="append",
                        default=[])
    parser.add_argument(
        "--include-json",
        help="Path to a json file with project specific translations",
        action="append",
        default=[])
    parser.add_argument(
        "--include-py-files",
        help="Path to additional Python files and/or folders to scan",
        action="append",
        default=[])

    options = parser.parse_args()

    # configure logging
    config_logging(options.debug)

    # get a list of all Python files inside the folder
    global PY_LOCAL
    PY_LOCAL = get_local_imports(options.filename)

    # update default translation dict with project specific ones
    for j in options.include_json:
        PY_DEPS.update(json.load(open(j)))

    # get dependencies
    deps = check_python_deps(options.filename, list(
        map(os.path.abspath, options.exclude_folder)))

    # scan additional dependencies
    for f in options.include_py_files:
        deps.update(check_python_deps(f, list(
            map(os.path.abspath, options.exclude_folder))))

    # print info about dependencies
    print_conda_env(deps)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
