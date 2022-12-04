import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='PyLTSpice',
    # version='2.3.1',
    scripts=['PyLTSpice/__init__.py',
             'PyLTSpice/detect_encoding.py',
             'PyLTSpice/Histogram.py',
             'PyLTSpice/RawRead.py',
             'PyLTSpice/RawWrite.py',
             'PyLTSpice/SemiDevOpReader.py',
             'PyLTSpice/SpiceBatch.py',
             'PyLTSpice/LTSteps.py',
             'PyLTSpice/sim_stepping.py',
             'PyLTSpice/SpiceEditor.py',
             'PyLTSpice/sweep_iterators.py',
             ],
    # install_requires = [],
    author="Nuno Brum",
    author_email="me@nunobrum.com",
    description="An set of tools to Automate LTSpice simulations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nunobrum/PyLTSpice",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
)
