import os
import pathlib

logFile=None

def log(message, important=False):
  global logFile
  if important:
    print(message)
  if not logFile:
    logDir = "{}/file-syncer/".format(os.getenv("APPDATA"))
    if not os.path.exists(logDir):
      os.makedirs(logDir)
    path = "{}/log.log".format(logDir)
    logFile = open(path, "a+")
    print("", file=logFile)
    print("", file=logFile)
    print("========================================================================================================================", file=logFile)
    print("========================================================================================================================", file=logFile)
    print("========================================================================================================================", file=logFile)
  print("{}: {}".format(os.getenv("COMPUTERNAME"), message), file=logFile)

def debug(message):
  log(message)

def info(message):
  log(message, True)

def warn(message):
  log("WARNING: " + message, True)

def err(message):
  log("ERROR: " + message, True)
