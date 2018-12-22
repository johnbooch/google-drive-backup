import os
import logging
import subprocess
from argparse import ArgumentParser

# Create Parser
parser = ArgumentParser(description='Piano Steps environment script')
parser.add_argument('-m', '--mode', type=str, default='Info', help='Run deployment in debug or info mode')
parser.add_argument('-c', '--clean', action='store_true', default=False, help='Clean env directory')

# Ger setup arguments
opts = parser.parse_args()

# Setup logger
logger = logging.getLogger('Setup-Logger')
logger.setLevel(getattr(logging, opts.mode.upper()))
logger.addHandler(logging.StreamHandler()) # Prints to stderr

# Global Paths
ENV_PATH = os.path.join(os.getcwd(), 'env')
DEP_PATH = os.path.join(os.getcwd(), 'setup', 'dependencies.txt')
# Global Commands
VENV_COMMAND = "python3.7 -m virtualenv "+ENV_PATH
VENV_DEPENDENCIES = os.path.join(ENV_PATH, 'bin', 'pip')+" install -r "+DEP_PATH

# Helper functions
def clean_dir(dir):
    import shutil
    shutil.rmtree(dir)

def run_commands_seq(*cmds):
    import subprocess
    for cmd in cmds:
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        while True:
            o = p.stdout.readline().decode('utf-8')
            if o == '' and p.poll() is not None:
                break
            if o:
                logger.info(o.strip())

def setup_virtual_env(clean):
    logger.debug("Environment path: %s", ENV_PATH)
    logger.debug("Dependencies path: %s", DEP_PATH)

    if not os.path.exists(os.path.join(ENV_PATH, 'bin ')):
        run_commands_seq(VENV_COMMAND)
        logger.info("Virtual envrironment created")
    
    # Clean virtual enviroment directory
    if clean:
        logger.info("Cleaning environment directory")
        clean_dir(ENV_PATH)

    # Install dependencies 
    logger.debug("Installing dependencies from %s", DEP_PATH)
    run_commands_seq(VENV_DEPENDENCIES)
    logger.info("Dependency installation completed")
    
    logger.info("Virtual environment created successfully")

def main():
    setup_virtual_env(False)

# Call Main
if __name__ == "__main__":
    main()
    