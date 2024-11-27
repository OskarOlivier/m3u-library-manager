# core/sync/ssh_handler.py

import subprocess
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Tuple, Optional, Dict, Any
import asyncio
import tempfile
from utils.m3u.parser import read_m3u, write_m3u, _normalize_path

@dataclass
class SSHCredentials:
    """SSH connection credentials with caching."""
    host: str
    username: str
    password: str
    remote_path: str = "/media/CHIA/Music"  # Remote music library root
    
    # Class variable to cache password
    _cached_password: Optional[str] = None
    
    def __post_init__(self):
        # Cache password for future use only if connection succeeds
        if hasattr(self, 'password') and self.password:
            SSHCredentials._cached_password = self.password

    def get_remote_path(self, relative_path: str) -> str:
        """
        Convert a relative path to a full remote POSIX path.
        
        Args:
            relative_path: Path relative to music library root
            
        Returns:
            Full remote path with forward slashes
        """
        # Normalize to relative form and ensure forward slashes
        normalized = _normalize_path(relative_path).replace('\\', '/')
        return f"{self.remote_path}/{normalized}"

class SSHHandler:
    """Handles SSH operations using plink/pscp with consistent path handling."""
    
    def __init__(self, credentials: SSHCredentials):
        self.credentials = credentials
        
        # Set up logging
        self.logger = logging.getLogger('ssh_handler')
        self.logger.setLevel(logging.DEBUG)
        
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
            (success, error_message)
        """
        self.logger.debug("Testing SSH connection")
        try:
            cmd = [
                'plink',
                '-ssh',
                f'{self.credentials.username}@{self.credentials.host}',
                '-pw',
                self.credentials.password,
                '-batch',
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
                return True, None
                
            # Check for specific error conditions
            error_msg = result.stderr.lower()
            if "authentication failed" in error_msg or "access denied" in error_msg:
                if invalidate_on_fail:
                    SSHCredentials._cached_password = None
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
        """Verify remote music library root exists and is accessible."""
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
            exists = result.returncode == 0 and "exists" in result.stdout
            
            if not exists:
                self.logger.error(f"Remote music library not found: {self.credentials.remote_path}")
            
            return exists
            
        except Exception as e:
            self.logger.error(f"Failed to verify remote path: {e}")
            return False

    def copy_from_remote(self, remote_path: str, local_path: Path) -> bool:
        """
        Copy a file from remote to local using pscp.
        
        Args:
            remote_path: Path to remote file
            local_path: Local destination path
            
        Returns:
            bool: True if successful
        """
        try:
            cmd = [
                'pscp',
                '-pw', self.credentials.password,
                f'{self.credentials.username}@{self.credentials.host}:{remote_path}',
                str(local_path)
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True,
                timeout=30
            )
            
            if "no such file" in result.stderr.lower():
                self.logger.debug(f"Remote file not found: {remote_path}")
                return False
            
            if result.returncode != 0:
                self.logger.error(f"Error copying from remote: {result.stderr}")
                return False
                
            return True
            
        except subprocess.TimeoutExpired:
            self.logger.error("Copy operation timed out after 30 seconds")
            return False
        except Exception as e:
            self.logger.error(f"Failed to copy from remote: {e}")
            return False

    def copy_to_remote(self, local_path: Path, remote_path: str) -> bool:
        """
        Copy a file from local to remote using pscp.
        
        Args:
            local_path: Path to local file
            remote_path: Remote destination path
            
        Returns:
            bool: True if successful
        """
        try:
            cmd = [
                'pscp',
                '-pw', self.credentials.password,
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

    async def run_command(self, command: str) -> subprocess.CompletedProcess:
        """
        Run a command on the remote system asynchronously.
        
        Args:
            command: Command to execute
            
        Returns:
            CompletedProcess with command result
        """
        try:
            cmd = [
                'plink',
                '-ssh',
                f'{self.credentials.username}@{self.credentials.host}',
                '-pw',
                self.credentials.password,
                '-batch',
                command
            ]
            
            # Run command asynchronously
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=process.returncode,
                stdout=stdout.decode() if stdout else '',
                stderr=stderr.decode() if stderr else ''
            )
            
        except Exception as e:
            self.logger.error(f"Failed to run command: {e}")
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=1,
                stdout='',
                stderr=str(e)
            )