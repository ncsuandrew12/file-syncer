import os
import pathlib
import shutil
import subprocess

cGoogleDriveVariants=[ "Google Drive", "Google_Drive", "google-drive" ]
files=[]
logFile=None
targetRoot=None
sysVars={}

def log(message, important=False):
  global files
  global logFile
  if important:
    print(message)
  if not logFile:
    logFile = open("setup-game-symlinks.log", "a+")
    files.insert(0, logFile)
    print("", file=logFile)
    print("", file=logFile)
    print("========================================================================================================================", file=logFile)
    print("========================================================================================================================", file=logFile)
    print("========================================================================================================================", file=logFile)
  print("{}: {}".format(os.getenv("COMPUTERNAME"), message), file=logFile)

def getPath(filePath, isRemoteSubPath):
  dirMain = filePath.split("/")[0]
  subPath = filePath[len(dirMain) + 1:]
  path = filePath
  if dirMain.startswith("$"):
    dirMain = dirMain[1:]
    if isRemoteSubPath:
      path = "{}/{}".format(targetRoot, dirMain)
    else:
      if dirMain in sysVars:
        sysVar=sysVars[dirMain]
        if sysVar == "GOOGLEDRIVE":
          for gdrive in cGoogleDriveVariants:
            path = getPath("$HOME/Documents/{}".format(gdrive), False)
            if os.path.exists(path):
              break
            for username in sysVars["USERNAMES"]:
              if os.path.exists(path):
                break
              path = "E:/Users/{}/{}".format(username, gdrive) # TODO
          if not os.path.exists(path):
            raise Exception("Could not locate {}: {}".format(dirMain, subPath))
        else:
          raise Exception("Unknown var {} ({})".format(sysVar, dirMain))
      elif dirMain == "HOME":
        path = "{}:{}".format(os.getenv("SYSTEMDRIVE"), os.getenv("HOMEPATH"))
        for username in sysVars["USERNAMES"]:
          if os.path.exists(path):
            break
          path = "E:/Users/{}/{}".format(username, dirMain) # TODO
      else:
        path = os.getenv(dirMain)
        if not os.path.exists(path):
          raise Exception("Could not locate {}: {}", dirMain, path)
    path = "{}/{}".format(path, subPath)
  elif ":" in filePath:
    if isRemoteSubPath:
      path = "{}/{}/{}".format(targetRoot, filePath[0:1], filePath[3])
  else:
    raise Exception("Paths must begin with $<var> or a drive letter. Problematic path: {}", filePath)
  return path

listFile = open("setup-game-symlinks.files", "r")
files.insert(0, listFile)
try:
  for filePath in listFile:
    filePath = filePath.rstrip()
    log("Processing '{}'".format(filePath))

    if filePath.startswith("#"):
      log("Skipping comment line: {}".format(filePath))
      continue;

    if filePath.startswith(">"):
      parts=filePath.split("=")
      varName=parts[0][1:]
      varVal=parts[1]
      if varName == "ALTUSERNAMES":
        varVal=varVal.split(",")
        varVal.insert(0, os.getenv("USERNAME"))
        sysVars["USERNAMES"]=varVal
      else:
        varVal=filePath[len(varName) + 2:]
        sysVars[varName]=varVal
      continue

    if not bool(targetRoot):
      targetRoot = getPath(sysVars["TARGETDIR"], False)
      if not os.path.exists(targetRoot):
        raise Exception("Target root directory does not exist: {}".format(targetRoot))
      continue

    localPath = getPath(filePath, False)
    remotePath = getPath(filePath, True)

    log("{} -> {}".format(localPath, remotePath))

    if os.path.islink(localPath):
      log("Skipping {} because it is already a symlink".format(localPath))
      continue

    if not pathlib.Path(localPath).exists():
      log("Skipping {} because it doesn't exist".format(localPath))
      continue

    copyPath = remotePath
    if pathlib.Path(remotePath).exists():
      remotePathBak = remotePath
      i=1
      while pathlib.Path(remotePathBak).exists():
        remotePathBak = "{}-bak-{}".format(remotePath, i)
        i+=1
      log("{} already exists. Will backup local files to {}".format(remotePath, remotePathBak), True)
      copyPath = remotePathBak

    if os.path.isdir(localPath):
      log("{} is directory".format(localPath))
      parentPath = pathlib.Path(copyPath).parent.absolute()
      if not parentPath.exists():
        os.makedirs(parentPath)
      shutil.copytree(localPath, copyPath)
      shutil.rmtree(localPath)
      remotePath = remotePath + "/"
      log("Linking {} -> {}".format(localPath, remotePath), True)
      subprocess.call(["setup-game-symlink.bat", localPath, remotePath])
    elif os.path.isfile(localPath):
      log("{} is file".format(localPath))
      shutil.copy(localPath, copyPath)
      os.remove(localPath)
      log("Linking {} -> {}".format(localPath, remotePath), True)
      subprocess.call(["setup-game-symlink.bat", localPath, remotePath])
    else:
      log("ERROR: {} is neither symlink, directory, nor file".format(localPath), True)
finally:
  for file in files:
    try:
      file.close()
    except Exception as e:
      log(e, True)
