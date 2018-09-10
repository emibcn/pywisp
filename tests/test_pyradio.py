#!/usr/bin/python3
# -*- coding: utf-8 -*-

from pyradio.pyradio import Pyradio
from pyradio.wisp import Wisp
from pyradio.mikrotik import MTDevice

# Create a WISP Mixin
class MyWisp(Wisp):
   def get_host(self, name, deep=False, from_br=None):
      if type(name) != list:
         name = [name]
      return [MTDevice({}, username="admin", password="PASSWORD", ip=n, name=n) for n in name]

# Instantiate the WISP and PyRadio
pyradio = Pyradio()
pyradio.wisp = MyWisp(ac_conf={
      "url": "https://localhost:9082",
      "user": "admin",
      "password": "admin",
}, getlog=pyradio.setup_logger)

# Create some phantom arguments
pyradio.args.host = "10.255.255.2"
pyradio.args.getip = True

# Get devices
device = pyradio.wisp.get_host(pyradio.args.host)
assert device != None, 'get_host should have returned a list or a device'
assert len(device), 'get_host should have returned a list with at least one device'

# Test `get_ip` output
def test_parse_device(capsys):
    pyradio.parse_device(device[0])
    captured = capsys.readouterr()
    assert captured.out == pyradio.args.host + "\n"

