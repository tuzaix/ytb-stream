import subprocess
import os
import platform
from ..config import config
from ..utils import generate_random_password

class FTPService:
    def __init__(self):
        self.script_path = config.FTP_SCRIPT_PATH

    def create_user(self, username: str, quota_mb: int, speed_kbps: int) -> str:
        """
        Creates an FTP user, sets quota and speed limits.
        Returns the generated password.
        """
        print(f"[FTP Service] Creating user: {username}, Quota: {quota_mb}MB, Speed: {speed_kbps}Kbps")
        
        # Generate a secure random password
        password = generate_random_password(16)

        # 1. Call the shell script to create user
        if platform.system() == "Linux":
            try:
                # Ensure script is executable
                # subprocess.run(["chmod", "+x", self.script_path], check=True)
                
                # Run script
                # Output of script contains the password. We need to parse it.
                # The provided script prints a lot of info.
                # We might need to adjust the script to output only password or parse the output.
                # For now, we assume the script returns the password in the last line or we capture specific output.
                
                # MOCK for now since we can't run bash on Windows easily without WSL
                # In a real scenario, we would use subprocess.check_output
                pass
            except Exception as e:
                print(f"Error executing FTP script: {e}")
                raise e
        else:
            print("[FTP Service] Windows detected. Skipping actual shell script execution.")

        # 2. Apply Quota (Reserved Interface)
        self._set_quota(username, quota_mb)

        # 3. Apply Speed Limit (Reserved Interface)
        self._set_speed_limit(username, speed_kbps)

        # Return the generated password
        return password

    def _set_quota(self, username: str, quota_mb: int):
        """
        Reserved interface for setting disk quota using Linux commands (e.g., setquota).
        """
        print(f"[FTP Service] Setting disk quota for {username} to {quota_mb} MB")
        # Example: subprocess.run(["setquota", "-u", username, ...])

    def _set_speed_limit(self, username: str, speed_kbps: int):
        """
        Reserved interface for setting transfer speed limit.
        This might involve writing to vsftpd user_config_dir or using `tc`.
        """
        print(f"[FTP Service] Setting speed limit for {username} to {speed_kbps} Kbps")
        # Example: Write 'anon_max_rate=...' and 'local_max_rate=...' to /etc/vsftpd/user_conf/username

    def delete_user(self, username: str):
        """
        Deletes an FTP user.
        """
        print(f"[FTP Service] Deleting user: {username}")
        if platform.system() == "Linux":
            try:
                # Example: userdel -r username
                # subprocess.run(["userdel", "-r", username], check=True)
                pass
            except Exception as e:
                print(f"Error deleting FTP user: {e}")
                # Log error but maybe don't crash?
        else:
            print("[FTP Service] Windows detected. Skipping actual user deletion.")

    def get_base_path(self, username: str, account_name: str) -> str:
        path_template = config.BASE_FTP_HOME
        # Resolve logical path
        logical_path = path_template.format(username=username, account_name=account_name)
        
        if platform.system() == "Windows":
            # Map /home/ftp to local ftp_root for development
            project_root = r"d:\develop\ytb-stream"
            local_root = os.path.join(project_root, "ftp_root")
            
            # Extract subpath (remove /home/ftp/ prefix)
            subpath = logical_path.replace("/home/ftp/", "").replace("/", os.sep)
            return os.path.join(local_root, subpath)
        
        return logical_path

    def list_directories(self, username: str, account_name: str) -> list[str]:
        path = self.get_base_path(username, account_name)
        
        # Ensure directory exists for dev/mock purposes
        if not os.path.exists(path):
            try:
                os.makedirs(path, exist_ok=True)
                # Create dummy dirs if empty
                if not os.listdir(path):
                    os.makedirs(os.path.join(path, "shorts_demo"), exist_ok=True)
                    os.makedirs(os.path.join(path, "long_demo"), exist_ok=True)
            except Exception as e:
                print(f"Error creating/mocking directory {path}: {e}")
                return []

        try:
            items = os.listdir(path)
            dirs = [d for d in items if os.path.isdir(os.path.join(path, d))]
            return dirs
        except Exception as e:
            print(f"Error listing directories in {path}: {e}")
            return []

ftp_service = FTPService()
