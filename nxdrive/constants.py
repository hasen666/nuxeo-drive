# coding: utf-8
from pathlib import Path
from sys import platform

LINUX = platform == "linux"
MAC = platform == "darwin"
WINDOWS = platform == "win32"

BUNDLE_IDENTIFIER = "org.nuxeo.drive"
APP_NAME = "Nuxeo Drive"
COMPANY = "Nuxeo"

TIMEOUT = 20
STARTUP_PAGE_CONNECTION_TIMEOUT = 30
TX_TIMEOUT = 300
FILE_BUFFER_SIZE = 1024 ** 2
MAX_LOG_DISPLAYED = 50000

DOWNLOAD_TMP_FILE_PREFIX = "."
DOWNLOAD_TMP_FILE_SUFFIX = ".nxpart"
PARTIALS_PATH = Path(".partials")
ROOT = Path()

UNACCESSIBLE_HASH = "TO_COMPUTE"

TOKEN_PERMISSION = "ReadWrite"

# The registry key from the HKCU hive where to look for local configuration on Windows
CONFIG_REGISTRY_KEY = "Software\\Nuxeo\\Drive"
