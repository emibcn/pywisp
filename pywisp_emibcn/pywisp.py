#!/usr/bin/python3
# -*- coding: utf-8 -*-

import argparse, configparser, os, pkgutil, logging
from importlib import import_module
from pprint import pprint

# Internal imports
from pywisp_emibcn.wisp import Wisp
from pywisp_emibcn.sshdevice import backup_devices

class PyWisp():

    log = None
    args = None
    arg_parser = None
    args_sub_parser = None
    config = None
    wisp = None

    # Permet mostrar l'epilog amb la llista ben formatada, mentre es
    # mostren els arguments i els seus defaults formatats correctament
    # https://stackoverflow.com/questions/18462610/argumentparser-epilog-and-description-formatting-in-conjunction-with-argumentdef
    class MyCustomFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
        pass


    def __init__(self, wisp=None):
        '''Parses arguments and configurations'''

        self.log = self.setup_logger()

        self.args, self.arg_parser, self.arg_sub_parser = self.parse_arguments()
        self.config, self.wisp = self.parse_configuration(self.args.conf)

        # Allow to create a WISP externally (useful when imported as a library)
        if wisp:
            self.wisp = wisp


    def setup_logger(self, name=__name__):
        '''Setup a logger'''
        class OneLineExceptionFormatter(logging.Formatter):
             def formatException(self, exc_info):
                  result = super().formatException(exc_info)
                  return repr(result)

             def format(self, record):
                  result = super().format(record)
                  if record.exc_text:
                        result = result.replace("n", "")
                  return result

        handler = logging.StreamHandler()
        formatter = OneLineExceptionFormatter(logging.BASIC_FORMAT)
        handler.setFormatter(formatter)
        log = logging.getLogger(name)
        log.setLevel(os.environ.get("LOGLEVEL", "INFO"))
        log.addHandler(handler)

        return log


    def parse_device(self, device):
        '''Parses a device using arguments passed to program'''

        if 'getname' in self.args and self.args.getname:
            print(device.name)
        if 'getid' in self.args and self.args.getid:
            print(device.id)
        if 'getip' in self.args and self.args.getip:
            print(device.ip)
        if 'getmac' in self.args and self.args.getmac:
            print(device.mac)
        if 'getstatus' in self.args and self.args.getstatus:
            print(device.status)
        if 'getdhcp' in self.args and self.args.getdhcp:
            pprint(device.getDHCPLeases(bound=None))
        if 'getwifi' in self.args and self.args.getwifi:
            pprint(device.getWifiStatus())
        if 'getwifistations' in self.args and self.args.getwifistations:
            pprint(device.getWifiStations())
        if 'getjson' in self.args and self.args.getjson:
            pprint(device.data)
        if 'url' in self.args and self.args.url:
            print(self.wisp.ac.getDevicesURL([device.id])[0]['url'])
        if 'cmd' in self.args and self.args.cmd:
            stdin, stdout, stderr = device.command(args.cmd)
            print(stdout.read().decode(), end="")
            print(stderr.read().decode(), end="")
        if 'ssh' in self.args and self.args.ssh:
            device.shell()


    def parse_arguments(self, parser=argparse.ArgumentParser(formatter_class=MyCustomFormatter)):
        '''Parses arguments passed to program into a dict'''

        parser.add_argument("--conf", type=str,
                                  default="{}/{}".format(os.getenv('HOME'), '.pywisp'),
                                  help="Reads configuration from this file instead of default")

        sp = parser.add_subparsers()

        b_ac = sp.add_parser("backup_ac",formatter_class=self.MyCustomFormatter,
                                  help="Backup all AirControl devices")
        b_ac.add_argument("backup_ac_path", type=str, nargs='?',metavar="PATH",
                                  help="Directory in which save backup files")
        b_ac.add_argument("--retries",
                                  action="store_true", default=3,
                                  help="Retries for every device before stop trying")

        b_mt = sp.add_parser("backup_mt",formatter_class=self.MyCustomFormatter,
                                  help="Backup all Mikrotik devices")
        b_mt.add_argument("backup_mt_path", type=str, nargs='?',metavar="PATH",
                                  help="Directory in which save backup files")
        b_mt.add_argument("--retries",
                                  action="store_true", default=3,
                                  help="Retries for every device before stop trying")

        reorder = sp.add_parser("reorder_ac",formatter_class=self.MyCustomFormatter,
                                  help="Reorder branches from AirControl devices")

        host_parser = sp.add_parser("host", formatter_class=self.MyCustomFormatter,
                                  help="Find device by it's hostname, MAC or IP")
        host_parser.add_argument("host", type=str,
                                  help="Devices hostname, MAC or IP")

        host_parser.add_argument("--deep",
                                  action="store_true",
                                  help="Find device by it's hostname, MAC or IP, using all BRs station list as haystack")
        host_parser.add_argument("--from-br", type=str,
                                  help="Deep find only in this BR")

        host_parser.add_argument("--getname",
                                  action="store_true",
                                  help="Gets device name")
        host_parser.add_argument("--getjson",
                                  action="store_true",
                                  help="Gets device full data")
        host_parser.add_argument("--getip",
                                  action="store_true",
                                  help="Gets device IP")
        host_parser.add_argument("--getid",
                                  action="store_true",
                                  help="Gets device ID")
        host_parser.add_argument("--getmac",
                                  action="store_true",
                                  help="Gets device MAC")
        host_parser.add_argument("--getdhcp",
                                  action="store_true",
                                  help="Gets device's DHCP leases/stations")
        host_parser.add_argument("--getwifi",
                                  action="store_true",
                                  help="Gets device's wifi status")
        host_parser.add_argument("--getwifistations",
                                  action="store_true",
                                  help="Gets device's wifi stations")
        host_parser.add_argument("--getstatus",
                                  action="store_true",
                                  help="Gets device status")
        host_parser.add_argument("--url",
                                  action="store_true",
                                  help="Gets an authenticated URL to connect to the device using browser")

        host_parser.add_argument("--ssh",
                                  action="store_true",
                                  help="Connects to device using SSH")
        host_parser.add_argument("--cmd", type=str,
                                  help="Connects to device and run a command")

        args = parser.parse_args()

        self.log.debug('Arguments: %s' % args)

        return args, parser, sp


    def parse_configuration(self, file_name):
        '''Parses configuration file into a dict/class'''
        config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())

        wisp = None
        wisp_conf = {'getlog': self.setup_logger}

        if os.path.isfile(file_name):

            # Populate the [env] section
            env_dict = {name: os.path.expandvars(value.replace('$', '$$')) for name, value in os.environ.items()}
            config.read_dict(
                {"env": env_dict},
                source='<env>')

            self.log.debug("Loading %s" % file_name)
            config.read(file_name)

            wisp_conf['ac_conf'] = None
            if 'ac' in config:
                wisp_conf['ac_conf'] = {name: value for name, value in config.items('ac')}
                self.log.debug("Loaded AC configuration:  %s" % wisp_conf['ac_conf'])

            if 'wisp' in config:
                self.log.debug("Detected extra class for managing wisp.")

                if 'path' in config['wisp'] and 'module' in config['wisp'] and 'class' in config['wisp']:
                    self.log.debug("Detected WISP: %s || %s || %s" % (config['wisp']['path'], config['wisp']['module'], config['wisp']['class']))
                    path = os.path.dirname( config['wisp']['path'] )

                    for (finder, name, _) in pkgutil.iter_modules([path]):
                        if name == config['wisp']['module']:
                            self.log.debug("Loading module %s from file '%s'..." % (config['wisp']['module'], config['wisp']['path']))
                            loader = finder.find_module(name)
                            mod = loader.load_module()
                            cls = getattr(mod, config['wisp']['class'])

                            self.log.debug("Merging class %s to our WISP definition..." % config['wisp']['class'])
                            wisp = type('Wisp' + config['wisp']['class'], (cls,Wisp), {})(**wisp_conf)
                            self.log.debug("Wisp Class: %s" % type(wisp).__name__)
            else:
                wisp = Wisp(**wisp_conf)

        else:
            self.log.warning("No config file")

        return config, wisp


