# NOTICE
#
# This software was produced for the U. S. Government
# under Basic Contract No. W15P7T-13-C-A802, and is
# subject to the Rights in Noncommercial Computer Software
# and Noncommercial Computer Software Documentation
# Clause 252.227-7014 (FEB 2012)
#
# (C) 2017 The MITRE Corporation.

import os
import socket
import base64

import yaml
import cryptography.fernet

from app.utils import import_database_from_file, confirm

url = None
config = None


def load():
    # Global variables to avoid loading twice
    global url, config
    if config is not None:
        return config

    with open('conf/cascade.yml', 'r') as f:
        config = yaml.load(f.read())

    server_settings = config['server']
    proto = 'https' if server_settings['https']['enabled'] else 'http'
    url = '{proto}://{hostname}:{port}'.format(proto=proto, **server_settings)
    server_settings['url'] = url
    return config


def get_value(key, default, indent=0):
    tab = "    "
    if isinstance(default, dict):
        if key:
            print("{}{}:".format(tab * indent, key))
        return {k: get_value(k, v, indent=indent + int(key is not None)) for k, v in default.items()}
    elif isinstance(default, (list, tuple)):
        return default
    else:
        new_value = input("{}{key} ({default}): ".format(tab * indent, key=key, default=str(default).strip())).strip()
        if new_value == "":
            return default
        elif isinstance(default, bool):
            # Convert "True" and "Yes" to boolean true
            return new_value[0].lower() in ("y", "t")
        else:
            # Otherwise figure out the initial type and convert it
            return type(default)(new_value)


def setup(auto_defaults=False):
    placeholder = "<autogenerate>"

    with open('conf/defaults.yml', 'r') as f:
        defaults = yaml.load(f.read())

    defaults['server']['hostname'] = socket.getfqdn().lower()
    if auto_defaults:
        print("Automatically updated configuration settings for CASCADE based on defaults.yml")
        custom_settings = defaults
    else:
        print("Update configuration settings for CASCADE. Enter nothing to keep the default value")
        custom_settings = get_value(None, defaults)

    crypto = custom_settings['database']['crypto']

    if crypto['fernet'] == placeholder:
        crypto['fernet'] = cryptography.fernet.Fernet.generate_key()

    if crypto['key'] == placeholder:
        crypto['key'] = base64.b64encode(os.urandom(64))

    with open('conf/cascade.yml', 'w') as f:
        yaml.dump(custom_settings, f, explicit_start=True, indent=4, default_flow_style=False)

    print("\nInitializing database...")
    for filename in 'attack.bson', 'cascade-analytics.bson', 'default-sessions.bson':
        import_database_from_file('misc/{}'.format(filename))


__all__ = ["setup"]
