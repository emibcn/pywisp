![Coverage](https://raw.githubusercontent.com/emibcn/pywisp/badges/master/test-coverage.svg)
[![Python CI](https://github.com/emibcn/pywisp/actions/workflows/test.yml/badge.svg)](https://github.com/emibcn/pywisp/actions/workflows/test.yml)
[![Build Status](https://travis-ci.com/emibcn/pywisp.svg?branch=master)](https://travis-ci.com/emibcn/pywisp)


# PyWisp installation
## Install pywisp
```shell
pip3 install --user pywisp_emibcn
```

## Configure PyWisp
Then configure as per [~/.pywisp](#pywisp-config-file-pywisp)

Finally, create the python script which implements the WISP infrastructure and authentication
mechanisms, as per [wisp.py](#wisp-infrastructure-and-host-authentication-definitions)

# PyWisp usage
```
usage: pywisp [-h] [--conf CONF] {backup_ac,backup_mt,reorder_ac,host} ...

positional arguments:
  {backup_ac,backup_mt,reorder_ac,host}
    backup_ac           Backup all AirControl devices
    backup_mt           Backup all Mikrotik devices
    reorder_ac          Reorder branches from AirControl devices
    host                Find device by it's hostname, MAC or IP

optional arguments:
  -h, --help            show this help message and exit
  --conf CONF           Reads configuration from this file instead of default
                        (default: $HOME/.pywisp)
```


### Backup all Ubiquiti's devices
```
usage: pywisp backup_ac [-h] [--retries] [PATH]

positional arguments:
  PATH        Directory in which save backup files (default: None)

optional arguments:
  -h, --help  show this help message and exit
  --retries   Retries for every device before stop trying (default: 3)
```

### Backup all Mikrotik's devices
```
usage: pywisp backup_mt [-h] [--retries] [PATH]

positional arguments:
  PATH        Directory in which save backup files (default: None)

optional arguments:
  -h, --help  show this help message and exit
  --retries   Retries for every device before stop trying (default: 3)
```

### Host lookup and actions
```
usage: pywisp host [-h] [--deep] [--from-br FROM_BR] [--getname] [--getjson]
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
  --cmd CMD          Connects to device and run a command (default: None)
```


# PyWisp config file: `~/.pywisp`
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
ac = /var/backups/mywisp/ac/
mt = /var/backups/mywisp/mt/
```

# WISP infrastructure and host authentication definitions
## `${env:HOME}/MyWISP/wisp.py`
In [this example](/examples/Wisp_1.py), we hardcode relations between IPs, some device names, users and passwords. We could be getting those relations from where ever, for example, an SQL database, a secure wallet downloaded from an S3, an spreadsheet at GoogleDocs (sic), an internal REST API, etc. Examples are welcome via pull request.

You can add more types of devices (for example, Mimosa) subclassing [`SSHDevice`](/pywisp_emibcn/sshdevice.py) and instantiating it correctly from your `wisp.py`. If you do so, I appreciate pull requests ;) 

You can create a complete subclassed [`Wisp`](/pywisp_emibcn/wisp.py) object and pass it to `PyWisp` on instantiation. This way you can use PyWisp from within other projects, like from your Django APP or from your Zabbix scripts, mantaining your infrastructure and authentication mechanisms centralized.


# TODO list
- [x] Move `print`s and similars to a ~~good~~ logging system.
- [ ] Enhance logging system
- [x] Create examples repo with one `wisp.py` example
- [ ] Create more examples (useful for testing, too)
- [ ] Create more and useful documentation
- [x] Testing
- [ ] Testing, testing, testing...
