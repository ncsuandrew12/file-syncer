# file-syncer
Python scripts for synchronizing files (namely game save files) across multiple computers using a standard file synchronization
service.

If you don't have Python 3 installed, install it (for free) from the Windows Store: https://www.microsoft.com/store/productId/9P7QFQMJRFP7

To configure for your own use, create cfg-user.json file in the same directory as this README file. Set "TargetDir" to your Google Drive/OneDrive/OwnCloud/Dropbox directory (or, preferably, a sub-directory of it). If you're using Google Drive, you can probably just set "TargetDir" to "$GOOGLEDRIVE/some_directory"

If you want, you can add additional games' data paths to filelist.files.

Run main.py in PowerShell with Admin privileges.

Current limitations:

-Must be run as Administrator (can't create links otherwise)

-Must be run by the target user (can't seem to read/write file paths otherwise)

-Must use Google Drive or some other file synchronization service (OneDrive/OwnCloud/Dropbox/etc.) to synchronize a directory between all relevant computers.

TODOs:

-Remove Administrator requiremen

-Add convenience searches for additional cloud storage services: OneDrive, Dropbox, OwnCloud.

-Add support for Linux.

-Package as an executable/service?

-Set up a schedule automatically?

-Derive list of disks from Windows instead of brute-forcing all possible drive letters.
