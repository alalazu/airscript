| GitHub | PyPI |
| ------ | ---- |
| [![GitHub](https://img.shields.io/badge/GitHub-airscript-blue?logo=github)](https://github.com/alalazu/airscript) | [![PyPI](https://img.shields.io/pypi/v/pyAirscript?logo=pypi)](https://pypi.org/project/pyAirscript/) |

# AirScript

AirScript is your scriptable Python interface to the Airlock Gateway
configuration REST API, providing access to configuration objects,
virtual hosts, mappings etc.

AirScript can be used interactively using its console which allows
you to easily and quickly inspect and adjust an Airlock Gateway
configuration using the REST API. It can also be used for
more complex operations for which a script has previously been created,
e.g. migrating an applications configuration from a test to a production
environment.

[Airlock Gateway](https://www.airlock.com/en/secure-access-hub/components/gateway) is a web application firewall (WAF) and protects mission-critical,
web-based applications and APIs from attacks and undesired visitors.
As a central security instance, it examines every HTTP(S) request for attacks and
thus blocks any attempt at data theft and manipulation.

## Getting started

### Installation
```bash
pip install pyAirscript
```

### Documentation

The documentation has not yet been created and is forthcoming.

### Setup
First, you need to create a config file with connection parameters for your Airlock Gateways.
You can use samples/config.yaml as a template. 

The API keys can be retrieved via Airlock Config Center - System Setup - System Admin.

The default location for the config file is "~/.airscript/config.yaml".
Otherwise, you can specify its location on the command line:
```bash
airscript --config <path to config file>
```

### Usage
```bash
usage: airscript.py [-h] [-c CONFIGFILE] [-i INIT] [-v] [-l LOGLEVEL] [-L LOGFILE] [-V] [path ...]

AirScript - the Airlock Gateay Configuration Script

positional arguments:
  path                  script to execute and its parameters

options:
  -h, --help            show this help message and exit
  -c CONFIGFILE, --config CONFIGFILE
                        path to config file (default: ~/.airscript/config.yaml)
  -i INIT, --init INIT  path to initialisation script(s), can be specified multiple times (default, in order: /etc/airscript/init.air, ~/.airscript.rc
  -v, --verbose         verbose output
  -l LOGLEVEL, --loglevel LOGLEVEL
                        log level, bitmask of fatal (1), critical (2), error (4), warning (8), info (16), verbose (32), trace (64), debug (128) (default: 31)
  -L LOGFILE, --logfile LOGFILE
                        log destination: stdout, stderr, or <filename> (default: None)
  -V, --version         get version information
```

## Example sessions

### Mapping: activate maintenance mode
```python
Welcome to AirScript - the Airlock Gateay Configuration Script - Version 6
Loading gateway definitions
Connecting to 'test'
Fetching active config
Preloaded:
- gw: gateway 'test'
- c: current active config
AirScript is ready
>>> m=c.mappings(name='apollo')
>>> m
{74: {'id': 74, 'name': 'apollo', 'path': '/apollo/', 'labels': ['Sharepoint_2016', 'Sharepoint', 'Kerberos', 'Prod', 'Derived']}}
>>> print(m[74].attrs['enableMaintenancePage'])
False
>>> m[74].attrs['enableMaintenancePage']=True
>>> c.sync()
>>> c.activate( comment="Apollo: maintenance page activated" )
```

### Virtual host: change IP
```python
Welcome to AirScript - the Airlock Gateay Configuration Script - Version 6
Loading gateway definitions
Connecting to 'test'
Fetching active config
Preloaded:
- gw: gateway 'test'
- c: current active config
AirScript is ready
>>> c
{'id': '68', 'comment': 'example app', 'type': 'CURRENTLY_ACTIVE'}
>>> c.vhosts()
{'66': {'id': '66', 'name': 'example.com:8500 (docker registry)', 'ipv4': '10.1.7.3/24'}, '7': {'id': '7', 'name': "test.example.com:443", 'ipv4': '10.1.7.34/24'}}
>>> vh=c.vhosts('7')
>>> pp(vh)
{'7': {'id': '7', 'name': "cuenca.zuska.marmira.com:443 (Let's Encrypt)", 'ipv4': '10.89.7.29/24'}}
>>> pp(vh['7'].attrs)
{'aliasNames': [],
 'defaultRedirect': '/',
 'downloadPdfsAsAttachmentsEnforced': False,
 'encodedSlashesAllowed': False,
 'expertSettings': {'apache': {'enabled': False, 'settings': ''},
                    'securityGate': {'enabled': False, 'settings': ''}},
 'hostName': 'cuenca.zuska.marmira.com',
 'keepAliveTimeout': 10,
 'name': "cuenca.zuska.marmira.com:443 (Let's Encrypt)",
 'networkInterface': {'externalLogicalInterfaceName': 'EXT0',
                      'http': {'enabled': True,
                               'httpsRedirectEnforced': False,
                               'port': 80},
                      'https': {'enabled': True,
                                'http2Allowed': False,
                                'port': 443},
                      'ipV4Address': '10.89.7.29/24',
                      'ipV6Address': ''},
 'pathRedirects': [],
 'serverAdmin': '',
 'session': {'cookieDomain': '', 'cookiePath': '/'},
 'showMaintenancePage': False,
 'tenant': '',
 'tls': {'caCertificatesForChainAndOcspValidation': [],
         'caCertificatesForClientCertificateSelection': [],
         'chainVerificationDepth': 1,
         'cipherSuite': 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384:DHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256',     
         'cipherSuiteMode': 'DEFAULT',
         'clientCertificateAuthentication': 'NOT_REQUIRED',
         'letsEncryptEnabled': False,
         'ocspStaplingEnabled': False,
         'ocspValidationEnforced': False,
         'protocol': 'all -SSLv3 -TLSv1 -TLSv1.1',
         'protocolMode': 'DEFAULT'}}
>>> vh['7'].set( 'networkInterface.ipV4Address', '10.1.8.12/24' )
>>> c.sync()
>>> c.save( comment="Changed test.example.com IP address" )
```

This creates a new but yet inactive configuration. It can be manually activated in the Airlock Config Center.

## Getting support

AirScript is not part of the official Airlock product delivery. Airlock support will be unable
to accept or answer tickets.

If you encounter an error, the author welcomes pull requests with fixes. Alternatively, an issue may be created
on the [GitHub issue tracker](https://github.com/alalazu/airscript/issues).
Please note that there is no guaranteed response time and any support is best effort.
