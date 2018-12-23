
import calendar
import logging
import os
import re
import shutil
import uuid

from oauth2client import client
from oauth2client.file import Storage
from oauth2client import tools

from googleapiclient.discovery import build
from httplib2 import Http

from lib.Utilities import  GDRIVE_BACKUP_APP_AUTH_DIR, GDRIVE_BACKUP_APP_LOG_DIR

PROGRESS_BARS = (u' ', u'▏', u'▎', u'▍', u'▌', u'▋', u'▊', u'▉', u'█')

MIME_TYPES = {
    'folder': 'application/vnd.google-apps.folder'
}

class Downloader():

    USER_AGENT = "Google-Drive-Backup"
    
    SCOPES = {
        "DRIVE": "https://www.googleapis.com/auth/drive",
        "READONLY": "https://www.googleapis.com/auth/drive.readonly",
        "FILE": "https://www.googleapis.com/auth/drive.file"
    }

    def __init__(self, args):
        self.args = args
        
        # TODO: Crednetials should be built by another object and passed in
        # Build Credentials
        self.logLevelProgess("Getting Credentials", logging.INFO)
        self.buildCredentials(self.args.scope)
        self.logLevelProgess("Validated Credentials", logging.INFO)

    #TODO: I don't think credentials should be built by a downloader object. This should be passed in
    def buildCredentials(self, scope):
        # User credential file
        user_token_file = os.path.join(GDRIVE_BACKUP_APP_AUTH_DIR, "drive_python_token_file.json")  #TODO: Make this user specific
        user_creds_file = os.path.join(GDRIVE_BACKUP_APP_AUTH_DIR, "drive_python_secret_file.json") #TODO: Make this user specific

        if not os.path.exists(user_token_file):
            with open(user_token_file, 'w'): pass 
            self.logLevelProgess("Created user token file at: {0}".format(user_token_file), logging.DEBUG)

        if not os.path.exists(user_token_file):
            self.logLevelProgess("No client secrets file present at {0}. Please run google-drive-backup install <client-secrets>.json".format(GDRIVE_BACKUP_APP_AUTH_DIR), logging.ERROR)
            self.abortBackup()
        
        # Perform Oauth flow
        store = Storage(user_token_file)
        self.credentials = store.get()
        if not self.credentials or self.credentials.invalid:
            flow = client.flow_from_clientsecrets(user_creds_file, Downloader.SCOPES[scope])
            flow.user_agent = Downloader.USER_AGENT
            self.credentials = tools.run_flow(flow, store)

    def startBackup(self):

        # Instantiate drive services
        self.service = build('drive', "v3", self.credentials.authorize(Http(timeout=50))) #TODO: Magic Number

        # Get user info 
        self.getUser()
        self.logLevelProgess(u'Drive Info:{0} {1}'.format(self.user['user']['displayName'], self.user['user']['emailAddress']), logging.INFO)

        # Determine source
        sources = self.validateSource(self.args.source)
        self.logLevelProgess(u'Successfully found drive sources', logging.INFO)

        # Create destination directory
        root = self.ensureDestination(self.args.destination)
        self.logLevelProgess(u'Successfully created Google Drive Backup directory at: {0}'.format(root), logging.INFO)

        # Begin downloading from source
        self.traverseSource(sources, root)

        # File compression
        if self.args.compression:
            self.compress(self.args.compression, root)

    def abortBackup(self):
        raise Exception #TODO: For now

    def getUser(self):
        try:
            self.user = self.service.about().get(fields="user").execute()
        except:
            self.logLevelProgess(u'Error getting user', logging.ERROR)
            self.abortBackup()

    def validateSource(self, source):
        return self.getSource(source, "name='{0}' and trashed=false".format(source))    
    
    def ensureDestination(self, dest):
        if not os.path.isabs(dest):
            self.logLevelProgess(u'Destination: {0} is not an absolute path', logging.ERROR)
            self.abortBackup()
        
        if os.path.exists(dest):
            self.logLevelProgess(u'Destination: {0} already exists and is potentially storing a backup or some other data. In place backups are not yet supported.'.format(dest), logging.ERROR)
            self.abortBackup()
        os.mkdir(dest)
        return dest

    def getSource(self, source, q):
        if not source:
            self.logLevelProgess(u'Error: No source was provided', logging.ERROR)
            self.abortBackup()
        try:
            return self.service.files().list(q=q).execute()['files']
        except:
            self.logLevelProgess(u'Error getting source folder/file {0}'.format(source), logging.ERROR)
            self.abortBackup()

    def createNextSourceDirectory(self, source, currDir):
        # Create next folder for files to be downloaded into
        nextDir = os.path.join(currDir, re.sub(r'[<>:"/\\\\|?*]|\.\.\Z', '-', source['name'], flags=re.IGNORECASE).strip())
        # TODO: Support for in place backups for optimization
        if os.path.exists(nextDir):
            nextDir = nextDir + uuid.uuid4().hex #TODO: We can still have hash collisions here
            self.logLevelProgess(u'Found duplicate folders at same node. Consider avoiding duplicate nodes in drive. Directory name as been changed to: {0}'.format(nextDir), logging.WARNING)
        os.mkdir(nextDir)
        return nextDir

    def traverseSource(self, sources, directory):
        print(directory)
        # Download files in current source directory
        [self.download(source, directory) for source in sources if self.isFile(source)]
        # Traverse through next directory
        [self.traverseSource(self.getSource(source, "'{0}' in parents".format(source['id'])), self.createNextSourceDirectory(source, directory)) for source in sources if self.isFolder(source)]
    
    def download(self, file, dest):
        pass

    @staticmethod
    def compress(compression, root):
        shutil.make_archive(root, compression, root_dir=root)

    @staticmethod
    def logLevelProgess(msg, level):
        logger = logging.getLogger(__name__)
        logger.log(level, msg)

    @staticmethod
    def isFile(item):
        return item['mimeType'] != MIME_TYPES['folder']

    @staticmethod
    def isFolder(item):
        return item['mimeType'] == MIME_TYPES['folder']
    
''' 
    @staticmethod
    def logDownloadProgress():
        pass
'''