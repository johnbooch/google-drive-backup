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
    # Start program
    d = Downloader(args)
    d.startBackup()

if __name__ == "__main__":
    main()