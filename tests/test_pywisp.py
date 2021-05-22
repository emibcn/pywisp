#!/usr/bin/python3
# -*- coding: utf-8 -*-

from pywisp_emibcn.pywisp import PyWisp
from pywisp_emibcn.wisp import Wisp
from pywisp_emibcn.mikrotik import MTDevice

# Create a WISP Mixin
class MyWisp(Wisp):
   def get_host(self, name, deep=False, from_br=None):
      if type(name) != list:
         name = [name]
      return [MTDevice({}, username="admin", password="PASSWORD", ip=n, name=n) for n in name]

# Instantiate the WISP and PyWisp
pywisp = PyWisp()
pywisp.wisp = MyWisp(ac_conf={
      "url": "https://localhost:9082",
      "user": "admin",
      "password": "admin",
}, getlog=pywisp.setup_logger)

# Create some phantom arguments
pywisp.args.host = "10.255.255.2"
pywisp.args.getip = True

# Get devices
device = pywisp.wisp.get_host(pywisp.args.host)
assert device != None, 'get_host should have returned a list or a device'
assert len(device), 'get_host should have returned a list with at least one device'

# Test `get_ip` output
def test_parse_device(capsys):
    pywisp.parse_device(device[0])
    captured = capsys.readouterr()
    assert captured.out == pywisp.args.host + "\n"

