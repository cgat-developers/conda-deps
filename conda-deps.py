'''
conda-deps.py - translate dependencies into a conda recipe
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

.. python conda-deps.py </path/to/file.py>

References
----------

https://docs.python.org/3/library/ast.html#module-ast
http://bit.ly/2rDf5xu
http://bit.ly/2r0Uv9t
https://github.com/titusjan/astviewer

'''

import os
import shutil
import sys
import importlib.util
import re
import ast
import argparse
import json

# load translations for Python deps
PY_DEPS = json.load(
    open('{}/python-deps.json'.format(os.path.split(__file__)[0])))


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

    if name == 'sys':
        return True

    result = False

    python_path = os.path.dirname(sys.executable)
    module_path = None

    try:
        module_path = importlib.util.find_spec(name).origin
    except BaseException:
        pass

    #print(">>>> {}".format(name))
    #print(">>>> {}".format(python_path))
    #print(">>>> {}".format(module_path))

    if module_path is not None:
        result = 'site-packages' not in module_path or \
            python_path in module_path

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
       translation detailed in the file "python-deps.json"

       python-deps.json will be growing over time as
       we find more cases where the package name and the
       import name differs
    '''

    result = PY_DEPS.get(name, name)

    return result


def check_python_deps(filename):

    # check input is correct
    if not os.access(filename, os.R_OK):
        raise IOError("File {} was not found\n".format(filename))

    if os.path.isdir(filename):
        raise IOError("The given input is a folder, and must be a file\n")

    # parse script with Python's AST module:
    # https://docs.python.org/3/library/ast.html#module-ast
    with open(filename) as f:
        tree = ast.parse(f.read())

    deps = set()

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
            if module != "ignore":
                deps.add(module)

    return deps


def print_conda_env(deps, envname="myenv",
                    envchannels=["conda-forge", "bioconda", "defaults"]):
    '''
       Print conda environment file
    '''

    if len(deps) == 0:
        print("\nNo dependencies found.\n")
        return

    print("\nname: {}".format(envname))
    print("channels:")
    for c in envchannels:
        print(" - {}".format(c))
    print("dependencies:")
    for d in deps:
        print(" - {}".format(d))


def main(argv=None):
    """script main.
    parses command line options in sys.argv, unless *argv* is given.
    """

    if (sys.version_info < (3, 0, 0)):
        raise OSError("This script is Python 3 only")
        sys.exit(-1)

    if argv is None:
        argv = sys.argv

    # setup command line parser
    parser = argparse.ArgumentParser(
        description='Translate Python dependencies into a conda environment file.')

    parser.add_argument("filename", help="Path to Python file")

    options = parser.parse_args()

    # get dependencies dependencies
    deps = check_python_deps(options.filename)

    # print info about dependencies
    print_conda_env(deps)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
