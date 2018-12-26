
import calendar
import io
import logging
import os
import re
import shutil
import uuid
from time import sleep

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from httplib2 import Http
from oauth2client import client, tools
from oauth2client.file import Storage
from tqdm import tqdm

from lib.Utilities import GDRIVE_BACKUP_APP_AUTH_DIR, GDRIVE_BACKUP_APP_LOG_DIR
from lib.Utilities import RetryOnFailure

GDOC_MIME_TYPE_CONVERSION = {
    'application/vnd.google-apps.document': {
        'msoffice': { 'mimeType': r'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'ext': '.docx'}, 
        'pdf': { 'mimeType': r'application/pdf', 'ext': '.pdf'}    
    },
    'application/vnd.google-apps.spreadsheet': {
        'msoffice': {'mimeType': r'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'ext': '.xls'},
        'pdf': { 'mimeType': r'application/pdf', 'ext': '.pdf'}    
    },
    'application/vnd.google-apps.presentation': {
        'msoffice': {'mimeType': r'application/vnd.openxmlformats-officedocument.presentationml.presentation', 'ext': '.pptx' },
        'pdf': { 'mimeType': r'application/pdf', 'ext': '.pdf'}    
    },
    'application/vnd.google-apps.drawing': {
        'msoffice': { 'mimeType': r'application/pdf', 'ext': '.pdf'},    
        'pdf': { 'mimeType': r'application/pdf', 'ext': '.pdf'}    
    },
    'application/vnd.google-apps.script': {
        'msoffice': {'mimeType': r'application/vnd.google-apps.script+json', 'ext': '.json' },
        'pdf': {'mimeType': r'application/vnd.google-apps.script+json', 'ext': '.json' }
    }
}

MIME_TYPES = {
    'gDocRegEx': r'application/vnd\.google-apps\..+',
    'folder': r'application/vnd.google-apps.folder',
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

        # Setup downloader logging
        self.setupDownloaderLogging(self.args.logging.upper())
        
        # TODO: Crednetials should be built by another object and passed in
        # Build Credentials
        self.logLevelProgess("Getting Credentials", logging.INFO)
        self.buildCredentials(self.args.scope)
        self.logLevelProgess("Validated Credentials", logging.INFO)

    def setupDownloaderLogging(self, level):
        logger = logging.getLogger(__name__)
        logger.setLevel(level)

        logFile = os.path.join(GDRIVE_BACKUP_APP_LOG_DIR, 'google-drive-backup.log')
        logFilter = logging.Filter(name=__name__)
        
        fileHandler = logging.FileHandler(logFile, mode='w', encoding='utf-8')
        fileHandler.setLevel(level)
        fileHandler.addFilter(logFilter)

        streamHandler = logging.StreamHandler()
        streamHandler.setLevel(level)

        fileFormatter = logging.Formatter(u'%(asctime)s - %(name)' + u's - %(levelname)8s - %(message)s')
        streamFormatter = logging.Formatter(u'\r%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        fileHandler.setFormatter(fileFormatter)
        streamHandler.setFormatter(streamFormatter)

        logger.addHandler(fileHandler)
        logger.addHandler(streamHandler)

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
        # Destination needs to be an absolute path (for now)
        if not os.path.isabs(dest):
            self.logLevelProgess(u'Destination: {0} is not an absolute path'.format(dest), logging.ERROR)
            self.abortBackup()
        
        # TODO: Destination paths that already exist are not supported yet
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

    def makePath(self, path, addition):
        # Create next folder for files to be downloaded into
        new = os.path.join(path, re.sub(r'[<>:"/\\\\|?*]|\.\.\Z', '-', addition, flags=re.IGNORECASE).strip())
        
        # TODO: Support for in place backups for optimization
        if os.path.exists(new):
            new = new + uuid.uuid4().hex #TODO: We can still have hash collisions here
            self.logLevelProgess(u'Found duplicate folders at same node. Consider avoiding duplicate nodes in drive. Directory name as been changed to: {0}'.format(new), logging.WARNING)
        
        os.mkdir(new)
        return new

    def traverseSource(self, sources, directory):
        # Download files in current source directory
        [self.download(source, directory) for source in sources if self.isFile(source)]
        # Traverse through next directory
        [self.traverseSource(self.getSource(source, "'{0}' in parents".format(source['id'])), self.makePath(directory, source['name'])) for source in sources if self.isFolder(source)]
    
    def download(self, file, dest):

        #TODO: Check if file should be downloaded, for future support 
        #self.shouldDownload(file,dest)

        # Get file media
        if re.match(MIME_TYPES['gDocRegEx'], file['mimeType']):
            conversion = self.googleDocConversion(file)
            fileName = file['name'] + conversion['ext']
            request = self.service.files().export_media(fileId=file['id'], mimeType=conversion['mimeType'])
        else:
            fileName =  file['name']
            request = self.service.files().get_media(fileId=file['id'])
        
        # Build file path 
        filePath = os.path.join(dest, fileName)

        # Create media downloader
        fd = io.FileIO(filePath, mode='wb')
        downloader = MediaIoBaseDownload(fd, request, chunksize=1024*1024)

        # Create file download bar
        #fileDownloadBar = DownloadProgressbar(total=100, desc= 'File Download Progress', unit='%', leave=False)
        
        @RetryOnFailure(5, logging.getLogger(__name__)) # TODO: Magic number
        def downloadChunks(*args, **kwargs):
            done = False
            fileDownloadBar.set_postfix(file=file['name'], refresh=True)
            while done is False:
                progress, done = downloader.next_chunk()
                #fileDownloadBar.updateBar(int(progress.progress())*100, 100)
                #sleep(0.5) # Give progress bar some time to update itself
            return (progress, done)
        
        # Download
        result = downloadChunks()

        # Teardown progress bar
        #fileDownloadBar.close()

        # Check status
        if not result:
            self.logLevelProgess('Failed to download file: {0}'.format(filePath), logging.ERROR)
            if self.args.graceful:
                self.abortBackup()

        _ , done =  result

        if not done:
            self.logLevelProgess('Partial download of file: {0}'.format(file['name']), logging.ERROR)
            if self.args.graceful:
                self.abortBackup()

    def googleDocConversion(self, file):
        return GDOC_MIME_TYPE_CONVERSION[file['mimeType']][self.args.gDocConversion] 

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

class DownloadProgressbar(tqdm):
    def updateBar(self, size, totalSize):
        if totalSize is not None:
            self.total = totalSize
        self.update(size - self.n)