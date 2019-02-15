import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name="readgssi",
    version="0.0.10",
    author="Ian Nesbitt",
    author_email="ian.nesbitt@gmail.com",
    license='AGPL',
    description="Python tool to read and plot Geophysical Survey Systems Incorporated (GSSI) radar data in DZT format",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/iannesbitt/readgssi",
    packages=setuptools.find_packages(),
    install_requires=['obspy', 'numpy', 'geopy', 'matplotlib', 'pandas', 'h5py', 'pynmea2', 'pytz'],
    entry_points='''
        [console_scripts]
        readgssi=readgssi.readgssi:main
    ''',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Physics",
        "Natural Language :: English",
        "Development Status :: 4 - Beta",
    ],
)
