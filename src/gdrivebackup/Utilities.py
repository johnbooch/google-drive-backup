import os

GDRIVE_BACKUP_APP_DIR = os.path.join(os.path.expanduser('~'), ".google_drive_backup")
GDRIVE_BACKUP_APP_AUTH_DIR = os.path.join(os.path.join(GDRIVE_BACKUP_APP_DIR), "known_users")
GDRIVE_BACKUP_APP_LOG_DIR = os.path.join(os.path.join(GDRIVE_BACKUP_APP_DIR), "logs")


from shutil import get_archive_formats
from argparse import ArgumentParser

from oauth2client import tools

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

def build_drive_parser():
    parser = ArgumentParser(description='Google Drive Backup CLI Parser', parents=[tools.argparser])
    parser.add_argument('--source', type=str, default = None, help= 'Source folder or file to backup' )
    parser.add_argument('--destination', type=str, default="~", help='Destination for backup to be stored')
    parser.add_argument('--graceful', action='store_true', help='Backup must be graceful, i.e no downloads are allowed to fail. Non-graceful backups will mark corrupted files')
    parser.add_argument('--compression', type=str, default= None, choices=[fmt[0] for fmt in get_archive_formats()], help='Compression format for downloaded files')
    parser.add_argument("--gDocConversion", type=str, choices=['msoffice', 'pdf'], default='pdf', help='Google Doc mime type conversion')
    parser.add_argument('--scope', type=str, default='READONLY', choices=['READONLY', 'FILE', 'DRIVE'], help='OAuth 2.0 scope (Must match OAuth Credentials File)')
    parser.add_argument('--logging', type=str, default="Info", help='Log' )
    
    return parser

def RetryOnFailure(retries, logger):
    def RetryOnFailureDecorator(fn):
        def retry(*args, **kwargs):
            for _ in range(retries):
                try:
                    return fn(args, kwargs)
                except Exception as e:
                    if logger:
                        logger.warning('Exception: {0}. Retrying...'.format(str(e)))
                    continue
            if logger:
                logger.error('Error executing task')
            return None
        return retry
    return RetryOnFailureDecorator 
