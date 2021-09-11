
from setuptools import setup, find_packages

VERSION = (0, 0, 11)
__version__ = '.'.join(map(str, VERSION))

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read().replace('(/', '(https://github.com/emibcn/pywisp/blob/master/')

setup(
    name = 'pywisp_emibcn',
    version = __version__,
    description = "Access AirControl2, AirOS & Mikrotik",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author = "https://github.com/emibcn",
    author_email = "emibcn.github@gmail.com",
    url = "https://github.com/emibcn/pywisp",
    project_urls={
        "Bug Tracker": "https://github.com/emibcn/pywisp/issues",
    },
    license = "GPLv3",
    platforms = ["any"],
    packages = ['pywisp_emibcn'],
    package_dir = {"": "."},
    py_modules=['pywisp', 'pywisp/mikrotik', 'pywisp/aircontrol', 'pywisp/sshdevice'],
    scripts = ["bin/pywisp"],
    install_requires = ['requests', 'paramiko', 'termcolor', "argparse", "configparser"],
    include_package_data = True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Environment :: Console",
        "Environment :: Web Environment",
        "Environment :: Other Environment",
    ],
)
