#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
WISP declaration example

In this example, we hardcode relations between IPs, some device names,
users and passwords, while using some tools from AirControl or from
devices DHCP servers.
'''

import os

# Internal imports
from pyradio.aircontrol import ACDevice, int2ip, is_ip
from pyradio.mikrotik import MTDevice
from pyradio.sshdevice import backup_devices

ID_RSA = os.getenv('HOME') + "/.ssh/id_rsa.mw"
PASSWORD = "MyNotSoSecurePassword"
PASSWORD_CLIENT = "MyNotSoSecurePasswordForSomeClients"

class MyWifi():
   '''pyradio.Wisp mixin implementation'''
   
   def get_ac_devices(self, devices=[]):
      '''Generate antennas list (with credentials)'''
      antenas = []
      for dev in devices:
         password = PASSWORD
         
         # Bug AF old
         if 'hostname' in dev['properties'] and dev['properties']['hostname'].startswith('AF'):
            password = password[:8]
         
         antenas.append(ACDevice(dev, username='admin', password=password, rsa=ID_RSA))
      
      return antenas


   def get_ac_brs(self, from_br=None):
      '''Generate antennas list (with credentials) only of BRs'''
      if from_br is None:
         repetidors = self.ac.getDevices(name_starts="br")
      else:
         repetidors = self.ac.getDevices(name=from_br)
      
      repes = []
      for repetidor in repetidors:
         try:
            repes.append( ACDevice(repetidor, username='admin', password=PASSWORD, rsa=ID_RSA) )
         except (KeyboardInterrupt, SystemExit):
            raise
         except Exception as e:
            print("Hi ha hagut un problema connectant amb {}: {}".format(repe.name, str(e)))
            continue
      return repes
   
      
   def get_mt_devices(self):
      '''Generate antennas list (with credentials)'''
      
      # Get VACCs from CCR
      antenas, ccr = self.get_dhcp_clients_from_ccr_ip("10.255.255.7", password_ccr=PASSWORD, password_devices=PASSWORD_CLIENT, find="^VACC.*")
      print("CCR: {ccr} (VACCs): {count} VACCs".format(ccr=str(ccr), count=str(len(antenas))))

      # Get RTs from all CCRs, ans save CCRs list
      ccrs = []
      for ccr_ip in self.get_ccrs_ips(): 
         antenas_ccr, ccr = self.get_dhcp_clients_from_ccr_ip(ccr_ip, password_ccr=PASSWORD, password_devices=PASSWORD, find=".*-RT")
         print("CCR: {ccr}: {count} RTs".format(ccr=str(ccr), count=len(antenas_ccr)))
         
         if len(antenas_ccr) > 0:
            antenas += antenas_ccr
         
         ccrs.append(ccr)
         
      # Add CCRs   
      antenas += ccrs

      # Add APs from OtherWISP
      antenas += self.get_otherwisp_aps()

      return antenas
      

   def get_host(self, name, deep=False, from_br=None):
   
      # Per IP
      if is_ip(name):
         if name in self.get_ccrs_ips():
            return [MTDevice({}, username="admin", password=PASSWORD, ip=name, rsa=ID_RSA)]

      # OtherWISP
      if name.startswith('vacc'):
         devices, ccr = self.get_dhcp_clients_from_ccr_ip("10.255.255.7", password_ccr=PASSWORD, password_devices=PASSWORD_CLIENT, find="^{}.*".format(name.upper()) )
         
         return devices

      # CCRs
      if name.startswith('ccr'):
         
         return self.get_ccrs()
         
      # Repetidors de client (MT)
      elif name.endswith('-rt'):
         
         return self.get_rts(name, self.get_ccrs())

      # Aircontrol
      else:
         
         # Get devices list
         if not deep:
            clients = self.ac.getDevices(name=name)
         else:
            clients = self.get_aircontrol_deep(name, from_br)
         
         # Find device
         devices = []
         for client in clients:
            
            # Bug AF old
            if client['properties']['hostname'].startswith('AF'):
               password = PASSWORD[:8]
            else:
               password = PASSWORD
            
            print("Descarreguem {} - {}".format(client['properties']['hostname'], client['properties']['mac']))
            devices.append(ACDevice(client, username='admin', password=password, rsa=ID_RSA))

         return devices

      return []


   def get_dhcp_clients_from_ccr(self, ccr, password_ccr="", password_devices="", find=""):
      '''Connects to a CCR and gets a filtered list of its DHCP leases'''

      # Get leases list
      clients = ccr.getDHCPLeases(name=find, bound=None)
      
      # Generate antennas list (with credentials)
      devices = [
         MTDevice(client, username='admin', password=password_devices, rsa=ID_RSA)
         for client in clients
      ]
      
      # Return antenas list and CCR
      return devices


   def get_dhcp_clients_from_ccr_ip(self, ip, password_ccr="", password_devices="", find=""):
      # Connect to CCR
      ccr = MTDevice({}, username="admin", password=password_ccr, ip=ip, rsa=ID_RSA)
      return self.get_dhcp_clients_from_ccr(ccr, password_ccr=password_ccr, password_devices=password_devices, find=find), ccr

   def get_otherwisp_aps_ips(self):
      return [
            "10.111.0." + str(num) 
            for num in [5, 6, 7, 8, 9, 13, 14, 16, 17, 18, 19, 20, 26]
         ]


   def get_otherwisp_aps(self):
      return [
         MTDevice({}, ip=ip, username='admin', password=PASSWORD, rsa=ID_RSA)
         for ip in self.get_otherwifi_aps_ips()
      ]

   def get_ccrs_ips(self):
      return ["10.255.255." + str(num) for num in [2, 3, 4, 5, 6, 7, 8, 9, 254] ]


   def get_ccrs(self):
      return [
         MTDevice({}, username='admin', password=PASSWORD, rsa=ID_RSA, ip=ip)
         for ip in self.get_ccrs_ips()
      ]


   def get_rts(self, name, ccrs):
      '''Get RTs from all CCRs, ans save CCRs list'''
      devices = []
      for ccr in ccrs:
         devices_ccr = self.get_dhcp_clients_from_ccr(ccr, password_ccr=PASSWORD, password_devices=PASSWORD, find=".*{}-RT".format(name[:-3]))
         
         if len(devices_ccr) > 0:
            devices += devices_ccr
      
      return devices
