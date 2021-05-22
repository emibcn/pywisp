#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pywisp_emibcn.sshdevice import SSHDevice

STATUS = {
   "bound": "online",
   "waiting": "offline",
}

class MTDevice(SSHDevice):
   '''Mikrotik device class'''
   
   product = ""
   data    = {}
   
   
   def __init__(self, data, *args, **kwargs):
      '''Set specific Mikrotik values'''
      
      if 'host-name' in data:
         kwargs['name'] = data['host-name']
      if 'address' in data:
         kwargs['ip'] = data['address']
      if 'mac-address' in data:
         kwargs['mac'] = data['mac-address']
      if 'status' in data:
         kwargs['status'] = STATUS[data['status']]
      
      # Save original data
      self.data = data
      
      super().__init__(*args, **kwargs)
      
   
   def backup(self, path):
      '''Backup Mikrotik device config'''
      self.login()
      
      # Use MT export tool
      stdin, stdout, stderr = self.command("/export")
      
      # Save stdout to backup file
      with open(path + '/' + self.backup_file, "wb") as myfile:
         myfile.write(stdout.read())
   
   
   def parse_list(self, stdout):
      '''Parses a tipical 'terse' Mikrotik list'''
      
      # Consume first line (column titles, flags)
      lines = [""]
      index = 0
      
      # Put every item info into a line
      for line in stdout.readlines():
         # Primera línia d'un element
         if line.strip() == "":
            lines.append("")
            index = len(lines) - 1
            continue
         
         lines[index] += line.strip() + " "
      
      # Remove last empty line
      del lines[index]
      
      # Parse each line into a dict
      list = []
      for line in lines:
         variables = line.split()
         
         element = {}
         for variable in variables:
            if '=' in variable:
               var_val = variable.split('=', 1)
               element[var_val[0]] = var_val[1].strip('"')
            elif variable.isdigit():
               element['index'] = variable
         
         if len(element) > 0:
            list.append(element)
      
      del lines
      
      return list
   
   
   def parse_values(self, stdout):
      '''Parses a tipical 'variable: value' list'''
      
      element = {}
      for line in stdout:
         
         var_val = [x.strip() for x in line.strip().split(":", 1)]
         
         if len(var_val) < 2:
            continue
         
         while var_val[1][-1] == ',':
            var_val[1] += stdout.readline().strip()
         
         element[ var_val[0].strip() ] = var_val[1].strip()
      
      return element
   
   
   def getName(self):
      command = ':global idt [/system identity get name]; :put $idt;'
      stdin, stdout, stderr = self.command(command)
      
      self.name = stdout.readline().strip()
   
   
   def getDHCPLeases(self, name="", bound=True):
      
      command = '/ip dhcp-server lease print detail without-paging'
      where = ""
      
      # Filter by host-name with a regexp
      if name != "":
         where += ' host-name~"{}"'.format(name)
      
      # Filter (un)bound devices
      if bound != None:
         where += ' status{}=bound'.format('' if bound else '!')
      
      # Add filters to command
      if where != "":
         command += ' where' + where
      
      #stdin, stdout, stderr = self.command(":put \"" + command + "\"")
      stdin, stdout, stderr = self.command(command)
      
      return self.parse_list(stdout)
   

   def getWifiStatus(self):
      command = '/interface wireless registration-table print without-paging'
      command = "/interface wireless monitor 0 once"
      stdin, stdout, stderr = self.command(command)
      
      
      return self.parse_values(stdout)
