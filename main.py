import json
import os
import pathlib
import shutil
import subprocess

cGoogleDriveVariants=[ "Google Drive", "Google_Drive", "google-drive" ]
files=[]
logFile=None
targetRoot=None
config={}

def log(message, important=False):
  global files
  global logFile
  if important:
    print(message)
  if not logFile:
    logFile = open("log.log", "a+")
    files.insert(0, logFile)
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

def mklink(linkPath, targetPath):
  subprocess.call(["mklink.bat", linkPath, targetPath])

def mklinkDir(linkPath, targetPath):
  subprocess.call(["mklinkDir.bat", linkPath, targetPath])

def getPath(filePath, isRemoteSubPath):
  dirMain = filePath.split("/")[0]
  subPath = filePath[len(dirMain) + 1:]
  path = filePath
  if dirMain.startswith("$"):
    dirMain = dirMain[1:]
    if isRemoteSubPath:
      path = "{}/{}".format(targetRoot, dirMain)
    else:
      if dirMain in config:
        path = config[dirMain]
        if not os.path.exists(path):
          raise Exception("Could not locate {} ({}): {}".format(dirMain, path, subPath))
      elif dirMain == "HOME":
        path = "{}:{}".format(os.getenv("SYSTEMDRIVE"), os.getenv("HOMEPATH"))
        for username in config["Usernames"]:
          if os.path.exists(path):
            break
          path = "E:/Users/{}/{}".format(username, dirMain) # TODO Don't hard-coded the drive letter
      else:
        path = os.getenv(dirMain)
        if not path:
          raise Exception("Environment variable {} does not exist".format(dirMain))
        if not os.path.exists(path):
          raise Exception("{} does not exist".format(path))
    path = "{}/{}".format(path, subPath)
  elif ":" in filePath:
    if isRemoteSubPath:
      path = "{}/{}/{}".format(targetRoot, filePath[0:1], filePath[3])
  else:
    raise Exception("Paths must begin with $<var> or a drive letter. Problematic path: {}", filePath)
  return path

listFile = open("filelist.files", "r")
files.insert(0, listFile)
try:
  with open("cfg.json") as cfg:
    config = json.load(cfg)
    usernames=[]
    for cfgKey in config:
      if cfgKey == "AlternateUserNames":
        usernames = config[cfgKey]
    usernames.insert(0, os.getenv("USERNAME"))
    config["Usernames"] = usernames

  gDriveRootDir = None
  for gdriveRootDirName in cGoogleDriveVariants:
    gDriveRootDir = getPath("$HOME/Documents/{}".format(gdriveRootDirName), False)
    if os.path.exists(gDriveRootDir):
      break
    for username in config["Usernames"]:
      if os.path.exists(gDriveRootDir):
        break
      gDriveRootDir = "E:/Users/{}/{}".format(username, gdriveRootDirName) # TODO Don't hard-coded the drive letter
  config["GOOGLEDRIVE"] = gDriveRootDir

  for filePath in listFile:
    filePath = filePath.rstrip()
    debug("Processing '{}'".format(filePath))

    if filePath.startswith("#"):
      debug("Skipping comment line: {}".format(filePath))
      continue;

    if not bool(targetRoot):
      targetRoot = getPath(config["TargetDir"], False)
      if not os.path.exists(targetRoot):
        raise Exception("Target root directory does not exist: {}".format(targetRoot))
      continue

    localPath = getPath(filePath, False)
    remotePath = getPath(filePath, True)

    debug("{} -> {}".format(localPath, remotePath))

    if os.path.islink(localPath):
      debug("Skipping {} because it is already a symlink".format(localPath))
      continue

    if not pathlib.Path(localPath).exists():
      debug("Skipping {} because it doesn't exist".format(localPath))
      continue

    copyPath = remotePath
    if pathlib.Path(remotePath).exists():
      remotePathBak = remotePath
      i=1
      while pathlib.Path(remotePathBak).exists():
        remotePathBak = "{}-bak-{}".format(remotePath, i)
        i+=1
      info("{} already exists. Will backup local files to {}".format(remotePath, remotePathBak))
      copyPath = remotePathBak

    if os.path.isdir(localPath):
      debug("{} is directory".format(localPath))
      parentPath = pathlib.Path(copyPath).parent.absolute()
      if not parentPath.exists():
        os.makedirs(parentPath)
      shutil.copytree(localPath, copyPath)
      shutil.rmtree(localPath)
      info("Linking {} -> {}".format(localPath, remotePath))
      mklinkDir(localPath, remotePath)
    elif os.path.isfile(localPath):
      debug("{} is file".format(localPath))
      shutil.copy(localPath, copyPath)
      os.remove(localPath)
      info("Linking {} -> {}".format(localPath, remotePath))
      mklink(localPath, remotePath)
    else:
      err("{} is neither symlink, directory, nor file".format(localPath))
finally:
  for file in files:
    try:
      file.close()
    except Exception as e:
      warn(e)