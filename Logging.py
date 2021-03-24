# Standard
import logging
import os
import pathlib
import sys
from logging.handlers import RotatingFileHandler

class MaxLogLevelFilter(logging.Filter):
  def __init__(self, logLevel):
    self.logLevel = logLevel
  def filter(self, record):
    return record.levelno <= self.logLevel
  logLevel = logging.DEBUG

class Formatter(logging.Formatter):
  def format(self, record):
    record.timeZone = "EST"
    record.levelnameSuffix = (" " * (len("CRITICAL") - len(record.levelname)))
    return logging.Formatter.format(self, record)

logDir = "{}/Users/{}/file-syncer".format(os.getenv("HOMEDRIVE"), os.getenv("USERNAME"))
if not os.path.exists(logDir):
  print("Making logDir: " + logDir)
  os.makedirs(logDir)

logger = logging.getLogger("firetap.tools.pyhelper")
# logger.setLevel(logging.DEBUG)
formatter = Formatter(
  fmt="%(asctime)s %(timeZone)s %(processName)s:%(threadName)s %(levelname)s:%(levelnameSuffix)s %(pathname)s:%(lineno)d(%(funcName)s) %(message)s",
  datefmt=None)
fileHandler = RotatingFileHandler(
  filename="{}/log.log".format(logDir),
  maxBytes=5 * 1024 * 1024, # 5MB
  backupCount=9,
  delay=True)
fileHandler.setFormatter(formatter)
stdoutHandler = logging.StreamHandler(stream=sys.stdout)
stdoutHandler.setFormatter(formatter)
stderrHandler = logging.StreamHandler(stream=sys.stderr)
stderrHandler.setFormatter(formatter)
logger.addHandler(fileHandler)
logger.addHandler(stdoutHandler)
logger.addHandler(stderrHandler)
logging.getLogger().setLevel(logging.NOTSET)
stdoutHandler.setLevel(logging.INFO)
stdoutHandler.addFilter(MaxLogLevelFilter(logging.WARNING))
stderrHandler.setLevel(logging.ERROR)