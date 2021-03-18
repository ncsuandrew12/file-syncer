import json
import os
import pathlib
import shutil
import subprocess
from Logging import debug
from Logging import info
from Logging import warn
from Logging import err

openFiles=[]
logFile=None
targetRoot=None
config={}

def main():
  try:
    loadConfig("cfg.json")
    loadFileList("filelist.files")
    setupSyncServices()
    setupLinks()
  finally:
    for file in openFiles:
      try:
        file.close()
      except Exception as e:
        warn(e)

def loadConfig(file):
  global config
  with open(file) as cfg:
    config = json.load(cfg)
    usernames=[]
    for cfgKey in config:
      if cfgKey == "AlternateUserNames":
        usernames = config[cfgKey]
    usernames.insert(0, os.getenv("USERNAME"))
    config["Usernames"] = usernames

def loadFileList(file):
  global files
  files = []
  with open(file, "r") as listFile:
    for filePath in listFile:
      files.append(filePath)

def setupSyncServices():
  setupSyncService("GOOGLEDRIVE", [ "Google Drive", "GoogleDrive", "GDrive", "Google-Drive", "Google_Drive", "google-drive" ])

def setupSyncService(varName, dirNameVariants):
  rootDir = None
  for rootDirName in dirNameVariants:
    rootDir = getPath("$HOME/{}".format(rootDirName), False)
    if os.path.exists(rootDir):
      break
    rootDir = getPath("$HOME/Documents/{}".format(rootDirName), False)
    if os.path.exists(rootDir):
      break
    rootDir = getPath("{}:/Users/{}/{}".format(os.getenv("HOMEDRIVE"), os.getenv("USERNAME"), rootDirName), False)
    if os.path.exists(rootDir):
      break
    rootDir = getPath("{}:/Users/{}/Documents/{}".format(os.getenv("HOMEDRIVE"), os.getenv("USERNAME"), rootDirName), False)
    if os.path.exists(rootDir):
      break
    rootDir = getPath("{}:/{}".format(os.getenv("HOMEDRIVE"), rootDirName), False)
    if os.path.exists(rootDir):
      break
    rootDir = getPath("{}:/{}".format(os.getenv("SYSTEMDRIVE"), rootDirName), False)
    if os.path.exists(rootDir):
      break
    for username in config["Usernames"]:
      if os.path.exists(rootDir):
        break
      rootDir = "E:/Users/{}/{}".format(username, rootDirName) # TODO Don't hard-coded the drive letter
  if os.path.exists(rootDir):
    config[varName] = rootDir
  else:
    info("Could not find {} directory.".format(varName))

def setupLinks():
  global targetRoot
  for filePath in files:
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
    if not setupLink(localPath, remotePath):
      continue

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
        path = "{}:{}".format(os.getenv("HOMEDRIVE"), os.getenv("HOMEPATH"))
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

def setupLink(linkPath, targetPath):
    debug("{} -> {}".format(linkPath, targetPath))
    if os.path.islink(linkPath):
      debug("Skipping {} because it is already a symlink".format(linkPath))
      return False
    if not pathlib.Path(linkPath).exists():
      debug("Skipping {} because it doesn't exist".format(linkPath))
      return False
    copyPath = targetPath
    if pathlib.Path(targetPath).exists():
      remotePathBak = targetPath
      i=1
      while pathlib.Path(remotePathBak).exists():
        remotePathBak = "{}-bak-{}".format(targetPath, i)
        i+=1
      info("{} already exists. Will backup local files to {}".format(targetPath, remotePathBak))
      copyPath = remotePathBak
    if os.path.isdir(linkPath):
      debug("{} is directory".format(linkPath))
      parentPath = pathlib.Path(copyPath).parent.absolute()
      if not parentPath.exists():
        os.makedirs(parentPath)
      shutil.copytree(linkPath, copyPath)
      shutil.rmtree(linkPath)
      info("Linking {} -> {}".format(linkPath, targetPath))
      mklinkDir(linkPath, targetPath)
    elif os.path.isfile(linkPath):
      debug("{} is file".format(linkPath))
      shutil.copy(linkPath, copyPath)
      os.remove(linkPath)
      info("Linking {} -> {}".format(linkPath, targetPath))
      mklink(linkPath, targetPath)
    else:
      err("{} is neither symlink, directory, nor file".format(linkPath))
      return False
    return True

def mklink(linkPath, targetPath):
  subprocess.call(["mklink.bat", linkPath, targetPath])

def mklinkDir(linkPath, targetPath):
  subprocess.call(["mklinkDir.bat", linkPath, targetPath])

main()
