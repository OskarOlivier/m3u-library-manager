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
        # Cache password for future use
        SSHCredentials._cached_password = self.password

class SSHHandler:
    """Handles SSH operations using plink"""
    
    def __init__(self, credentials: SSHCredentials):
        self.credentials = credentials
        self.logger = logging.getLogger('ssh_handler')
        
    def test_connection(self) -> Tuple[bool, Optional[str]]:
        """Test SSH connection"""
        try:
            cmd = [
                'plink',
                '-ssh',
                f'{self.credentials.username}@{self.credentials.host}',
                '-pw',
                self.credentials.password,
                'echo "Connection test"'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return True, None
            return False, result.stderr
            
        except subprocess.TimeoutExpired:
            return False, "Connection timed out"
        except Exception as e:
            return False, str(e)
            
    def copy_to_remote(self, local_path: Path, remote_path: str) -> bool:
        """Copy file to remote location"""
        try:
            cmd = [
                'pscp',
                '-pw',
                self.credentials.password,
                str(local_path),
                f'{self.credentials.username}@{self.credentials.host}:{remote_path}'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.logger.error(f"Error copying to remote: {result.stderr}")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to copy to remote: {e}")
            return False
            
    def copy_from_remote(self, remote_path: str, local_path: Path) -> bool:
        """Copy file from remote location"""
        try:
            cmd = [
                'pscp',
                '-pw',
                self.credentials.password,
                f'{self.credentials.username}@{self.credentials.host}:{remote_path}',
                str(local_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.logger.error(f"Error copying from remote: {result.stderr}")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to copy from remote: {e}")
            return False
            
    def delete_remote_file(self, remote_path: str) -> bool:
        """Delete file from remote location"""
        try:
            cmd = [
                'plink',
                '-ssh',
                f'{self.credentials.username}@{self.credentials.host}',
                '-pw',
                self.credentials.password,
                f'rm "{remote_path}"'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.logger.error(f"Error deleting remote file: {result.stderr}")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete remote file: {e}")
            return False