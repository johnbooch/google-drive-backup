from oauth2client import tools
from argparse import ArgumentParser

def build_drive_parser():
    parser = ArgumentParser(description="Google Drive Backup Parser", parents=[tools.argparser])
    parser.add_argument('--destination', type=str, default="~", help='Destination for downloaded files')
    parser.add_argument('--scope', type=str, default="READONLY", help="Oauth scope")
    parser.add_argument('--compression', type=str, default=None, help="Compression format for downloaded files")
    parser.add_argument('--folder', type=str, default='root', help='Folder to be backed up')
    parser.add_argument('--log_level', type=str, default="Info", help='Log' )
    
    return parser