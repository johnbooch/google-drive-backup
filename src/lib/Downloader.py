
import calendar
import logging
import os
import time

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
        
        # Setup logging #TODO: This does not belong here
        self.setupLogging(getattr(logging, self.args.log_level.upper()))

        # Build Credentials
        self.log_level_progress("Getting Credentials", logging.INFO)
        self.buildCredentials(self.args.scope)
        self.log_level_progress("Validated Credentials", logging.INFO)

    #TODO: This does not belong here
    def setupLogging(self, level):
        r_logger = logging.getLogger()
        r_logger.setLevel(level)
    
        log_file = os.path.join(GDRIVE_BACKUP_APP_LOG_DIR, 'google-drive-backup.log')
        log_filter = logging.Filter(name=__name__)
        
        file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.addFilter(log_filter)
    
        class CustomStreamFilter():
            def filter(self, record):
                if record.levelname == 'ERROR' and record.exc_info:
                    return 0
                return 1
    
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel('ERROR')
        stream_handler.addFilter(CustomStreamFilter())
    
        file_formatter = logging.Formatter(u'%(asctime)s - %(name)' + u's - %(levelname)8s - %(message)s')
        stream_formatter = logging.Formatter(u'\r%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
        file_handler.setFormatter(file_formatter)
        stream_handler.setFormatter(stream_formatter)
    
        r_logger.addHandler(file_handler)
        r_logger.addHandler(stream_handler)


    def buildCredentials(self, scope):
        # User credential file
        user_token_file = os.path.join(GDRIVE_BACKUP_APP_AUTH_DIR, "drive_python_token_file.json")  #TODO: Make this user specific
        user_creds_file = os.path.join(GDRIVE_BACKUP_APP_AUTH_DIR, "drive_python_secret_file.json") #TODO: Make this user specific

        if not os.path.exists(user_token_file):
            with open(user_token_file, 'w'): pass 
            self.log_level_progress("Created user token file at: {0}".format(user_token_file), logging.DEBUG)

        if not os.path.exists(user_token_file):
            self.log_level_progress("No client secrets file present at {0}. Please run google-drive-backup install <client-secrets>.json".format(GDRIVE_BACKUP_APP_AUTH_DIR), logging.ERROR)
            self.abort_backup()
        
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
        self.get_user()
        self.log_level_progress(u'Drive Info:{0} {1}'.format(self.user['user']['displayName'], self.user['user']['emailAddress']), logging.INFO)

        # Determine source
        source = self.validate_source(self.args.source)
        self.log_level_progress(u'Successfully found drive sources', logging.INFO)

        # Begin downloading from source
        self.traverse_source(source)

    def abort_backup(self):
        raise Exception #TODO: For now

    def get_user(self):
        try:
            self.user = self.service.about().get(fields="user").execute()
        except:
            self.log_level_progress(u'Error getting user', logging.ERROR)
            self.abort_backup()

    def validate_source(self, source):
        return self.get_source(source, "name='{0}' and trashed=false".format(source))    

    def get_source(self, source, q):
        if not source:
            self.log_level_progress(u'Error: No source was provided', logging.ERROR)
            self.abort_backup()
        try:
            return self.service.files().list(q=q).execute()['files']
        except:
            self.log_level_progress(u'Error getting source folder/file {0}'.format(source), logging.ERROR)
            self.abort_backup()

    def traverse_source(self, sources):
        print(sources)
        # Download files in current source directory
        [self.download(source) for source in sources if self.isFile(source)]
        # Traverse through next directory
        [self.traverse_source(self.get_source(source, "'{0}' in parents".format(source['id']))) for source in sources if self.isFolder(source)]
    
    def download(self, file):
        self.log_level_progress('Downloading file: {0}'.format(file['name']), logging.DEBUG)

    @staticmethod
    def log_level_progress(msg, level):
        logger = logging.getLogger(__name__)
        logger.log(level, msg)
        print(msg)

    @staticmethod
    def isFile(item):
        return item['mimeType'] != MIME_TYPES['folder']

    @staticmethod
    def isFolder(item):
        return item['mimeType'] == MIME_TYPES['folder']
    
''' 
    @staticmethod
    def log_download_progess():
        pass
'''