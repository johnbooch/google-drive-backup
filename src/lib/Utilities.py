import os

GDRIVE_BACKUP_APP_DIR = os.path.join(os.path.expanduser('~'), ".google_drive_backup")
GDRIVE_BACKUP_APP_AUTH_DIR = os.path.join(os.path.join(GDRIVE_BACKUP_APP_DIR), "known_users")
GDRIVE_BACKUP_APP_LOG_DIR = os.path.join(os.path.join(GDRIVE_BACKUP_APP_DIR), "logs")

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
