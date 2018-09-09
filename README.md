# Pyradio installation
## Install pyradio
```shell
pip install --user git+https://github.com/emibcn/pyradio.git
```

## Configure pyradio
Then configure as per [~/.pyradio](#Pyradio config file: `~/.pyradio`)

Finally, create the python script which implements the WISP infrastructure and authentication
mechanisms, as per [wisp.py](#WISP infrastructure and host authentication definitions `${env:HOME}/MyWISP/wisp.py`)

# Pyradio usage
```
usage: pyradio [-h] [--conf CONF] {backup_ac,backup_mt,reorder_ac,host} ...

positional arguments:
  {backup_ac,backup_mt,reorder_ac,host}
    backup_ac           Backup all AirControl devices
    backup_mt           Backup all Mikrotik devices
    reorder_ac          Reorder branches from AirControl devices
    host                Find device by it's hostname, MAC or IP

optional arguments:
  -h, --help            show this help message and exit
  --conf CONF           Reads configuration from this file instead of default
                        (default: /home/emi/.pyradio)
```


```
usage: pyradio backup_ac [-h] [--retries] [PATH]

positional arguments:
  PATH        Directory in which save backup files (default: None)

optional arguments:
  -h, --help  show this help message and exit
  --retries   Retries for every device before stop trying (default: 3)
```


```
usage: pyradio backup_mt [-h] [--retries] [PATH]

positional arguments:
  PATH        Directory in which save backup files (default: None)

optional arguments:
  -h, --help  show this help message and exit
  --retries   Retries for every device before stop trying (default: 3)
```


```
usage: pyradio host [-h] [--deep] [--from-br FROM_BR] [--getname] [--getjson]
                    [--getip] [--getid] [--getmac] [--getdhcp] [--getwifi]
                    [--getwifistations] [--getstatus] [--url] [--ssh]
                    [--cmd CMD]
                    host

positional arguments:
  host               Devices hostname, MAC or IP

optional arguments:
  -h, --help         show this help message and exit
  --deep             Find device by it's hostname, MAC or IP, using all BRs
                     station list as haystack (default: False)
  --from-br FROM_BR  Deep find only in this BR (default: None)
  --getname          Gets device name (default: False)
  --getjson          Gets device full data (default: False)
  --getip            Gets device IP (default: False)
  --getid            Gets device ID (default: False)
  --getmac           Gets device MAC (default: False)
  --getdhcp          Gets device's DHCP leases/stations (default: False)
  --getwifi          Gets device's wifi status (default: False)
  --getwifistations  Gets device's wifi stations (default: False)
  --getstatus        Gets device status (default: False)
  --url              Gets an authenticated URL to connect to the device using
                     browser (default: False)
  --ssh              Connects to device using SSH (default: False)
```



# Pyradio config file: `~/.pyradio`
```
[wisp]
path = ${env:HOME}/MyWISP/
module = wisp
class = MyWISP

[ac]
url = https://10.100.1.102:9082
user = admin
password = MyNotSoSecurePassword

[backup]
ac = /tmp/meswifi/ac/
mt = /tmp/meswifi/mt/
```

# WISP infrastructure and host authentication definitions `${env:HOME}/MyWISP/wisp.py`
```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

# Internal imports
from pyradio.aircontrol import ACDevice, int2ip, is_ip
from pyradio.mikrotik import MTDevice
from pyradio.sshdevice import backup_devices

ID_RSA = os.getenv('HOME') + "/.ssh/id_rsa.mw"
PASSWORD = "MyNotSoSecurePassword"
PASSWORD_CLIENT = "MyNotSoSecurePasswordForClients"

class MyWISP():
   '''pyradio.Wisp mixin implementation'''
   
   def get_ac_devices(self, devices=[]):
      '''Generate antennas list (with credentials)'''
      antenas = []
      for dev in devices:
         password = PASSWORD
         
         if 'hostname' in dev['properties'] and dev['properties']['hostname'].startswith('AF'):
            password = password[:8]
         
         antenas.append(ACDevice(dev, username='admin', password=password, rsa=ID_RSA))
      
      return antenas


   def get_ac_brs(self, from_br=None):
      '''Generate antennas list (with credentials) only of BRs'''
      if from_br is None:
         repetidors = self.ac.getDevices(name_starts="br")
      else:
         repetidors = self.ac.getDevices(name=frombr)
      
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
      return self.get_aps()


   def get_aps_ips(self):
      return [
            "10.111.0." + str(num) 
            for num in [5, 6, 7, 8, 9, 13, 14, 16, 17, 18, 19, 20, 26]
         ]


   def get_aps(self):
      return [
         MTDevice({}, ip=ip, username='admin', password=PASSWORD, rsa=ID_RSA)
         for ip in self.get_aps_ips()
      ]

   def get_host(self, name, deep=False, from_br=None):
   
      # Per IP
      if is_ip(name) and name in self.get_aps_ips():
            return [MTDevice({}, username="admin", password=PASSWORD, ip=name, rsa=ID_RSA)]

      # Aircontrol
      else:
         
         # Get devices list
         if not deep:
            clients = self.ac.getDevices(name=name)
         else:
            clients = self.get_aircontrol_deep(name, frombr)
         
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

```