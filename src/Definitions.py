
"""
This file contains all macro definitions, utility functions, and libraries
used in this software. Any changes of value made in this file will propagate
to all test cases generated by this software. Some settings that are not
possible to configure in command line may be easily specified in this file.

@author: Calvin Jia Liang
Created on Sep 3, 2014
"""

import os
import ssl
import shutil
import sys
import socket
import select
import time
import copy
import subprocess
import math
import queue
from OpenSSL import *

# current version of this software; should be updated for each modification
SOFTWARE_VERSION = "0.2.2"

# current version of test case; should be updated for each modification
TEST_VERSION = "1.1"

# default subject field entries other than the CN
DEFAULT_C = "US"
DEFAULT_ST = "CA"
DEFAULT_L = "San Luis Obispo"
DEFAULT_O = "Certificate Validation and Compliance"
DEFAULT_U = "X509 Verification Checker"
DEFAULT_EMAIL = "someone@mail.com"

# default x509 settings
DEFAULT_KSIZE = 1024
DEFAULT_KTYPE = crypto.TYPE_RSA
DEFAULT_HOUR_BEFORE = -48
DEFAULT_HOUR_AFTER = 8760
DEFAULT_VERSION = 0x02
DEFAULT_DIGEST = "SHA1"
DEFAULT_SUITE = "DEFAULT"

# default certificate and key file operation setting
DEFAULT_PASSWORD = "test"
DEFAULT_CIPHER = "aes-256-cbc"
DEFAULT_PEM_NAME = "cert.pem"
DEFAULT_KEY_NAME = "cert.key"

# default file paths
DEFAULT_SERIAL_PATH = os.path.join(".", "serial")
DEFAULT_LICENSE_PATH = os.path.join(".", "LICENSE")
DEFAULT_CA_PREFIX = os.path.join(".", "ca", "ca")
DEFAULT_CERT_DIR = os.path.join(".", "certs", "")

# other static settings throughout the test
REPEAT = 3
HOUR_DISCREPANCY = 48
INVALID_TRAIL = ".invalid.test"
NONSTANDARD_OID = "1.3.6.1.4.1.11129.2.5.1"

# other default settings throughout the test
DEFAULT_NUM_CHAINED = 4
DEFAULT_SERIAL = 1001
DEFAULT_PAUSE = 0
DEFAULT_CA_NAME = "verify.x509.test"
DEFAULT_METADATA_NAME = "metadata"

# rank macros for severity
SEV_HIGH = "High"
# invalid CA certificate becomes valid
SEV_MED = "Medium"
# invalid leaf certificate becomes valid
SEV_LOW = "Low"
# compliance issue

# rank macros for ease of execution
EASE_HIGH = "High"
# require no CA or compliant CA with basic server sign
EASE_MED = "Medium"
# require non-compliant CA with server sign
EASE_LOW = "Low"
# require CA with CA sign or compromise of other information

# default server settings
DEFAULT_PORT = 443
DEFAULT_SSL_VER = SSL.SSLv23_METHOD
DEFAULT_ADDR = "127.0.0.1"

# functionality test set
FUNC_KEY_SIZES = [512, 1024, 2048, 1025]
FUNC_KEY_TYPES = [crypto.TYPE_RSA]
FUNC_CIPHER_SUITES = ["DEFAULT", "HIGH", "MEDIUM",
                      "LOW", "aNULL", "eNULL"]
FUNC_SSL_VERSIONS = [SSL.TLSv1_2_METHOD, SSL.TLSv1_1_METHOD,
                     SSL.TLSv1_METHOD, SSL.SSLv3_METHOD]

# overflow test set
OVERFLOW_VALID_CA = True
OVERFLOW_CHAIN_LEN = 100
OVERFLOW_EXT_LEN = 500
OVERFLOW_OID_MUL = 500
DEFAULT_OVERFLOW_LENGTH = 640000

# debugging options
VERBOSE = False

# global variables
serial = None


# utility functions

"""
Get the default fqdn of the intermediate CA
:param lev: level of depth below the root CA
:type  lev: integer
:returns: string
"""


def getIntCAName(lev):
    return "int.lev%i%s" % (lev, getIntCADomain())

"""
Get the default domain name of the intermediate CA
:returns: string
"""


def getIntCADomain():
    return ".ca.authority"

"""
Get an invalid fqdn from the valid fqdn
:param testName: valid fqdn
:type  testName: string
:returns: string
"""


def getInvalidDomain(testName):
    return testName + INVALID_TRAIL

"""
Get an invalid null extended fqdn from the valid fqdn
:param testName: valid fqdn
:type  testName: string
:returns: string
"""


def getInvalidNullDomain(testName):
    return testName + "\0" + INVALID_TRAIL

"""
Get a new test name for the chain extended test case
:param testName: original test name
:type  testName: string
:returns: string
"""


def getChainedName(testName):
    return testName + "Chained"

"""
Get a new test name for the altname extended test case
:param testName: original test name
:type  testName: string
:returns: string
"""


def getAltExtendedName(testName):
    return testName + "AltName"


def isIPAddr(fqdn):
    ip = fqdn.split('.')

    if (len(ip) != 4):
        return False

    for a in ip:
        try:
            o = int(a)
        except:
            return False

        if (o < 0 or o > 255):
            return False

    return True

"""
Get a new serial number that is an increment of the last number; first number
obtained from the serial file
:note: this function modifies global variable
:param filePath: path to the serial file
:type  filePath: string
:returns: integer
"""


def getNewSerial(filePath=DEFAULT_SERIAL_PATH):
    global serial

    if (not serial):
        with open(filePath, 'r') as f:
            serial = int(f.readline().strip())

    rtn = serial
    serial += 1
    return rtn

"""
Save the serial number to file
:param filePath: path to the serial file
:type  filePath: string
"""


def saveSerial(filePath=DEFAULT_SERIAL_PATH):
    with open(filePath, 'w') as f:
        f.write(str(serial))


def unmarkCriticalExtensions(case):
    cnt = 0

    for cert in case.certs:
        for extension in cert.extensions:
            if (extension.criticality()):
                extension.critical = False
                cnt += 1

    return cnt

"""
Get the license of this software
:param filePath: path to the license file
:type  filePath: string
:return: string
"""


def getLicense(path=DEFAULT_LICENSE_PATH):
    data = ""

    try:
        with open(path, 'r') as f:
            data = f.read()
    except:
        pass
#         raise Exception("Missing license file");

    return data

"""
Concatenate two files (first + second) together to form a new file
:param src: path to the first file
:type  src: string
:param oth: path to the second file
:type  oth: string
:param dest: path to the destination file
:type  dest: string
"""


def concatFiles(src, oth, dest):
    with open(src, 'rb') as s:
        with open(oth, 'rb') as o:
            data = s.read() + o.read()

    with open(dest, 'wb+') as d:
        d.write(data)

"""
Prints a message then terminate the program immediately
:param msg: message to print out
:type  msg: string
:param log: output stream
:type  log: Function object
"""


def forcedExit(msg, log):
    log(msg)
    log("Program Exits with Error.")
    sys.exit(1)
