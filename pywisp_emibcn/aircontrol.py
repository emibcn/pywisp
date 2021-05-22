#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, requests, ipaddress, datetime, json
from pywisp_emibcn.sshdevice import SSHDevice

from pprint import pformat

# Disable warnings
import urllib3
urllib3.disable_warnings()

# Internal utils
def ip2int(addr):
   return int(ipaddress.IPv4Address(addr))


def int2ip(addr):
   return str(ipaddress.IPv4Address(addr))


def is_ip(addr):
   try:
      ipaddress.ip_address(addr)
   except:
      return False
   
   return True


def get_client_from_wifi_station(client_wifi):
   return {
            'deviceId': -1,
            'properties': {
               'hostname': client_wifi['remote']['hostname'] if 'remote' in client_wifi else client_wifi['name'],
               'ip': client_wifi['lastip'],
               'mac': client_wifi['mac'],
            }
         }


STATUS = ["unknown", "not monitored", "online", "offline"]

class ACDevice(SSHDevice):
   '''AirControl/Ubiquiti device class'''
   
   id      = 0
   ssid    = ""
   branch  = ""
   product = ""
   data    = {}
   
   
   def __init__(self, json, ac=None, *args, **kwargs):
      '''Set specific AirOS values'''
      
      today = datetime.date.today()
      
      if ac and 'hostname' in json['properties']:
         d = ac.getDevices(name=json['properties']['hostname'])
         if len(d) > 0:
            json = d[0]
      
      self.data = json
         
      #pprint(json)
      
      # Assign data from original device JSON
      self.id = json['deviceId']
      
      if 'hostname' in json['properties']:
         kwargs['name']        = json['properties']['hostname']
      if 'mac' in json['properties']:
         kwargs['mac'] = json['properties']['mac']
      if 'ip' in json['properties']:
         kwargs['ip'] = int2ip(json['properties']['ip'])
      if 'status' in json['properties']:
         if json['properties']['status'] in STATUS:
            kwargs['status'] = STATUS[ json['properties']['status'] ]
         else:
            kwargs['status'] = json['properties']['status']
      
      # Set specific AirOS properties
      if 'parentId' in json:
         self.branch = json['parentId']
      if 'essid' in json['properties']:
         self.ssid    = json['properties']['essid']
      if 'product' in json['properties']:
         self.product = json['properties']['product']
      
      super().__init__(*args, **kwargs)

   
   def getName(self):
      '''Get device name from the device itself'''
      
      command = 'uname -n'
      stdin, stdout, stderr = self.command(command)
      
      self.name = stdout.readline().strip()
   
   
   def setBackupName(self, backup_file=""):
      '''Append '.tar' to backup filename'''
      
      super().setBackupName(backup_file=backup_file)
      self.backup_file += ".tar"
   
   
   def backup(self, path):
      
      self.login()
      
      # No sFTP server on Ubiquiti systems. Let's do a tar.
      # Send tar command with stdout as local backup file
      files = ["/tmp/system.cfg", "/etc/persistent/rc.prestart", "/etc/persistent/rc.poststart"]
      command = 'tar -c -f - {}'.format(" ".join('"{}"'.format(f) for f in files))
      stdin, stdout, stderr = self.command(command)
      
      # Write tar command output to local tar file
      with open(path + '/' + self.backup_file, "wb") as myfile:
         myfile.write(stdout.read())
      

   def getWifiStatus(self):
      status = {}
      
      for var, value in self.data['properties'].items():
         if var.startswith('chain') or \
               var.startswith('channel') or \
               var.startswith('freq') or \
               var.startswith('essid') or \
               var.startswith('noise') or \
               var.startswith('distance') or \
               var.startswith('signal'):
            status[var] = value
      
      return status
   
   
   def getWifiStations(self):
      command = "wstalist ath0"
      stdin, stdout, stderr = self.command(command)
      
      return json.loads(stdout.read().decode())
   
   
   def __str__(self):
      return u"{} : {} - {} ({})".format(self.name, self.mac, self.ip, self.id)

   
