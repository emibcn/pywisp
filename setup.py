
from setuptools import setup, find_packages

VERSION = (0, 0, 3)
__version__ = '.'.join(map(str, VERSION))

setup(
    name = 'pywisp',
    version = __version__,
    description = "Access AirControl2, AirOS & Mikrotik",
    long_description = "Access AirControl2 (API), AirOS (SSH) & Mikrotik (SSH) from the same place",
    author = "Emilio del Giorgio",
    author_email = "https://github.com/emibcn",
    url = "https://github.com/emibcn/pywisp",
    license = "GPLv3",
    platforms = ["any"],
    packages = ['pywisp'],
    py_modules=['pywisp', 'pywisp/mikrotik', 'pywisp/aircontrol', 'pywisp/sshdevice'],
    scripts = ["bin/pywisp"],
    install_requires = ['requests', 'paramiko', 'termcolor', "argparse", "configparser"],
    include_package_data = True,
    classifiers = [
        "Environment :: Command line",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GPLv3 License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ],
)
