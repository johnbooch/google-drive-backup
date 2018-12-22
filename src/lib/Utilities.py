import os

GDRIVE_BACKUP_APP_DIR = os.path.join(os.path.expanduser('~'), ".google_drive_backup")
GDRIVE_BACKUP_APP_AUTH_DIR = os.path.join(os.path.join(GDRIVE_BACKUP_APP_DIR), "known_users")
GDRIVE_BACKUP_APP_LOG_DIR = os.path.join(os.path.join(GDRIVE_BACKUP_APP_DIR), "logs")