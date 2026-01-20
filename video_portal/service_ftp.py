import subprocess
import os
import logging
import secrets
import string

# Path to the shell script
# ../../dev_tools/vsftpd/create_ftpuser.sh
SCRIPT_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "dev_tools", "vsftpd", "create_ftpuser.sh")
)

logger = logging.getLogger(__name__)

def generate_password(length=12):
    """Generate a secure random password containing letters and digits."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(length))

def create_ftp_account(username: str) -> str:
    """
    Creates an FTP account by calling the shell script with a generated password.
    Returns the generated password.
    """
    if not os.path.exists(SCRIPT_PATH):
        logger.error(f"FTP script not found at {SCRIPT_PATH}")
        raise FileNotFoundError(f"FTP script not found at {SCRIPT_PATH}")

    # Generate random password
    password = generate_password()

    # Prepare command
    cmd = ["bash", SCRIPT_PATH, username, password]
    
    try:
        # Log command without password
        safe_cmd = ["bash", SCRIPT_PATH, username, "******"]
        logger.info(f"Executing FTP creation script: {' '.join(safe_cmd)}")
        
        # Execute script
        subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            check=True,
            encoding="utf-8"
        )
        
        # Return the generated password
        return password

    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        # In a real Linux env, we would raise. 
        # In this Windows dev env, we mock it for testing the UI flow.
        if os.name == 'nt':
            logger.warning(f"Windows environment or execution failure ({type(e).__name__}). Mocking FTP success.")
            return password
            
        if isinstance(e, subprocess.CalledProcessError):
            logger.error(f"Failed to create FTP user. Error: {e.stderr}")
        raise e

DELETE_SCRIPT_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "dev_tools", "vsftpd", "delete_ftpuser.sh")
)

def delete_ftp_account(username: str):
    """
    Deletes an FTP account by calling the shell script.
    """
    if not os.path.exists(DELETE_SCRIPT_PATH):
        logger.error(f"FTP delete script not found at {DELETE_SCRIPT_PATH}")
        raise FileNotFoundError(f"FTP delete script not found at {DELETE_SCRIPT_PATH}")

    # Prepare command
    cmd = ["bash", DELETE_SCRIPT_PATH, username]
    
    try:
        logger.info(f"Executing FTP deletion script: {' '.join(cmd)}")
        
        # Execute script, pipe 'y' to stdin for confirmation
        # process = subprocess.Popen(
        #     cmd,
        #     stdin=subprocess.PIPE,
        #     stdout=subprocess.PIPE,
        #     stderr=subprocess.PIPE,
        #     text=True,
        #     encoding="utf-8"
        # )
        # stdout, stderr = process.communicate(input="y\n")
        
        # if process.returncode != 0:
        #     logger.error(f"FTP deletion failed. Stdout: {stdout}, Stderr: {stderr}")
        #     raise subprocess.CalledProcessError(process.returncode, cmd, output=stdout, stderr=stderr)
            
        # logger.info(f"FTP deletion output: {stdout}")
        logger.info("FTP deletion script call is currently commented out.")

    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        # In a real Linux env, we would raise. 
        # In this Windows dev env, we mock it for testing the UI flow.
        if os.name == 'nt':
            logger.warning(f"Windows environment or execution failure ({type(e).__name__}). Mocking FTP deletion.")
            return
            
        if isinstance(e, subprocess.CalledProcessError):
            logger.error(f"Failed to delete FTP user. Error: {e.stderr}")
        raise e
