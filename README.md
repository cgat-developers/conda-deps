# Purpose

**Warning: This is work in progress, and not must be used yet**

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

# Installation

This script only works in **Python 3** and will only scan properly **Python 3** source code.

Here are a few commands to get the script up and running from scratch:

    curl -O https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh
    bash Miniconda3-latest-Linux-x86_64.sh -b -p conda-install
    source conda-install/etc/profile.d/conda.sh 
    conda update --all --yes
    conda create -n conda-deps python=3
    conda activate conda-deps
    wget https://raw.githubusercontent.com/cgat-developers/conda-deps/master/conda-deps.py
    wget https://raw.githubusercontent.com/cgat-developers/conda-deps/master/python-deps.json
    python conda-deps.py --help

# Usage

Assuming you have `conda-deps.py` in your working directory:

    python conda-deps.py </path/to/file.py>
    
The script can also scan folders with Python code in it:

    python conda-deps.py </path/to/folder/>
    
In case you want to exclude one or more subfolders, use the `--exclude-folder` option one or more times:

    python conda-deps.py --exclude-folder </path/to/folder/folder1> </path/to/folder>
    
By default, the script looks for `import <module>` statements in files ending in `.py`. 
First, it discards `module` when it is part of the Python Standard Library (e.g. `import os`).
Otherwise, it assumes that there is a conda package called `module` (e.g. `import numpy` corresponds
to the `numpy` package in conda). However, since that is not always the case, it translates `module`
to something else by looking at a dictionary created by loading the
[python-deps.json](https://github.com/cgat-developers/conda-deps/blob/master/python-deps.json) file.


# References

* https://docs.python.org/3/library/ast.html#module-ast
* http://bit.ly/2rDf5xu
* http://bit.ly/2r0Uv9t
* https://github.com/titusjan/astviewer
