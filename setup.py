import setuptools

# Reference:
# https://packaging.python.org/tutorials/packaging-projects/

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="conda_deps",
    version="0.0.1",
    author="cgat-developers",
    author_email="sebastian.luna.valero@gmail.com",
    description="Generate conda environment files from Python source code",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pypa/sampleproject",
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
