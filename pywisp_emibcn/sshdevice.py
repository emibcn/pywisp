#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime, paramiko, base64, os, socket
from termcolor import colored
from pprint import pprint
try:
    import interactive
except ImportError:
    from . import interactive


class SSHDevice:

    ip         = ""
    mac        = ""
    __name    = ""
    username = ""
    password = ""
    rsa        = ""
    status    = ""
    backup_file_base = ""

    client = False

    def __init__(self, ip="", mac="", name="", username="", password="", rsa="", status="", backup_file=""):

        # Set minimal device data
        self.ip         = ip
        self.mac        = mac
        self.name      = name
        self.username = username
        self.password = password
        self.rsa        = rsa
        self.status    = status
        self.backup_file_base = backup_file

    # Use setters anf getters for properties needing expensive actions
    @property
    def name(self):
        if not self.__name or self.__name == "":
            self.getName()
        return self.__name

    @name.setter
    def name(self, name):
        self.__name = name
        if name and name != "":
            self.setBackupName()

    @property
    def backup_file(self):
        if not self.__backup_file or self.__backup_file == "":
            self.setBackupName()
        return self.__backup_file

    @backup_file.setter
    def backup_file(self, backup_file):
        self.__backup_file = backup_file

    def getName(self):
        raise NotImplementedError("Should have implemented `getName` method")

    def setBackupName(self, backup_file=""):
        '''Set backup filename'''

        if backup_file:
            self.backup_file_base = backup_file

        # Set backup file name
        if not self.backup_file_base:
            today = datetime.date.today()
            self.backup_file = "{name}.{date}.bkp".format( name=self.name, date=today.strftime('%Y-%m-%d') )
        else:
            self.backup_file = self.backup_file_base


    def login(self):
        '''Open SSH connection only if it is not already opened'''
        if self.client == False:

            # Start SSH connection
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Try login with user/password
            try:
                self.client.connect(self.ip, username=self.username, password=self.password, timeout=5, allow_agent=False, look_for_keys=False)
            except:
                # Try login with RSA key
                key = paramiko.RSAKey.from_private_key_file(self.rsa)
                self.client.connect(self.ip, username=self.username, timeout=5, pkey=key)


    def logout(self):
        '''Close SSH connection only if it is opened'''
        if self.client != False:
            self.client.close()
            # Higiene
            del self.client
            self.client = False


    def command(self, command):
        '''Send command to device and return (stdin, stdout, stderr) streams tuple'''
        self.login()

        return self.client.exec_command(command, timeout=5)


    def shell(self, *args, **kwargs):
        '''Opens a TTY shell'''
        self.login()

        if 'self' in kwargs:
            del kwargs['self']

        chan = self.client.invoke_shell(*args, **kwargs)
        interactive.interactive_shell(chan)
        chan.close()


    # Higiene
    def __del__(self):
        self.logout()

    def __str__(self):
        if self.mac:
            return u"{} : {} - {}".format(self.name, self.mac, self.ip)
        else:
            return u"{} : {}".format(self.name, self.ip)



def backup_devices_list(devices, path):
    '''Do backup on an ACDevice list'''
    i = 1
    failed = []

    for device in devices:

        # Debug:
        #if i == 10:
        #    break

        print(u"{index}.- {device}".format(index=i, device=str(device)))

        # Debug:
        #if i == 1:
        #    pprint(device.data)
        #    break

        warning = ""
        file = path + "/" + device.backup_file
        if os.path.exists(file) and os.stat(file).st_size > 0:
            print(u"    " + colored("[WARNING] Backup ja realitzat. Saltem.", 'yellow', attrs=['bold']))
            continue

        try:
            device.backup(path)
        except paramiko.ssh_exception.AuthenticationException as e:
            warning = u"[WARNING] Credencials incorrectes! (" + str(e) + ")"
        except paramiko.ssh_exception.NoValidConnectionsError as e:
            warning = u"[WARNING] No es pot establir connexió al port 22! (" + str(e) + ")"
        except socket.timeout as e:
            warning = u"[WARNING] Servidor no abastable! (" + str(e) + ")"
        except KeyboardInterrupt as e:
            raise e
        except Exception as e:
            warning = u"[WARNING] Excepció no gestionada: " + str(e)
        finally:
            device.logout()

        if warning != "":
            device.warning = warning
            print(u"    " + colored(warning, 'red', attrs=['bold']))
            failed.append(device)

        # Higiene
        else:
            del device

        i += 1

    return failed


def backup_devices(devices, path, retries=3):
    # Ensure backup dir exists
    print(u"Make dir: " + path)
    os.makedirs(path, exist_ok=True)

    failed = devices
    ok = 0
    while retries > 0:

        total = len(failed)

        # Do backup and get failed list
        failed = backup_devices_list(failed, path)

        # Sum non-failed to 'ok' counter
        ok += total - len(failed)

        # If list is empty, break while
        if len(failed) == 0:
            break

        # Decrease counter
        retries -= 1
        if retries > 0:
            print(colored(u"\nTornem a intentar amb les antenes que hagin fallat (queden {} intents, {} fallats)\n".format(retries-1, len(failed)), 'white', attrs=['bold']))

    # Print totals
    print(u"\n")
    print(colored(u"Descarregats {ok} backups".format(ok=ok), 'green', attrs=['bold']))
    print(colored(u"NO Descarregats {ko} backups".format(ko=len(failed)), 'red', attrs=['bold']))
    print(u"\n")

    # Print failed
    if len(failed) > 0:
        print(u"Failed %d devices:" % (len(failed)))
        for f in failed:
            print(u" - {device}: {warning}".format(device=str(f), warning=colored(f.warning, 'red', attrs=['bold'])))

        print(u"\n")
