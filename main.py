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
    loadConfig()
    loadFileList("filelist.files")
    users = [ os.getenv("USERNAME") ]
    if config["AllUsers"]:
      users = [userDir.name for userDir in pathlib.Path("{}/Users".format(os.getenv("SYSTEMDRIVE"))).glob('*') if userDir.name not in ['Default', 'Default User', 'Public', 'All Users'] and userDir.is_dir() ]
    for user in users:
      debug("Running for {}".format(user))
      usernames = getAliases(user)
      setupCustomVars(usernames)
      setupSyncServices(usernames)
      debug("config:\n{}".format(json.dumps(config, sort_keys=True, indent=2)))
      setupLinks(user)
  finally:
    for file in openFiles:
      try:
        file.close()
      except Exception as e:
        warn(e)

def loadConfig():
  global config
  with open("cfg.json") as cfg:
    config = json.load(cfg)
  if os.path.exists("cfg-user.json"):
    with open("cfg-user.json") as cfg:
      configUser = json.load(cfg)
    # Overwrite the defaults with the user's settings
    for key in configUser:
      config[key] = configUser[key]

def loadFileList(file):
  global files
  files = []
  with open(file, "r") as listFile:
    for filePath in listFile:
      files.append(filePath)

def getAliases(username):
  usernames=[]
  for cfgKey in config:
    if cfgKey == "UserNameAliases":
      if username in config[cfgKey]:
        usernames = config[cfgKey][username].copy()
  if username not in usernames:
    usernames.insert(0, username)
  return usernames

def setupSyncServices(usernames):
  setupSyncService(usernames, "GOOGLEDRIVE", [ "Google Drive", "GoogleDrive", "GDrive", "Google-Drive", "Google_Drive", "google-drive" ])

def setupSyncService(usernames, varName, dirNameVariants):
  searchDirs = []
  for rootDirName in dirNameVariants:
    searchDirs.append(getPath(usernames[0], "$HOME/{}".format(rootDirName), False))
    searchDirs.append(getPath(usernames[0], "$DOCUMENTS/{}".format(rootDirName), False))
    searchDirs.append(getPath(usernames[0], "{}/Users/{}/{}".format(os.getenv("HOMEDRIVE"), os.getenv("USERNAME"), rootDirName), False))
    searchDirs.append(getPath(usernames[0], "{}/Users/{}/Documents/{}".format(os.getenv("HOMEDRIVE"), os.getenv("USERNAME"), rootDirName), False))
    searchDirs.append(getPath(usernames[0], "{}/{}".format(os.getenv("HOMEDRIVE"), rootDirName), False))
    searchDirs.append(getPath(usernames[0], "{}/{}".format(os.getenv("SYSTEMDRIVE"), rootDirName), False))
    for driveLetter in string.ascii_uppercase:
      searchDirs.append(getPath(usernames[0], "{}:/{}".format(driveLetter, rootDirName), False))
      for username in usernames:
        searchDirs.append(getPath(username, "{}:/Users/{}/{}".format(driveLetter, username, rootDirName), False))
  for searchDir in searchDirs:
    if os.path.exists(searchDir):
      config[varName] = searchDir
      debug("{}: \"{}\"".format(varName, searchDir))
      break
  if not os.path.exists(config[varName]):
    info("Could not find {} directory.".format(varName))

def setupCustomVars(usernames):
  setupVar(usernames, "HOME", getSearchDirsHome)
  setupVar(usernames, "DOCUMENTS", getSearchDirsDocuments)
  setupVar(usernames, "APPDATA", getSearchDirsAppData)
  setupVar(usernames, "APPDATALOCALLOW", getSearchDirsAppDataLocalLow)

def setupVar(usernames, varName, func):
  searchDirs = func(usernames)
  for searchDir in searchDirs:
    goodPath = False
    if os.path.exists(searchDir):
      goodPath = True
    if goodPath:
      config[varName] = searchDir
      break
  if not varName in config or not os.path.exists(config[varName]):
    warn("Could not find {} directory: {}".format(varName, searchDirs))

def getSearchDirsHome(usernames):
  searchDirs=[]
  for driveLetter in string.ascii_uppercase:
    for username in usernames:
      searchDirs.append("{}:/Users/{}".format(driveLetter, username))
  return searchDirs

def getSearchDirsDocuments(usernames):
  searchDirs=[]
  for driveLetter in string.ascii_uppercase:
    if not os.getenv("SYSTEMDRIVE").startswith(driveLetter):
      for username in usernames:
        searchDirs.append("{}:/Users/{}/Documents".format(driveLetter, username))
  for username in usernames:
    searchDirs.append("{}/Users/{}/Documents".format(os.getenv("SYSTEMDRIVE"), username))
  return searchDirs

def getSearchDirsAppData(usernames):
  return [ "{}/AppData/Roaming".format(config["HOME"]) ]

def getSearchDirsAppDataLocalLow(usernames):
  return [ "{}/AppData/LocalLow".format(config["HOME"]) ]

def setupLinks(user):
  global targetRoot
  for filePath in files:
    filePath = filePath.rstrip()
    debug("Processing \"{}\"".format(filePath))
    if filePath.startswith("#"):
      debug("Skipping comment line: \"{}\"".format(filePath))
      continue;
    if not bool(targetRoot):
      targetRoot = getPath(user, config["TargetDir"], False)
      if not os.path.exists(targetRoot):
        os.makedirs(targetRoot)
      continue
    localPath = getPath(user, filePath, False)
    remotePath = getPath(user, filePath, True)
    if not setupLink(localPath, remotePath):
      continue

def getPath(user, filePath, isRemoteSubPath):
  dirMain = filePath.split("/")[0]
  subPath = filePath[len(dirMain) + 1:]
  path = filePath
  if dirMain.startswith("$"):
    dirMain = dirMain[1:]
    if isRemoteSubPath:
      path = "{}/{}/{}".format(targetRoot, user, dirMain)
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
      path = "{}/{}/{}/{}".format(targetRoot, user, filePath[0:1], filePath[3])
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
  parentPath = pathlib.Path(copyPath).parent.absolute()
  if not parentPath.exists():
    os.makedirs(parentPath)
  if os.path.isdir(linkPath):
    debug("\"{}\" is directory".format(linkPath))
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
