# Purpose

The goal of `conda_deps` is to generate a [conda environment file](https://bit.ly/2THhLnA) as a result of
the dependencies found in source code. Initially, this script will scan Python code only, but 
it would be great to have it working for other programming languages as well.

This script will translate import statements in Python source code like:

    import numpy
    import scipy

into a conda environment yaml file:

    name: testenv
    
    channels:
    - conda-forge
    - bioconda
    - defaults

    dependencies:
    - python
    - numpy
    - scipy

# Installation

`conda_deps` only works in **Python 3** and will only scan properly **Python 3** source code.

`conda_deps` has been uploaded to `conda-forge` so you can install it with:

    # if you don't have conda available:
    curl -O https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh
    bash Miniconda3-latest-Linux-x86_64.sh -b -p conda-install
    source conda-install/etc/profile.d/conda.sh 
    conda update --all --yes
    
    # once conda is available:
    conda create --name conda_deps --channel conda-forge conda_deps
    conda activate conda_deps
    conda_deps --help

# Usage

This is how you scan a single Python file:

    conda_deps </path/to/file.py>
    
The script can also scan folders:

    conda_deps </path/to/folder/>
    
In case you want to exclude one or more subfolders, use the `--exclude-folder` option one or more times:

    conda_deps --exclude-folder </path/to/folder/folder1> </path/to/folder>

You may also want to scan additonal Python files of folders:

    python conda_deps.py </path/to/folder> --include-py-files my-script.py --include-py-files </another/folder>
    
# How it works
    
The script uses [Python's Abstract Syntax Trees](https://docs.python.org/3/library/ast.html#module-ast)
to parse Python files. It looks for `import <module>` statements, and discards the modules belonging to the
Python Standard Library (e.g. `import os`). It assumes that `<module>` has a corresponding conda package
with the same name (e.g. `import numpy` corresponds to `conda install numpy`). However, that is not
always the case and you can provide a proper translation between the module name and its corresponding
conda package (e.g. `import yaml` will require `conda install pyyaml`) via the 
[python_deps.json](https://github.com/cgat-developers/conda-deps/blob/master/python_deps.json) file, which
will be loaded into a dictionary at the beginning of the script. It looks like this:

    {
        "Bio":"biopython",
        "Cython":"cython",
        "bs4":"beautifulsoup4",
        "bx":"bx-python",
        "lzo":"python-lzo",
        "pyBigWig":"pybigwig",
        "sklearn":"scikit-learn",
        "web":"web.py",
        "weblogolib":"python-weblogo",
        "yaml":"pyyaml"
    }    

The key is the name in `import <module>` and the value is the name of the conda package. 

The **python_deps.json** file is meant to be useful for generic use. However, it is possible to include
additional json files specific to your project:

    python conda_deps.py --include-json my_project.json </path/to/project/>

The translations in **my_project.json** will take priority over those in **python_deps.json**.

If you find that there are missing translations in the general purpose **python_deps.json** file, please
feel free to open a pull request to add more.

# Related tools

* [snakefood](http://furius.ca/snakefood/): a more comprehensive tool but it works only with Python 2.
* [pipreqs](https://github.com/bndr/pipreqs): does a similar job but for **requirements.txt** files and pip.

# References

* https://docs.python.org/3/library/ast.html#module-ast
* http://bit.ly/2rDf5xu
* http://bit.ly/2r0Uv9t
* https://github.com/titusjan/astviewer
