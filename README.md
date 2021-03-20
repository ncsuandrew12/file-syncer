# file-syncer
Python scripts for synchronizing files (namely game save files) across multiple computers using a standard cloud storage
service.

Current limitations:

-Must be run as Administrator (can't create links otherwise)

-Must be run by the target user (can't seem to read/write file paths otherwise)

-Must use Google Drive or have another service syncing a directory named "Google Drive".

TODOs:

-Remove Administrator requirement

-Allow user to specify root file sync directory to make the script completely service-agnostic.

-Add convenience searches for additional cloud storage services: OneDrive, Dropbox.

-Package as an executable/service?

-Set up a schedule automatically?