def main():

    pywisp = PyWisp()

    # Backup everything!
    if 'backup_ac_path' in pywisp.args:
        path = pywisp.args.backup_ac_path
        if not path and 'backup' in pywisp.config and 'ac' in pywisp.config['backup']:
            path = pywisp.config['backup']['ac']

        retries = pywisp.args.retries
        if not retries and 'backup' in pywisp.config and 'retries' in pywisp.config['backup']:
            retries = pywisp.config['backup']['retries']

        pywisp.log.debug('Backup AC devices to %s' % (path))
        backup_devices(pywisp.wisp.get_ac_devices(), path, retries=retries)

    elif 'backup_mt_path' in pywisp.args:
        path = pywisp.args.backup_mt_path
        if not path and 'backup' in pywisp.config and 'mt' in pywisp.config['backup']:
            path = pywisp.config['backup']['mt']

        retries = pywisp.args.retries
        if not retries and 'backup' in pywisp.config and 'retries' in pywisp.config['backup']:
            retries = pywisp.config['backup']['retries']

        pywisp.log.debug('Backup MT devices to %s' % (path))
        backup_devices(pywisp.wisp.get_mt_devices(), path, retries=retries)

    # Reorder AirControl branches
    elif 'reorder_ac' in pywisp.args:
        pywisp.log.debug('Reorder branches!')
        pywisp.wisp.ac_reorder_branches()

    # Find host and print info about it or perform actions on it
    elif 'host' in pywisp.args:
        # Optional lower host (insensitive)
        pywisp.args.host = pywisp.args.host.lower().strip()

        # Get devices
        devices = pywisp.wisp.get_host(pywisp.args.host, deep=pywisp.args.deep, from_br=pywisp.args.from_br)
        if devices == None or len(devices) == 0:
            pywisp.log.error("No devices found: '%s'" % (pywisp.args.host))
            return 1

        # If its not a list, convert into it
        if type(devices) is not list:
            devices = [ devices ]

        # Apply actions for every device found
        for device in devices:
            pywisp.parse_device(device)

    return 0


if __name__ == "__main__":
    exit(main())
