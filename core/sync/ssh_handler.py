# core/sync/ssh_handler.py

import subprocess
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Tuple, Optional

@dataclass
class SSHCredentials:
    """SSH connection credentials"""
    host: str
    username: str
    password: str
    remote_path: str
    
    # Class variable to cache password
    _cached_password: Optional[str] = None
    
    def __post_init__(self):
        # Cache password for future use only if connection succeeds
        if hasattr(self, 'password') and self.password:
            SSHCredentials._cached_password = self.password

class SSHHandler:
    """Handles SSH operations using plink"""
    
    def __init__(self, credentials: SSHCredentials):
        self.credentials = credentials
        self.logger = logging.getLogger('ssh_handler')
        self.logger.setLevel(logging.DEBUG)
        
        # Add console handler if not already present
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
    def test_connection(self, invalidate_on_fail: bool = True) -> Tuple[bool, Optional[str]]:
        """
        Test SSH connection with potential password cache invalidation.
        
        Args:
            invalidate_on_fail: Whether to invalidate cached password on failure
            
        Returns:
            Tuple[bool, Optional[str]]: (success, error_message)
        """
        self.logger.debug("Testing SSH connection")
        try:
            cmd = [
                'plink',
                '-ssh',
                f'{self.credentials.username}@{self.credentials.host}',
                '-pw',
                self.credentials.password,
                '-batch',  # Non-interactive mode
                'echo "Connection test"'
            ]
            
            self.logger.debug(f"Running command: plink -ssh {self.credentials.username}@{self.credentials.host}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                self.logger.debug("SSH connection test successful")
                # Cache password only on successful connection
                SSHCredentials._cached_password = self.credentials.password
                return True, None
                
            # Check for specific error conditions
            error_msg = result.stderr.lower()
            if "authentication failed" in error_msg or "access denied" in error_msg:
                if invalidate_on_fail:
                    SSHCredentials._cached_password = None  # Clear cached password
                return False, "Authentication failed - please check your password"
            
            self.logger.error(f"SSH connection test failed: {result.stderr}")
            return False, result.stderr
            
        except subprocess.TimeoutExpired:
            self.logger.error("SSH connection timed out")
            return False, "Connection timed out - check network or server status"
        except Exception as e:
            self.logger.error(f"SSH connection error: {e}")
            return False, str(e)

    def verify_remote_path(self) -> bool:
        """Verify remote path exists and is accessible."""
        try:
            cmd = [
                'plink',
                '-ssh',
                f'{self.credentials.username}@{self.credentials.host}',
                '-pw',
                self.credentials.password,
                '-batch',
                f'test -d "{self.credentials.remote_path}" && echo "exists"'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return result.returncode == 0 and "exists" in result.stdout
            
        except Exception as e:
            self.logger.error(f"Failed to verify remote path: {e}")
            return False
            
    def copy_to_remote(self, local_path: Path, remote_path: str) -> bool:
        """Copy file to remote location."""
        try:
            cmd = [
                'pscp',
                '-pw',
                self.credentials.password,
                str(local_path),
                f'{self.credentials.username}@{self.credentials.host}:{remote_path}'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                self.logger.error(f"Error copying to remote: {result.stderr}")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to copy to remote: {e}")
            return False
            
    def copy_from_remote(self, remote_path: str, local_path: Path) -> bool:
        """Copy file from remote location."""
        try:
            cmd = [
                'pscp',
                '-pw',
                self.credentials.password,
                f'{self.credentials.username}@{self.credentials.host}:{remote_path}',
                str(local_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                error = result.stderr.lower()
                if "no such file" in error:
                    self.logger.warning(f"Remote file not found: {remote_path}")
                    return False
                self.logger.error(f"Error copying from remote: {result.stderr}")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to copy from remote: {e}")
            return False
            
    def delete_remote_file(self, remote_path: str) -> bool:
        """Delete file from remote location."""
        try:
            cmd = [
                'plink',
                '-ssh',
                f'{self.credentials.username}@{self.credentials.host}',
                '-pw',
                self.credentials.password,
                '-batch',
                f'rm "{remote_path}"'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                self.logger.error(f"Error deleting remote file: {result.stderr}")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete remote file: {e}")
            return False