#!/usr/bin/python3.5

import logging
import sys

logging.basicConfig(stream=sys.stderr)
sys.path.insert(0, '$HOME/bosch_pls/')
from api_v1 import app as application
