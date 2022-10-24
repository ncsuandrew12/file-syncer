# file-syncer
Python script for synchronizing files (namely game save files) across multiple computers using a standard file synchronization
service.

## How it Works

Basically, file-syncer looks for any existing files or directories that are listed in filelist.files. For each one it finds, it moves it to the common specified directory (`TargetDir`). It then creates a symlink from the old location to the new location. The common directory (`TargetDir`) should be a mirrored directory (using e.g. Google Drive/OneDrive/OwnCloud/Dropbox).

## Prerequisites

- Python 3. Can be installed for free from the [Windows Store](https://www.microsoft.com/store/productId/9P7QFQMJRFP7) or from the [Python website](https://www.python.org/downloads/).

## How to Use

To configure for your own use, create cfg-user.json file in the same directory as this README file. Set "TargetDir" to your Google Drive/OneDrive/OwnCloud/Dropbox directory (or, preferably, a sub-directory of it). If you're using Google Drive, you can probably just set `TargetDir` to `$GOOGLEDRIVE/some_directory`.

Example cfg-user.json file:

```
{
  "UserNameAliases": {
    "andrew": [
      "drew",
      "andy"
    ]
  },
  "TargetDir": "$GOOGLEDRIVE/my-game-files",
  "GOOGLEDRIVE": "C:/Users/andrew/google-drive"
}
```

**NOTE**: It may not be necessary to specify `GOOGLEDRIVE`. The script will attempt to locate your Google Drive directory automatically.

If you want, you can add additional games' data paths to filelist.files. You can specify full absolute paths, or you can use any of these placeholder variables:

- `HOME` - User's home directory
- `APPDATA` - User's Windows AppData directory (i.e. `$HOME/AppData`)
- `APPDATALOCALLOW` - User's Windows AppData/LocalLow directory (i.e. `$HOME/AppData/LocalLow`)
- `DOCUMENTS` - User's Windows **Documents** library path
- `MUSIC` - User's Windows **Music** library path
- `PICTURES` - User's Windows **Pictures** library path
- `VIDEOS` - User's Windows **Videos** library path

Run main.py in PowerShell with Admin privileges.

**WARNING**: The script will delete link files under certain circumstances. If (a) the file/directory in filelist.files already exists and is a broken symlink, and (b) the file/directory already exists in `TargetDir`, then the script will delete the existing symlink and create a new one pointing to the existing target. This is useful if you have moved `TargetDir` (for example, to a different drive). The log files will contain the the delete symlink file paths and their targets.

**WARNING**: For performance-sensitive applications (e.g. game files), we *strongly* recommmend against using a "streamed" directory for your file synchronization. If you are using Google Drive, then either (a) configure Google Drive to mirror your entire Google Drive, or (b) set `TargetDir` to be available offline.

**NOTE**: Existing files/directories under `TargetDir` will be renamed to *filename*-bak-*N* when both (a) they already exist and (b) the file/directory in filelist.files exists and is being moved by the script.

## Current Limitations

- Must be run as Administrator (can't create links otherwise)

- Must be run by the target user (can't seem to read/write file paths otherwise)

- Must use Google Drive or some other file synchronization service (OneDrive/OwnCloud/Dropbox/etc.) to synchronize a directory between all relevant computers.

## Future Work

- Remove Administrator requirement

- Add convenience searches for additional cloud storage services: OneDrive, Dropbox, OwnCloud.

- Add support for Linux.

- Package as an executable/service?

- Set up a schedule automatically?

- Derive list of disks from Windows instead of brute-forcing all possible drive letters.
