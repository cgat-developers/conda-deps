# Purpose

The goal of `conda_deps` is to generate a [conda environment file](https://bit.ly/2THhLnA) as a result of
the dependencies found in a repository. At the moment, it only translates Python and R dependencies
but it would be great to have it working for other programming languages as well.

`conda_deps` translates import statements in Python source code like:

    import numpy
    import scipy

into an environment file:

    name: testenv
    
    channels:
    - conda-forge
    - bioconda
    - defaults

    dependencies:
    - python
    - numpy
    - scipy

For R it translates library imports like:

    library(reshape2)
    library(ggplot2)

into:

    name: testenv
    
    channels:
    - conda-forge
    - bioconda
    - defaults

    dependencies:
    - r-base
    - r-reshape2    
    - r-ggplot2

## Warning

Please note that `conda_deps` does not check dependencies in a clever way. For example, if your code imports `scipy` and `numpy`, the script will generate an environment with both listed even though `numpy` **is** a dependency of `scipy` and only the latter would be required. So the expected output of `conda_deps` is a direct translation of the dependencies found in your code.

# Installation

`conda_deps` only works in **Python 3** and will only scan properly **Python 3** source code.
There should be no restriction in the case of R.

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

This is how you scan a single Python or R file:

    conda_deps </path/to/filename>
    
The script can also scan folders:

    conda_deps </path/to/folder/>
    
In case you want to exclude one or more subfolders, use the `--exclude-folder` option one or more times:

    conda_deps --exclude-folder </path/to/folder/folder1> </path/to/folder>

You may also want to scan additonal files of folders:

    conda_deps </path/to/folder> --include-files my-script.py --include-files </another/folder>
    
# How it works

## Python source code
    
The script uses [Python's Abstract Syntax Trees](https://docs.python.org/3/library/ast.html#module-ast)
to parse files ending in `.py`. It looks for `import <module>` statements, and discards the modules belonging to the
Python Standard Library (e.g. `import os`). It assumes that `<module>` has a corresponding conda package
with the same name (e.g. `import numpy` corresponds to `conda install numpy`). However, that is not
always the case and you can provide a proper translation between the module name and its corresponding
conda package (e.g. `import yaml` will require `conda install pyyaml`) via the 
[python_deps.json](https://github.com/cgat-developers/conda-deps/blob/master/conda_deps/python_deps.json) file, which
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

The dictionary key is the name in `import <module>` and the value is the name of the conda package. 

The **python_deps.json** file is meant to be useful for generic use. However, it is possible to include
additional json files specific to your project:

    conda_deps --include-py-json my_project.json </path/to/project/>

The translations in **my_project.json** will take priority over those in **python_deps.json**.

If you find that there are missing translations in the general purpose **python_deps.json** file, please
feel free to open a pull request to add more.

## R source code

In the case of R files, it uses `grep` to look for `library(name)` regular expressions in files ending in `.R`.
The same way we use a `json` file to detail translations for Python, 
we use the [r_deps.json](https://github.com/cgat-developers/conda-deps/blob/master/conda_deps/r_deps.json)
file which will be loaded into a dictionary at the beginning of the script. Here is how it looks like:

    {
        "dplyr":"r-dplyr",
        "edgeR":"bioconductor-edger",
        "flashClust":"r-flashclust",
        "gcrma":"bioconductor-gcrma",
        "ggplot2":"r-ggplot2",
        "gplots":"r-gplots",
        "gridExtra":"r-gridextra",
        "grid":"r-gridbase",
        "gtools":"r-gtools",
        "hpar":"bioconductor-hpar",
        "knitr":"r-knitr",
        "limma":"bioconductor-limma",
        "maSigPro":"bioconductor-masigpro",
    }

In this case the dictionary key is the name in `library(name)` and the value is the name of the conda package.

If you are missing a translation in **r_deps.json** you can either open a pull request to add it or include it
in your own json file:

    conda_deps --include-r-json my_project.json </path/to/project/>
    
Please note that the translations in **my_project.json** will take priority over those in **r_deps.json**.

## Warning

An important point to bear in mind is that the translations for both Python and R are not comprehensive and are mainly based in the dependencies used in the past. It will be a matter of time to keep adding new dependencies to the json files in charge of the translation. This implies that the environment file produced as output may not be valid straight away and conda will complain about that when creating the environment (i.e. error message: **PackagesNotFoundError**).

# Related tools

* [snakefood](http://furius.ca/snakefood/): a more comprehensive tool but it works only with Python 2.
* [pipreqs](https://github.com/bndr/pipreqs): does a similar job but for **requirements.txt** files and pip.

# References

* https://docs.python.org/3/library/ast.html#module-ast
* http://bit.ly/2rDf5xu
* http://bit.ly/2r0Uv9t
* https://github.com/titusjan/astviewer

# Changelog

* v0.0.9:
  - Scan **.Rmd** and **.ipynb** files as well, therefore the script now depends on **nbconvert**
  - Able to scan Python imports with multiple modules (e.g. `import numpy, matplotlib`)
  - Add new R dependencies to the json dictionary
  - Scan `rmagic` and `cythonmagic` in **.ipynb** files ([#1](https://github.com/cgat-developers/conda-deps/issues/1))
* v0.0.8:
  - [Add new R dependencies](https://github.com/cgat-developers/conda-deps/pull/6)
* v0.0.7:
  - Improve the test to check whether a module belongs to the Python Standard Library
  - Add new R dependencies to the json dictionary
* v0.0.6:
  - Add sanity check for dependency translation
  - [Improve regex to translate Bioconductor dependencies](https://github.com/cgat-developers/conda-deps/pull/3)
* v0.0.5:
  - Add **r_deps.json** to manifest file
  - Rename option **--include-py-files** to **--include-files**
* v0.0.4: 
  - Add translation of R dependencies
  - Not uploaded to conda-forge due to missing **r_deps.json** in the manifest file
* v0.0.3: minor bugfixes.
* v0.0.2: first working version uploaded to conda-forge.
