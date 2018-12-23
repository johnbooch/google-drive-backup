import logging
import os

from lib import Parser
from lib import Downloader
from lib import GDRIVE_BACKUP_APP_DIR, GDRIVE_BACKUP_APP_AUTH_DIR, GDRIVE_BACKUP_APP_LOG_DIR

__author__ = 'John Buccieri'
__version__ = '1.0'

PROG_MSG = r'''

   _____                   _        _____       _             ____             _                  __   ___  
  / ____|                 | |      |  __ \     (_)           |  _ \           | |                /_ | / _ \ 
 | |  __  ___   ___   __ _| | ___  | |  | |_ __ ___   _____  | |_) | __ _  ___| | ___   _ _ __    | || | | |
 | | |_ |/ _ \ / _ \ / _` | |/ _ \ | |  | | '__| \ \ / / _ \ |  _ < / _` |/ __| |/ / | | | '_ \   | || | | |
 | |__| | (_) | (_) | (_| | |  __/ | |__| | |  | |\ V /  __/ | |_) | (_| | (__|   <| |_| | |_) |  | || |_| |
  \_____|\___/ \___/ \__, |_|\___| |_____/|_|  |_| \_/ \___| |____/ \__,_|\___|_|\_\__,_| .__/    |_(_)___/ 
                      __/ |                                                              | |                
                     |___/                                                               |_|                
'''


def setupLogging(level):
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
    stream_handler.setLevel(level)
    stream_handler.addFilter(CustomStreamFilter())

    file_formatter = logging.Formatter(u'%(asctime)s - %(name)' + u's - %(levelname)8s - %(message)s')
    stream_formatter = logging.Formatter(u'\r%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    file_handler.setFormatter(file_formatter)
    stream_handler.setFormatter(stream_formatter)

    r_logger.addHandler(file_handler)
    r_logger.addHandler(stream_handler)


def build_application_scaffold():

    # Create application directory in user directory
    if not os.path.exists(GDRIVE_BACKUP_APP_DIR):
        os.mkdir(GDRIVE_BACKUP_APP_DIR)
    
    # Create application auth directory in application directory
    if not os.path.exists(GDRIVE_BACKUP_APP_AUTH_DIR):
        os.mkdir(GDRIVE_BACKUP_APP_AUTH_DIR)

    # Create application logs directory in application directory
    if not os.path.exists(GDRIVE_BACKUP_APP_LOG_DIR):
        os.mkdir(GDRIVE_BACKUP_APP_LOG_DIR)

def show_prog_msg():
    print(PROG_MSG, __author__, sep='\n')

def main():
    # Show program message
    show_prog_msg()
    # Build applicatio scaffold 
    build_application_scaffold()
    # Parse args
    args = Parser.build_drive_parser().parse_args()
    # Setup Logging
    setupLogging(getattr(logging, args.log_level.upper()))
    # Start program
    d = Downloader(args)
    d.startBackup()

if __name__ == "__main__":
    main()