from passlib.context import CryptContext
import secrets
import string
import os
import platform
from .config import config

# Use argon2 instead of bcrypt to avoid passlib+bcrypt issues
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def generate_random_password(length=12):
    """Generate a secure random password."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(length))

def get_youtube_auth_path(username: str, account_name: str) -> str:
    """
    Generate the absolute path for storing YouTube auth files.
    Handles cross-platform path resolution (Windows/Linux).
    """
    path_template = config.YOUTUBE_AUTH_FILES_HOME
    logical_path = path_template.format(username=username, account_name=account_name)
    
    if platform.system() == "Windows":
        # Map /home/youtube_auth_files to local directory for development
        project_root = r"d:\develop\ytb-stream"
        local_root = os.path.join(project_root, "youtube_auth_files")
        
        # Extract subpath (remove /home/youtube_auth_files/ prefix)
        prefix = "/home/youtube_auth_files/"
        if logical_path.startswith(prefix):
            subpath = logical_path[len(prefix):]
        else:
            # Fallback if path structure is different
            subpath = f"{username}/{account_name}"
            
        subpath = subpath.replace("/", os.sep)
        return os.path.join(local_root, subpath)
    
    return logical_path
