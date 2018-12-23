from oauth2client import tools
from argparse import ArgumentParser

def build_drive_parser():
    parser = ArgumentParser(description='Google Drive Backup CLI Parser', parents=[tools.argparser])
    parser.add_argument('--source', type=str, default = None, help= 'Source folder or file to backup' )
    parser.add_argument('--destination', type=str, default="~", help='Destination for backup to be stored')
    parser.add_argument('--compression', type=str, default= None, choices=['ZIP','TAR', 'GZ'], help='Compression format for downloaded files')
    parser.add_argument('--scope', type=str, default='READONLY', choices=['READONLY', 'FILE', 'DRIVE'], help='OAuth 2.0 scope (Must match OAuth Sceret File)')
    parser.add_argument('--folder', type=str, default='root', help='Folder to be backed up')
    parser.add_argument('--log_level', type=str, default="Info", help='Log' )
    
    return parser