import setuptools
from _version import version

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="readgssi",
    version=version,
    author="Ian Nesbitt",
    author_email="ian.nesbitt@gmail.com",
    license='AGPL',
    description="Python tool to read and plot Geophysical Survey Systems Incorporated (GSSI) radar data in DZT format",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://readgssi.readthedocs.org/",
    packages=setuptools.find_packages(),
    install_requires=['obspy', 'numpy', 'scipy', 'geopy', 'matplotlib', 'pandas', 'h5py', 'pynmea2', 'pytz'],
    entry_points='''
        [console_scripts]
        readgssi=readgssi.readgssi:main
    ''',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
        "Framework :: Matplotlib",
        "Topic :: Scientific/Engineering :: Physics",
        "Intended Audience :: Science/Research",
        "Natural Language :: English",
        "Development Status :: 4 - Beta",
    ],
)