class ACSession():
   cookies = {}
   URL_path = "/api/v1"
   URL = ""
   username = ""
   password = ""
   devices = None
   
   def __init__(self, URL, username, password):
      '''Assign login parameters'''
      self.URL = URL
      self.username = username
      self.password = password
         
   
   def login(self):
      '''Login to AirControl API server'''
      loginData = {
         'username': self.username,
         'password': self.password,
         'eulaAccepted':True,
      }
      
      # Login to server
      resp = requests.post(
         self.URL + self.URL_path + '/login', 
         json=loginData,
         headers={
            'Accept':'application/json', 
            'Content-Type':'application/json'
         },
         verify=False)
      
      # This means something went wrong.
      if resp.status_code != 200:
         raise Exception(u'GET /login/ {}: {}'.format(resp.status_code, resp.text))
      
      # Save cookies (session)
      self.cookies = resp.cookies
   
   
   def sendRequest(self, path, method="get", body={}):
      '''Send request to AirControl API server using cookies from login'''
      URL = self.URL + self.URL_path + path
      arguments = {
         'cookies':self.cookies,
         'headers': {
            'Accept':'application/json', 
            'Content-Type':'application/json'
         },
         'verify':False,
      }
      
      if method == 'get':
         resp = requests.get(URL, **arguments)
      elif method == 'post':
         resp = requests.post(URL, data=str(body), **arguments)
      elif method == 'patch':
         resp = requests.patch(URL, data=str(body), **arguments)
      
      # This means something went wrong.
      if resp.status_code > 299:
         raise Exception(u'{} {} {}: {} ({})'.format(method.upper(), path, resp.status_code, resp.text, pformat(body)))
      
      return resp
      
      
   def getDevices(self, name_starts=None, name=None, ip=None, mac=None):
      '''Get devices list, as a list of dicts (from JSON data)'''
      
      if mac is not None:
         return self.getDeviceByMac(mac)
         
      if not self.devices:
         self.devices = self.sendRequest("/devices").json()['results']
      
      if name:
         name = name.lower()
      if name_starts:
         name_starts = name_starts.lower()
      if mac:
         mac = mac.lower()
      
      if not name_starts and not name and not ip and not mac:
         result = self.devices
      else:
         result = [
            dev
            for dev in self.devices
               if ( 'properties' in dev and 'hostname' in dev['properties'] ) and \
                  (
                     (name_starts and dev['properties']['hostname'].lower().startswith(name_starts) ) or \
                     (name        and name in dev['properties']['hostname'].lower()                 ) or \
                     (mac         and mac  in dev['properties']['mac'].lower()                      ) or \
                     (ip          and ip   in int2ip(dev['properties']['ip'])                       )    \
                  ) 
         ]

      return result
   
   
   def getDeviceByMac(self, mac):
      '''Gets device by it's MAC address'''
      return self.sendRequest("/devices/mac/{}".format(mac)).json()
   
   
   def getDeviceStatus(self, id):
      '''Get device's URL'''
      req = {
         "metricSetId": 32,
         "from": 0,
         "to": 10,
         "scale": "seconds"
      }
      result = self.sendRequest("/devices/{}/metrics".format(id), method='post', body=json.dumps(req))
      return result.json()
   
   
   def getDevicesURL(self, list):
      '''Get device's URL'''
      result = self.sendRequest("/devices/webui", method='post', body=str(list))
      return result.json()['results']
   
   
   def patchDeviceCreate(self, deviceId, patchDevice):
      '''Creates single device basic properties patch'''
      
      acceptedMods = {
          "type": str,
          "ip": str,
          "domainName": str,
          "sshUserName": str,
          "sshPassword": str,
          "sshPort": int,
          "rememberSshSettings": bool,
          "httpPort": int,
          "useHttps": bool,
          "description": str,
          "tag": str,
          "parentId": int,
          "uplinkType": int,
          "overriddenServerAddress": {
            "ip": str,
            "port": int
          },
          "membershipTypeGateway": bool,
          "runDiscovery": bool,
          "lockPositionInTopology": bool,
          "lockIpAddress": bool,
          "connectedDirectly": bool,
          "sessionId": int,
          "deviceId": int
      }
      
      patch = {}
      for name,value in acceptedMods.items():
         if name in patchDevice and value == type(patchDevice[name]):
            patch[name] = patchDevice[name]
      
      patch['deviceId'] = deviceId
      
      return patch


   def patchDeviceList(self, patchList):
      '''Patch devices list basic properties'''
      
      return self.sendRequest(
                         "/devices/basic-properties", 
                         method='patch', 
                         body=json.dumps( patchList ))


   def patchDevice(self, deviceId, patchDevice):
      '''Patch device basic properties'''
      
      return self.patchDeviceList( [self.patchDeviceCreate(deviceId, patchDevice)] )
   
   
