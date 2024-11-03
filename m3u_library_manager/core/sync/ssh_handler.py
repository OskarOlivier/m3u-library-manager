# core/sync/ssh_handler.py
import subprocess
from pathlib import Path
from typing import Optional, Tuple, List
import logging
from dataclasses import dataclass
import sys
import tempfile
import os

@dataclass
class SSHCredentials:
    """Stores SSH connection credentials"""
    host: str
    username: str
    password: str
    remote_path: str

class SSHCommandError(Exception):
    """Raised when an SSH command fails"""
    pass

class SSHHandler:
    """Handles SSH/SFTP command execution using PuTTY tools"""
    
    def __init__(self, credentials: SSHCredentials):
        self.credentials = credentials
        self.logger = logging.getLogger('ssh_handler')
        
        # Set up console logging
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(console_handler)
        self.logger.setLevel(logging.DEBUG)
        
    def store_host_key(self) -> Tuple[bool, Optional[str]]:
        """Store the host key using plink"""
        try:
            self.logger.info("Storing host key...")
            cmd = [
                'plink',
                '-P', '22',
                '-hostkey', 'fuJE6SEaKUUgwTvaRZiLRx+atjukkt3mWVo/ERrwmbk',
                '-pw', self.credentials.password,
                f'{self.credentials.username}@{self.credentials.host}',
                'exit'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            self.logger.debug(f"Store key stdout: {result.stdout}")
            self.logger.debug(f"Store key stderr: {result.stderr}")
            
            return True, None
            
        except Exception as e:
            self.logger.error(f"Failed to store host key: {e}")
            return False, str(e)
            
    def test_connection(self) -> Tuple[bool, Optional[str]]:
        """Test SSH connection using plink"""
        try:
            self.logger.info(f"Testing SSH connection to {self.credentials.host}")
            
            # Store host key first
            key_success, key_error = self.store_host_key()
            if not key_success:
                return False, f"Failed to store host key: {key_error}"
            
            cmd = [
                'plink',
                '-P', '22',
                '-batch',
                '-hostkey', 'fuJE6SEaKUUgwTvaRZiLRx+atjukkt3mWVo/ERrwmbk',
                '-pw', self.credentials.password,
                f'{self.credentials.username}@{self.credentials.host}',
                'echo "Connection successful"'
            ]
            
            self.logger.debug("Running plink connection test")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            self.logger.debug(f"Plink stdout: {result.stdout}")
            self.logger.debug(f"Plink stderr: {result.stderr}")
            self.logger.debug(f"Return code: {result.returncode}")
            
            if result.returncode == 0 and "Connection successful" in result.stdout:
                self.logger.info("SSH connection successful")
                return True, None
                
            self.logger.error(f"SSH connection failed: {result.stderr}")
            return False, result.stderr
            
        except subprocess.TimeoutExpired:
            error_msg = "SSH connection timed out after 10 seconds"
            self.logger.error(error_msg)
            return False, error_msg
            
        except subprocess.SubprocessError as e:
            self.logger.error(f"Plink command failed: {e}", exc_info=True)
            return False, str(e)
            
    def check_remote_file(self, remote_path: str) -> bool:
        """Check if a file exists on remote system"""
        try:
            self.logger.debug(f"Checking remote file: {remote_path}")
            cmd = [
                'plink',
                '-P', '22',
                '-batch',
                '-hostkey', 'fuJE6SEaKUUgwTvaRZiLRx+atjukkt3mWVo/ERrwmbk',
                '-pw', self.credentials.password,
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
            cmd = [
                'pscp',
                '-P', '22',
                '-batch',
                '-hostkey', 'fuJE6SEaKUUgwTvaRZiLRx+atjukkt3mWVo/ERrwmbk',
                '-pw', self.credentials.password,
                str(local_path),
                f'{self.credentials.username}@{self.credentials.host}:{remote_path}'
            ]
            
            self.logger.debug("Running pscp upload")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.logger.error(f"Failed to copy to remote: {result.stderr}")
                raise SSHCommandError(f"Failed to copy to remote: {result.stderr}")
                
            self.logger.info("Copy to remote successful")
                
        except subprocess.SubprocessError as e:
            self.logger.error(f"Failed to execute PSCP command: {e}")
            raise SSHCommandError(f"Failed to execute PSCP command: {e}")
            
    def copy_from_remote(self, remote_path: str, local_path: Path) -> None:
        """Copy file from remote system using pscp"""
        try:
            self.logger.info(f"Copying from remote via PSCP: {remote_path} -> {local_path}")
            cmd = [
                'pscp',
                '-P', '22',
                '-batch',
                '-hostkey', 'fuJE6SEaKUUgwTvaRZiLRx+atjukkt3mWVo/ERrwmbk',
                '-pw', self.credentials.password,
                f'{self.credentials.username}@{self.credentials.host}:{remote_path}',
                str(local_path)
            ]
            
            self.logger.debug("Running pscp download")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.logger.error(f"Failed to copy from remote: {result.stderr}")
                raise SSHCommandError(f"Failed to copy from remote: {result.stderr}")
                
            self.logger.info("Copy from remote successful")
                
        except subprocess.SubprocessError as e:
            self.logger.error(f"Failed to execute PSCP command: {e}")
            raise SSHCommandError(f"Failed to execute PSCP command: {e}")
            
    def delete_remote_file(self, remote_path: str) -> None:
        """Delete file on remote system"""
        try:
            self.logger.info(f"Deleting remote file: {remote_path}")
            cmd = [
                'plink',
                '-P', '22',
                '-batch',
                '-hostkey', 'fuJE6SEaKUUgwTvaRZiLRx+atjukkt3mWVo/ERrwmbk',
                '-pw', self.credentials.password,
                f'{self.credentials.username}@{self.credentials.host}',
                f'rm "{remote_path}"'
            ]
            
            self.logger.debug("Running plink delete command")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.logger.error(f"Failed to delete remote file: {result.stderr}")
                raise SSHCommandError(f"Failed to delete remote file: {result.stderr}")
                
            self.logger.info("Delete successful")
                
        except subprocess.SubprocessError as e:
            self.logger.error(f"Failed to execute remote delete command: {e}")
            raise SSHCommandError(f"Failed to execute remote delete command: {e}")