'''
cgat_check_deps.py - find third-party dependencies in CGAT-core pipelines
=========================================================================

Adapted from:
https://github.com/cgat-developers/cgat-flow/blob/master/scripts/cgat_check_deps.py

Purpose
-------

.. The goal of this script is to find a list of third-party command-line
programs used in cgat-core pipelines.

It expects to find command-line programs called the CGAT way, i.e.:

   statement = """cmd-1 | cmd-2 | cmd-3""""
   P.run(statement)

Programs called other way (e.g. using subprocess) will not be picked up
by this script.
'''

import os
import shutil
import sys
import re
import ast
import argparse
import bashlex
import logging


# inspired by
# https://docs.python.org/3/library/ast.html#module-ast
# http://bit.ly/2rDf5xu
# http://bit.ly/2r0Uv9t
# really helpful, used astviewer (installed in a conda-env) to inspect examples
# https://github.com/titusjan/astviewer
def is_cgat_statement(node):
    '''
       Auxiliary function to check for cgat statement:
           statement = "command"
    '''

    result = False
    result = type(node) is ast.Assign and \
        hasattr(node, 'targets') and \
        hasattr(node.targets[0], 'id') and \
        node.targets[0].id == "statement"

    return result


def is_cgat_executable(node):
    '''
       Auxiliary function to check for cgat statement:
           executable = "command"
    '''

    result = False
    result = type(node) is ast.Assign and \
        hasattr(node, 'targets') and \
        hasattr(node.targets[0], 'id') and \
        node.targets[0].id == "executable"

    return result


def is_cgat_executable_name(node):
    '''
       Auxiliary function to check for cgat statement:
           executable_name = "command"
    '''

    result = False
    result = type(node) is ast.Assign and \
        hasattr(node, 'targets') and \
        hasattr(node.targets[0], 'id') and \
        node.targets[0].id == "executable_name"

    return result


def is_cgat_cmd(node):
    '''
       Auxiliary function to check for cgat statement:
           cmd = "command"
    '''

    result = False
    result = type(node) is ast.Assign and \
        hasattr(node, 'targets') and \
        hasattr(node.targets[0], 'id') and \
        node.targets[0].id == "cmd"

    return result


def is_cgat_append(node):
    '''
       Auxiliary function to check for cgat statement:
           statment.append("command")
    '''

    result = False
    result = type(node) is ast.Expr and \
        hasattr(node, 'value') and \
        hasattr(node.value, 'func') and \
        hasattr(node.value.func, 'value') and \
        hasattr(node.value.func.value, 'id') and \
        node.value.func.value.id == "statement" and \
        hasattr(node.value.func, 'attr') and \
        node.value.func.attr == "append"

    return result


def get_cmd_string(node):
    '''
       Auxiliary function to get commands in the cgat statement:
           statement = "command"
    '''
    
    result = ""
    if hasattr(node.value, 's'):
        result = node.value.s
    elif hasattr(node.value, 'left') and hasattr(node.value.left, 's'):
        result = node.value.left.s
    elif hasattr(node.value, 'func') and \
            hasattr(node.value.func, 'value') and \
            hasattr(node.value.func.value, 's'):
        result = node.value.func.value.s

    return result


def get_append_string(node):
    '''
       Auxiliary function to get commands in the cgat statement:
           statement.append("command")
    '''

    result = ""
    if hasattr(node, 'value') and \
       hasattr(node.value, 'args') and \
       hasattr(node.value.args[0], 's'):
        result = node.value.args[0].s
    elif hasattr(node, 'value') and \
            hasattr(node.value, 'args') and \
            hasattr(node.value.args[0], 'left') and \
            hasattr(node.value.args[0].left, 's'):
        result = node.value.args[0].left.s

    return result


def cleanup_statement(statement):
    '''
       Auxiliary function to cleanup cgat statements
    '''
    # cleanup whitespaces, tabs, and newlines
    result = " ".join(statement.split())
    # cleanup parameter interpolation
    result = re.sub("\%\(\w+\)\w+", "cgatparameter", result)
    return result


# Thanks to: https://github.com/idank/bashlex
# Workflow:
# statement = ''' <whatever> '''
# statement = " ".join(statement.split())
# statement = re.sub("\%\(", "", statement)
# statement = re.sub("\)s", "", statement)
# parts = bashlex.parse(statement)
# commands = []
# get_cmd_names(parts[0], commands)
def get_cmd_names(tree, commands):
    if hasattr(tree, 'parts') and len(tree.parts) == 0:
        return
    else:
        if hasattr(tree, 'kind'):
            if tree.kind == 'command' and hasattr(tree.parts[0], 'word'):
                result = str(tree.parts[0].word)
                if result != 'sudo':
                    commands.append(result)
                else:
                    commands.append(str(tree.parts[1].word))
            if (tree.kind == 'processsubstitution' or tree.kind == 'commandsubstitution') and \
                    hasattr(tree, 'command') and hasattr(tree.command, 'parts') and \
                    hasattr(tree.command.parts[0], 'word'):
                result = str(tree.command.parts[0].word)
                if result != 'sudo':
                    commands.append(result)
                else:
                    commands.append(str(tree.command.parts[1].word))
        if hasattr(tree, 'parts'):
            for e in tree.parts:
                get_cmd_names(e, commands)
        if hasattr(tree, 'command'):
            for e in tree.command.parts:
                get_cmd_names(e, commands)


def scan_cgatcore_deps(filename):
    '''
       Auxiliary function to get third-party command-line programs used in cgatcore.

       It expects to find command-line programs called the CGAT way, i.e.:

           statement = """cmd-1 | cmd-2 | cmd-3""""
           P.run(statement)
    '''

    # check existence of pipeline script
    if not os.access(filename, os.R_OK):
        raise IOError("File {} can't be read\n".format(filename))

    #logging.debug('cgat-core scan for file: {}'.format(filename))

    deps = set()

    # parse pipeline script
    with open(filename) as f:
        tree = ast.parse(f.read())

    # list to store all statements = ''' <commands> '''
    statements = []

    # inspired by
    # https://docs.python.org/3/library/ast.html#module-ast
    # http://bit.ly/2rDf5xu
    # http://bit.ly/2r0Uv9t
    # really helpful, used astviewer (installed in a conda-env) to inspect examples
    # https://github.com/titusjan/astviewer
    for node in ast.walk(tree):
        statement = ""
        if is_cgat_statement(node) or \
           is_cgat_executable(node) or \
           is_cgat_executable_name(node) or \
           is_cgat_cmd(node):

            statement = get_cmd_string(node)

        elif is_cgat_append(node):
            statement = get_append_string(node)

        if len(statement) > 0 and not statement.startswith(' -'):
            #print(statement)
            statement = cleanup_statement(statement)
            statements.append(statement)

    for statement in statements:
        # use bashlex to parse statements
        commands = []
        try:
            #print(statement)
            parts = bashlex.parse(statement)
            get_cmd_names(parts[0], commands)
        except bashlex.errors.ParsingError:
            logging.warning("scan_cgatcore_deps; could not parse file: {}".format(filename))

        for command in commands:
            #print(command)
            deps.add(command)

    return deps
