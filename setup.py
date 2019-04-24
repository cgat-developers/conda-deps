import setuptools

# References:
# https://packaging.python.org/tutorials/packaging-projects/
# https://python-packaging.readthedocs.io/en/latest/command-line-scripts.html
# https://python-packaging.readthedocs.io/en/latest/non-code-files.html

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="conda_deps",
    version="0.0.6",
    author="cgat-developers",
    author_email="sebastian.luna.valero@gmail.com",
    description="Generate conda environment files from Python source code",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cgat-developers/conda-deps",
    packages=setuptools.find_packages(),
    entry_points = {
        'console_scripts': ['conda_deps=conda_deps.conda_deps:main'],
    },
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
