import os
import pathlib

logFile=None

def log(message, important=False):
  global logFile
  if important:
    print(message)
  if not logFile:
    logDir = "{}/Users/{}/file-syncer".format(os.getenv("HOMEDRIVE"), os.getenv("USERNAME"))
    if not os.path.exists(logDir):
      print("Making logDir: " + logDir)
      os.makedirs(logDir)
    path = "{}/log.log".format(logDir)
    if os.path.exists(path):
      logFile = open(path, "a+")
    else:
      logFile = open(path, "w")
    print("Logging to file: \"{}\"".format(path))
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
