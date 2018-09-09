#!/usr/bin/python3
# -*- coding: utf-8 -*-

import argparse, configparser, os, pkgutil, logging
from importlib import import_module
from pprint import pprint

# Internal imports
from pyradio.wisp import Wisp
from pyradio.sshdevice import backup_devices

class Pyradio():

   # Permet mostrar l'epilog amb la llista ben formatada, mentre es 
   # mostren els arguments i els seus defaults formatats correctament
   # https://stackoverflow.com/questions/18462610/argumentparser-epilog-and-description-formatting-in-conjunction-with-argumentdef
   class MyCustomFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
      pass
   
   
   # Parses arguments and configurations
   def __init__(self, wisp=None):
         
      self.args, self.arg_parser, self.arg_sub_parser = self.parse_arguments()
      self.config, self.wisp = self.parse_configuration(self.args.conf)
      
      # Allow to create a WISP externally (useful when imported as a library)
      if wisp:
         self.wisp = wisp
   

   def parse_device(self, device):
      '''Parses a device using arguments passed to program'''
      
      if self.args.getname:
         print(device.name)
      if self.args.getid:
         print(device.id)
      if self.args.getip:
         print(device.ip)
      if self.args.getmac:
         print(device.mac)
      if self.args.getstatus:
         print(device.status)
      if self.args.getdhcp:
         pprint(device.getDHCPLeases(bound=None))
      if self.args.getwifi:
         pprint(device.getWifiStatus())
      if self.args.getwifistations:
         pprint(device.getWifiStations())
      if self.args.getjson:
         pprint(device.data)
      if self.args.url:
         print(self.wisp.ac.getDevicesURL([device.id])[0]['url'])
      if self.args.cmd:
         stdin, stdout, stderr = device.command(args.cmd)
         print(stdout.read().decode(), end="")
         print(stderr.read().decode(), end="")
      if self.args.ssh:
         device.shell()


   def parse_arguments(self, parser=argparse.ArgumentParser(formatter_class=MyCustomFormatter)):
      '''Parses arguments passed to program into a dict'''
      
      parser.add_argument("--conf", type=str,
                          default="{}/{}".format(os.getenv('HOME'), '.pyradio'),
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
      
      pprint(args)
      
      return args, parser, sp


   def parse_configuration(self, file_name):
      '''Parses configuration file into a dict/class'''
      config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
      
      wisp = None
      
      if os.path.isfile(file_name):
         
         # Populate the [env] section
         env_dict = {name: os.path.expandvars(value) for name, value in os.environ.items()}
         config.read_dict(
            {"env": env_dict},
            source='<env>')

         print("Loading", file_name)
         config.read(file_name)
         
         ac_conf = None
         if 'ac' in config:
            ac_conf = {name: value for name, value in config.items('ac')}
            print("Loaded AC configuration: ", end="")
            pprint(ac_conf)
         
         if 'wisp' in config:
            print("Detected extra class for managing wisp.")
            if 'path' in config['wisp'] and 'module' in config['wisp'] and 'class' in config['wisp']:
               print("Detected WISP: {} || {} || {}".format(config['wisp']['path'], config['wisp']['module'], config['wisp']['class']))
               path = os.path.dirname( config['wisp']['path'] )
               for (finder, name, _) in pkgutil.iter_modules([path]):
                  print("Name:", name)
                  if name == config['wisp']['module']:
                     print("Loading module {} from file '{}'...".format(config['wisp']['module'], config['wisp']['path']))
                     loader = finder.find_module(name)
                     mod = loader.load_module()
                     cls = getattr(mod, config['wisp']['class'])
                     print("Merging class {} to our WISP definition...".format(config['wisp']['class']))
                     wisp = type('Wisp' + config['wisp']['class'], (cls,Wisp), {})(ac_conf)
                     print("Wisp Class: " + type(wisp).__name__)
         else:
            wisp = Wisp()
          
      else:
         print("No config file")
      
      return config, wisp


def main():
   
   pyradio = Pyradio()
   
   # Backup everything!
   if 'backup_ac_path' in pyradio.args:
      path = pyradio.args.backup_ac_path
      if not path and 'backup' in pyradio.config and 'ac' in pyradio.config['backup']:
         path = pyradio.config['backup']['ac']
      
      retries = pyradio.args.retries
      if not retries and 'backup' in pyradio.config and 'retries' in pyradio.config['backup']:
         retries = pyradio.config['backup']['retries']
         
      print('Backup AC devices to {}'.format(path))
      backup_devices(pyradio.wisp.get_ac_devices(), path, retries=retries)
   
   elif 'backup_mt_path' in pyradio.args:
      path = pyradio.args.backup_mt_path
      if not path and 'backup' in pyradio.config and 'mt' in pyradio.config['backup']:
         path = pyradio.config['backup']['mt']
      
      retries = pyradio.args.retries
      if not retries and 'backup' in pyradio.config and 'retries' in pyradio.config['backup']:
         retries = pyradio.config['backup']['retries']
         
      print('Backup MT devices to {}'.format(path))
      backup_devices(pyradio.wisp.get_mt_devices(), path, retries=retries)
 
   # Reorder AirControl branches
   elif 'reorder_ac' in pyradio.args:
      print('Reorder branches!')
      pyradio.wisp.ac_reorder_branches()
 
   # Find host and print info about it or perform actions on it     
   elif 'host' in pyradio.args:
      # Optional lower host (insensitive)
      pyradio.args.host = pyradio.args.host.lower().strip()
      
      # Get devices
      devices = pyradio.wisp.get_host(pyradio.args.host, deep=pyradio.args.deep, from_br=pyradio.args.from_br)
      if devices == None or len(devices) == 0:
         print("[ERROR] No s'ha trobat cap dispositiu: '{}'".format(pyradio.args.host))
         return 1

      # If its not a list, convert into it
      if type(devices) is not list:
         devices = [ devices ]
      
      # Apply actions for every device found
      for device in devices:
         pyradio.parse_device(device)
   
   return 0


if __name__ == "__main__":
   exit(main())
