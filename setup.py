
from setuptools import setup, find_packages

VERSION = (0, 0, 2)
__version__ = '.'.join(map(str, VERSION))

setup(
    name = 'pyradio',
    version = __version__,
    description = "Access AirControl2, AirOS & Mikrotik",
    long_description = "Access AirControl2 (API), AirOS (SSH) & Mikrotik (SSH) from the same place",
    author = "Emilio del Giorgio",
    author_email = "https://github.com/emibcn",
    url = "https://github.com/emibcn/pyradio",
    license = "GPLv3",
    platforms = ["any"],
    packages = ['pyradio'],
    py_modules=['pyradio', 'pyradio/mikrotik', 'pyradio/aircontrol', 'pyradio/sshdevice'],
    scripts = ["bin/pyradio"],
    install_requires = ['requests', 'paramiko', 'termcolor'],
    include_package_data = True,
    classifiers = [
        "Environment :: Command line",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GPLv3 License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ],
)
