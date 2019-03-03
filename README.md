# Purpose

The goal of this script is to generate a conda yaml environment file
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

# Usage

Assuming you have `conda-deps.py` in your working directory::

    python conda-deps.py </path/to/file.py>

# References

* https://docs.python.org/3/library/ast.html#module-ast
* http://bit.ly/2rDf5xu
* http://bit.ly/2r0Uv9t
* https://github.com/titusjan/astviewer
