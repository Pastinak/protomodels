"""This Package is intended to contain everything related to theory:

   * cross section calculation code
   * sms decomposition code (LHE-based, SLHA-based)
   * some more tools, e.g. for reading/writing slha files, or particle names
   
"""
import os
import logging.config

basepath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
logging.config.fileConfig('%s/logging.conf' % basepath, disable_existing_loggers=False)
logger = logging.getLogger(__name__)
