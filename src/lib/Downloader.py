
import calendar
import logging
import os
import time

from oauth2client import client
from oauth2client.file import Storage
from oauth2client import tools

from googleapiclient.discovery import build
from httplib2 import Http

from lib.Utilities import GDRIVE_BACKUP_APP_DIR, GDRIVE_BACKUP_APP_AUTH_DIR, GDRIVE_BACKUP_APP_LOG_DIR

class Downloader():

    USER_AGENT = "Google-Drive-Backup-Downloader"
    
    SCOPES = {
        "DRIVE": "https://www.googleapis.com/auth/drive",
        "READONLY": "https://www.googleapis.com/auth/drive.readonly",
        "FILE": "https://www.googleapis.com/auth/drive.file"
    }

    PROGRESS_BARS = (u' ', u'▏', u'▎', u'▍', u'▌', u'▋', u'▊', u'▉', u'█')

    def __init__(self, args):
        self.args = args
        
        # Setup logging
        self.setup_logging(getattr(logging, self.args.log_level.upper()))

        # Build Credentials
        self.log_level_progress("Getting Credentials", logging.INFO)
        self.buildCredentials(self.args.scope)
        self.log_level_progress("Validated Credentials", logging.INFO)

    def setup_logging(self, level):
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

    def start_backup(self):

        # Instantiate drive services
        self.service = build('drive', "v3", self.credentials.authorize(Http(timeout=50))) #TODO: Magic Number

        # Get user info 
        self.get_user()
        self.log_level_progress(u'Drive Info:{0} {1}'.format(self.user['user']['displayName'], self.user['user']['emailAddress']), logging.INFO)

    def abort_backup(self):
        raise Exception #TODO: For now

    def get_user(self):
        try:
            self.user = self.service.about().get(fields="user").execute()
        except:
            self.log_level_progress(u'Error getting user', logging.ERROR)
            self.abort_backup()

    @staticmethod
    def log_level_progress(msg, level):
        logger = logging.getLogger(__name__)
        logger.log(level, msg)
        print(msg)
'''    
    def get_source_folder(self):
        pass

    def traverse_folder(self, folder):
        pass

    def download(self, file):
        pass

    def should_download(self, file, path):
        # Check existence 
        if not os.path.exists(path):
            return True
        # Check time
        file_time = calendar.timegm(time.strptime(file['modifiedTime'], '%Y-%m-%dT%H:%M:%S.%fZ'))
        backup_file_time = os.path.getmtime(path)
        if file_time > backup_file_time:
            return True
        else:
            return False  

    @staticmethod
    def is_file(item):
        pass

    @staticmethod
    def is_folder(item):
        pass
    
    @staticmethod
    def log_download_progess():
        pass
'''