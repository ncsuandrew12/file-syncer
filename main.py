import json
import os
import pathlib
import shutil
import string
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
    setupCustomVars()
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
  searchDirs = []
  for rootDirName in dirNameVariants:
    searchDirs.append(getPath("$HOME/{}".format(rootDirName), False))
    searchDirs.append(getPath("$HOME/Documents/{}".format(rootDirName), False))
    searchDirs.append(getPath("{}/Users/{}/{}".format(os.getenv("HOMEDRIVE"), os.getenv("USERNAME"), rootDirName), False))
    searchDirs.append(getPath("{}/Users/{}/Documents/{}".format(os.getenv("HOMEDRIVE"), os.getenv("USERNAME"), rootDirName), False))
    searchDirs.append(getPath("{}/{}".format(os.getenv("HOMEDRIVE"), rootDirName), False))
    searchDirs.append(getPath("{}/{}".format(os.getenv("SYSTEMDRIVE"), rootDirName), False))
    for driveLetter in string.ascii_uppercase:
      searchDirs.append(getPath("{}:/{}".format(driveLetter, rootDirName), False))
      for username in config["Usernames"]:
        searchDirs.append(getPath("{}:/Users/{}/{}".format(driveLetter, username, rootDirName), False))
  for searchDir in searchDirs:
    if os.path.exists(searchDir):
      config[varName] = searchDir
      debug("{}: \"{}\"".format(varName, searchDir))
      break
  if not os.path.exists(config[varName]):
    info("Could not find {} directory.".format(varName))

def setupCustomVars():
  setupCustomVarHome("HOME")
  setupCustomVarAppDataLocalLow("APPDATALOCALLOW")

def setupCustomVarHome(varName):
  searchDirs = []
  searchDirs.append("{}:{}".format(os.getenv("HOMEDRIVE"), os.getenv("HOMEPATH")))
  for driveLetter in string.ascii_uppercase:
    for username in config["Usernames"]:
      searchDirs.append("{}:/Users/{}".format(driveLetter, username))
  finishCustomVarSetup(varName, searchDirs)

def setupCustomVarAppDataLocalLow(varName):
  searchDirs = []
  searchDirs.append("{}/AppData/LocalLow".format(config["HOME"]))
  finishCustomVarSetup(varName, searchDirs)

def finishCustomVarSetup(varName, searchDirs):
  for searchDir in searchDirs:
    if os.path.exists(searchDir):
      config[varName] = searchDir
      debug("{}: \"{}\"".format(varName, config[varName]))
      break
  if not os.path.exists(config[varName]):
    warn("Could not find {} directory.".format(varName))

def setupLinks():
  global targetRoot
  for filePath in files:
    filePath = filePath.rstrip()
    debug("Processing \"{}\"".format(filePath))
    if filePath.startswith("#"):
      debug("Skipping comment line: \"{}\"".format(filePath))
      continue;
    if not bool(targetRoot):
      targetRoot = getPath(config["TargetDir"], False)
      if not os.path.exists(targetRoot):
        os.makedirs(targetRoot)
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
    debug("\"{}\" -> \"{}\"".format(linkPath, targetPath))
    if os.path.islink(linkPath):
      debug("Skipping \"{}\" because it is already a symlink".format(linkPath))
      return False
    if not pathlib.Path(linkPath).exists():
      debug("Skipping \"{}\" because it doesn't exist".format(linkPath))
      return False
    copyPath = targetPath
    if pathlib.Path(targetPath).exists():
      remotePathBak = targetPath
      i=1
      while pathlib.Path(remotePathBak).exists():
        remotePathBak = "{}-bak-{}".format(targetPath, i)
        i+=1
      info("\"{}\" already exists. Will backup local files to \"{}\"".format(targetPath, remotePathBak))
      copyPath = remotePathBak
    if os.path.isdir(linkPath):
      debug("\"{}\" is directory".format(linkPath))
      parentPath = pathlib.Path(copyPath).parent.absolute()
      if not parentPath.exists():
        os.makedirs(parentPath)
      shutil.copytree(linkPath, copyPath)
      shutil.rmtree(linkPath)
      info("Linking \"{}\" -> \"{}\"".format(linkPath, targetPath))
      mklinkDir(linkPath, targetPath)
    elif os.path.isfile(linkPath):
      debug("\"{}\" is file".format(linkPath))
      shutil.copy(linkPath, copyPath)
      os.remove(linkPath)
      info("Linking \"{}\" -> \"{}\"".format(linkPath, targetPath))
      mklink(linkPath, targetPath)
    else:
      err("\"{}\" is neither symlink, directory, nor file".format(linkPath))
      return False
    return True

def mklink(linkPath, targetPath):
  subprocess.call(["mklink.bat", linkPath.replace("/", "\\"), targetPath.replace("/", "\\")])

def mklinkDir(linkPath, targetPath):
  subprocess.call(["mklinkDir.bat", linkPath.replace("/", "\\"), targetPath.replace("/", "\\")])

main()
