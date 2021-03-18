import os
import pathlib

logFile=None

def log(message, important=False):
  global logFile
  if important:
    print(message)
  if not logFile:
    logFile = open("log.log", "a+")
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
