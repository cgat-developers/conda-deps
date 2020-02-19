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

# ways in which cgatcore name P.run(things)
CMD_OPTS = {'statement',
            'executable',
            'executable_name',
            'cmd'}

# inspired by
# https://docs.python.org/3/library/ast.html#module-ast
# http://bit.ly/2rDf5xu
# http://bit.ly/2r0Uv9t
# really helpful, used astviewer (installed in a conda-env) to inspect examples
# https://github.com/titusjan/astviewer
def is_cgat_statement(node):
    '''
        Auxiliary function to check for cgatcore P.run(things):
            Option 1) statement = "command"
            Option 2) executable = "command"
            Option 3) executable_name "command"
            Option 4) cmd = "command"

        Parameters:
            node: AST node

        Returns:
            result (boolean): whether it is a cgatcore statement or not
            bash_statement (string): if yes, it contains the bash statement

    '''

    # initialize outputs
    result = False
    bash_statement = None

    if type(node) is ast.Assign:
        # statement = "command"
        result = hasattr(node, 'targets') and \
            hasattr(node.targets[0], 'id') and \
            node.targets[0].id in CMD_OPTS

        if result:
            if hasattr(node.value, 's'):
                bash_statement = node.value.s
            elif hasattr(node.value, 'left') and hasattr(node.value.left, 's'):
                bash_statement = node.value.left.s
            elif hasattr(node.value, 'func') and \
                    hasattr(node.value.func, 'value') and \
                    hasattr(node.value.func.value, 's') and \
                    len(node.value.func.value.s) > 1:
                bash_statement = node.value.func.value.s

            logging.debug('is_cgat_statement - assign; statement: {}'.format(bash_statement))

    elif type(node) is ast.Expr:
        # statement.append("command")
        result = hasattr(node, 'value') and \
            hasattr(node.value, 'func') and \
            hasattr(node.value.func, 'value') and \
            hasattr(node.value.func.value, 'id') and \
            node.value.func.value.id == "statement" and \
            hasattr(node.value.func, 'attr') and \
            node.value.func.attr == "append"

        if result:
            if hasattr(node, 'value') and \
               hasattr(node.value, 'args') and \
               hasattr(node.value.args[0], 's'):
                bash_statement = node.value.args[0].s
            elif hasattr(node, 'value') and \
                    hasattr(node.value, 'args') and \
                    hasattr(node.value.args[0], 'left') and \
                    hasattr(node.value.args[0].left, 's'):
                bash_statement = node.value.args[0].left.s

            logging.debug('is_cgat_statement - expr; statement: {}'.format(bash_statement))

    return bash_statement


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

        statement = is_cgat_statement(node)

        if statement is not None:
            statement = cleanup_statement(statement)
            statements.append(statement)
            logging.debug("scan_cgatcore_deps; statement to process: {}".format(statement))

    for statement in statements:
        # use bashlex to parse statements
        commands = []
        try:
            parts = bashlex.parse(statement)
            get_cmd_names(parts[0], commands)
        except bashlex.errors.ParsingError:
            logging.warning("scan_cgatcore_deps; could not parse file: {}".format(filename))
            logging.warning("scan_cgatcore_deps; ignoring statement: {}".format(statement))

        for command in commands:
            #print(command)
            deps.add(command)

    return deps
