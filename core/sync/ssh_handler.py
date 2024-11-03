# core/sync/ssh_handler.py

from dataclasses import dataclass
import subprocess
import logging
from pathlib import Path
from typing import Optional, Tuple
import sys

@dataclass
class SSHCredentials:
    """Stores SSH connection credentials"""
    host: str
    username: str
    password: str
    remote_path: str
    _cached_password: Optional[str] = None  # Cache for password reuse
    
    @classmethod
    def create(cls, host: str, username: str, remote_path: str, password: Optional[str] = None):
        """Create credentials, optionally using cached password"""
        return cls(
            host=host,
            username=username,
            password=password or cls._cached_password or "",
            remote_path=remote_path,
            _cached_password=password
        )

class SSHHandler:
    """Handles SSH/SFTP command execution using PuTTY tools"""
    
    def __init__(self, credentials: SSHCredentials):
        self.credentials = credentials
        self.logger = logging.getLogger('ssh_handler')
        self._setup_logging()
        
    def _setup_logging(self):
        """Configure logging"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(console_handler)
        self.logger.setLevel(logging.DEBUG)
        
    def _get_command_base(self, tool: str) -> list:
        """Get base command list for PuTTY tools"""
        return [
            tool,
            '-P', '22',
            '-batch',
            '-pw', self.credentials.password
        ]
        
    def store_host_key(self) -> Tuple[bool, Optional[str]]:
        """Store the host key using plink"""
        try:
            # First attempt to connect without host key verification
            cmd = [
                'plink',
                '-P', '22',
                '-no-antispoof',  # Disable anti-spoofing protection
                '-pw', self.credentials.password,
                f'{self.credentials.username}@{self.credentials.host}',
                'exit'
            ]
            
            self.logger.debug(f"Running store key command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                input='y\n'  # Automatically accept host key
            )
            
            self.logger.debug(f"Store key stdout: {result.stdout}")
            self.logger.debug(f"Store key stderr: {result.stderr}")
            
            return True, None
            
        except Exception as e:
            self.logger.error(f"Failed to store host key: {e}")
            return False, str(e)
            
    def test_connection(self) -> Tuple[bool, Optional[str]]:
        """Test SSH connection"""
        try:
            # Initial connection to store host key
            key_success, key_error = self.store_host_key()
            if not key_success:
                return False, f"Failed to store host key: {key_error}"
            
            # Test actual connection
            cmd = self._get_command_base('plink') + [
                f'{self.credentials.username}@{self.credentials.host}',
                'echo "Connection successful"'
            ]
            
            self.logger.debug(f"Running test connection: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            self.logger.debug(f"Test connection stdout: {result.stdout}")
            self.logger.debug(f"Test connection stderr: {result.stderr}")
            
            if result.returncode == 0 and "Connection successful" in result.stdout:
                # Cache successful password
                SSHCredentials._cached_password = self.credentials.password
                return True, None
                
            return False, result.stderr
            
        except subprocess.TimeoutExpired:
            return False, "Connection timed out after 10 seconds"
        except Exception as e:
            return False, str(e)
            
    def check_remote_file(self, remote_path: str) -> bool:
        """Check if a file exists on remote system"""
        try:
            self.logger.debug(f"Checking remote file: {remote_path}")
            cmd = self._get_command_base('plink') + [
                f'{self.credentials.username}@{self.credentials.host}',
                f'test -f "{remote_path}" && echo "EXISTS"'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            exists = result.returncode == 0 and "EXISTS" in result.stdout
            self.logger.debug(f"File exists: {exists}")
            return exists
            
        except subprocess.SubprocessError as e:
            self.logger.error(f"Error checking remote file: {e}")
            return False
            
    def copy_to_remote(self, local_path: Path, remote_path: str) -> None:
        """Copy file to remote system using pscp"""
        try:
            self.logger.info(f"Copying to remote via PSCP: {local_path} -> {remote_path}")
            cmd = self._get_command_base('pscp') + [
                str(local_path),
                f'{self.credentials.username}@{self.credentials.host}:{remote_path}'
            ]
            
            self.logger.debug(f"Running pscp upload: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                error_msg = f"Failed to copy to remote: {result.stderr}"
                self.logger.error(error_msg)
                raise SSHCommandError(error_msg)
                
            self.logger.info("Copy to remote successful")
                
        except subprocess.SubprocessError as e:
            error_msg = f"Failed to execute PSCP command: {e}"
            self.logger.error(error_msg)
            raise SSHCommandError(error_msg)
            
    def copy_from_remote(self, remote_path: str, local_path: Path) -> None:
        """Copy file from remote system using pscp"""
        try:
            self.logger.info(f"Copying from remote via PSCP: {remote_path} -> {local_path}")
            cmd = self._get_command_base('pscp') + [
                f'{self.credentials.username}@{self.credentials.host}:{remote_path}',
                str(local_path)
            ]
            
            self.logger.debug(f"Running pscp download: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                error_msg = f"Failed to copy from remote: {result.stderr}"
                self.logger.error(error_msg)
                raise SSHCommandError(error_msg)
                
            self.logger.info("Copy from remote successful")
                
        except subprocess.SubprocessError as e:
            error_msg = f"Failed to execute PSCP command: {e}"
            self.logger.error(error_msg)
            raise SSHCommandError(error_msg)
            
    def delete_remote_file(self, remote_path: str) -> None:
        """Delete file on remote system"""
        try:
            self.logger.info(f"Deleting remote file: {remote_path}")
            cmd = self._get_command_base('plink') + [
                f'{self.credentials.username}@{self.credentials.host}',
                f'rm "{remote_path}"'
            ]
            
            self.logger.debug(f"Running plink delete command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                error_msg = f"Failed to delete remote file: {result.stderr}"
                self.logger.error(error_msg)
                raise SSHCommandError(error_msg)
                
            self.logger.info("Delete successful")
                
        except subprocess.SubprocessError as e:
            error_msg = f"Failed to execute remote delete command: {e}"
            self.logger.error(error_msg)
            raise SSHCommandError(error_msg)

class SSHCommandError(Exception):
    """Raised when an SSH command fails"""
    pass