# gui/windows/pages/sync/handlers/connection_handler.py

import logging
from typing import Optional, Tuple
from pathlib import Path

from app.config import Config
from core.sync.ssh_handler import SSHHandler, SSHCredentials
from core.sync.file_comparator import FileComparator
from core.sync.sync_operations import SyncOperations
from core.sync.backup_manager import BackupManager
from gui.dialogs.credentials_dialog import PasswordDialog

class ConnectionHandler:
    """Handles SSH connection and related components."""
    
    def __init__(self):
        self.logger = logging.getLogger('connection_handler')
        
        self.ssh_handler: Optional[SSHHandler] = None
        self.file_comparator: Optional[FileComparator] = None
        self.sync_ops: Optional[SyncOperations] = None
        
        # Initialize paths and managers
        self.local_base = Path(Config.LOCAL_BASE)
        self.backup_manager = BackupManager(Path(Config.BACKUP_DIR))
        
    def get_connection(self, max_attempts: int = 3) -> Tuple[bool, Optional[str]]:
        """
        Establish SSH connection if needed, with retry attempts.
        
        Args:
            max_attempts: Maximum number of password attempts
            
        Returns:
            Tuple[bool, Optional[str]]: (success, error_message)
        """
        if self.ssh_handler is not None:
            return True, None
            
        attempt = 0
        last_error = None
        
        while attempt < max_attempts:
            try:
                # Get password (cached or from user)
                password = self._get_password()
                if not password:
                    return False, "SSH connection cancelled"
                    
                # Setup credentials
                credentials = SSHCredentials(
                    host=Config.SSH_HOST,
                    username=Config.SSH_USERNAME,
                    password=password,
                    remote_path=Config.SSH_REMOTE_PATH
                )
                
                # Create and test connection
                self.ssh_handler = SSHHandler(credentials)
                success, error = self.ssh_handler.test_connection()
                
                if success:
                    # Initialize components on successful connection
                    self.file_comparator = FileComparator(self.ssh_handler)
                    self.sync_ops = SyncOperations(
                        self.ssh_handler,
                        self.backup_manager,
                        self.local_base,
                        Config.SSH_REMOTE_PATH
                    )
                    
                    # Verify remote path
                    if not self.ssh_handler.verify_remote_path():
                        return False, f"Remote path not accessible: {Config.SSH_REMOTE_PATH}"
                    
                    return True, None
                    
                # Handle authentication failures
                if "authentication failed" in str(error).lower():
                    self.logger.warning(f"Authentication failed, attempt {attempt + 1}/{max_attempts}")
                    SSHCredentials._cached_password = None  # Clear cached password
                    last_error = error
                    attempt += 1
                    continue
                    
                # Other errors are terminal
                self.ssh_handler = None
                return False, f"SSH connection failed: {error}"
                
            except Exception as e:
                self.logger.error("Connection error", exc_info=True)
                return False, str(e)
                
        # Max attempts reached
        return False, f"Authentication failed after {max_attempts} attempts"
            
    def _get_password(self) -> Optional[str]:
        """Get SSH password from cache or user."""
        if SSHCredentials._cached_password:
            return SSHCredentials._cached_password
            
        dialog = PasswordDialog()
        result = dialog.get_credentials()
        
        return result.password if result.accepted else None
        
    def cleanup(self):
        """Clean up connection resources."""
        self.ssh_handler = None
        self.file_comparator = None
        self.sync_ops = None