#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pywisp_emibcn.aircontrol import ACSession
from pprint import pprint

class Wisp():
   '''WISP interface to define infrastructure and host matching and authentication mechanisms'''
   
   ac_conf = {
      "url": "https://localhost:9082",
      "user": "admin",
      "password": "admin",
   }
   __ac = None
   __log = None
   __getlogger = None

   def __init__(self, ac_conf=None, getlog=None):
   
      if getlog:
         self.getlogger = getlog
         
      if ac_conf:
         self.ac_conf = ac_conf
         self.log.debug("__init__: Loaded AC configuration: %s" % (self.ac_conf) )

   @property
   def log(self):
      if not self.__log:
         self.__log = self.getlogger(__name__)

      return self.__log

   @log.setter
   def log(self, log):
      self.__log = log

   @property
   def getlogger(self):
      if not self.__getlogger:
         noop = lambda x, y: x
         return lambda name: type('fakelogger', (object,), {'error': print, 'warning': print, 'info': noop, 'debug': noop})()

      return self.__getlogger

   @getlogger.setter
   def getlogger(self, getlogger):
      self.__getlogger = getlogger
      self.log = None


   @property 
   def ac(self):
   
      if not self.__ac:
         self.__ac = ACSession(self.ac_conf['url'], self.ac_conf['user'], self.ac_conf['password'])
         self.__ac.login()
      
      return self.__ac

   @ac.setter
   def ac(self, ac):
      self.__ac = ac

      
   def get_host(self, name, deep=False, from_br=None):
      raise NotImplementedError("Should have implemented `get_host` method")


   def get_ac_devices(self):
      '''Generate antennas list (with credentials)'''
      raise NotImplementedError("Should have implemented `get_ac_devices` method")

   
   def get_ac_brs(self):
      '''Generate antennas list (with credentials) only of BRs'''
      raise NotImplementedError("Should have implemented `get_ac_brs` method")

   
   def get_mt_devices(self):
      '''Generate antennas list (with credentials)'''
      raise NotImplementedError("Should have implemented `get_mt_devices` method")


   def get_aircontrol_deep(self, name, from_br=None):
      self.log.info("Download BRs...")
      
      repetidors = self.get_ac_brs(from_br=None)
      
      self.log.info("BRs found: %s" % (len(repetidors)))

      clients_total = []
      clients_wifi = []
      for repetidor in repetidors:
         try:
            self.log.info("Download wifi stations from %s" % (repe.name))
            clients_wifi = repetidor.getWifiStations()
         except (KeyboardInterrupt, SystemExit):
            raise
         except Exception as e:
            self.log.warning("There was a problem connecting to %s: %s" % (repe.name, str(e)))
            continue
         
         clients = [
            {
               'deviceId': -1,
               'properties': {
                  'hostname': cw['remote']['hostname'],
                  'ip': cw['lastip'],
                  'mac': cw['mac'],
               }
            }
            for cw in clients_wifi
               if not name or \
                  (
                     name in cw['mac'].lower() or \
                     name in cw['lastip'] or \
                     ('remote' in cw and name in cw['remote']['hostname'].lower())
                  )
         ]
         
         for client in clients:
            self.log.info("%s - %s - %s" % (client['properties']['hostname'], client['properties']['mac'], client['properties']['ip']))
         
         clients_total += clients
      
      
      return clients_total


   
   def ac_reorder_branches(self):
      # Get devices list
      devices = self.get_ac_devices( self.ac.getDevices() )
      
      # Separate BRs and the rest of clients
      brs = []
      clients = []
      for antena in antenas:
         if antena.data['properties']['wlanOpModeString'] != 'sta':
            brs.append(antena)
         else:
            clients.append(antena)

      # For each BR
      done = 0
      patchList = []
      for br in brs:
         self.log.info("- %s (%s)" % (br.name, br.id))
         # For each client connectetd to it's SSID
         for client in clients:
            if client.ssid == br.ssid:
               if client.branch == br.id:
                  self.log.info("   - %s (%s)" % (client.name, client.ssid))
               else:
                  done += 1
                  self.log.info("   - Move {client} ({clid} - {clessid}) from {branch} to {brname} ({brid})".format(
                     client=client.name, 
                     clid=client.id, 
                     clessid=client.ssid, 
                     branch=client.branch, 
                     brname=br.name, 
                     brid=br.id))
                  
                  patchList.append(
                     self.ac.patchDeviceCreate(client.id, {"parentId": br.id})
                  )

      # Send patches
      self.ac.patchDeviceList(patchList)

      self.log.info("Done: %d" % (done + 1))
