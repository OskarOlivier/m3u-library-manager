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
        
    def get_connection(self) -> Tuple[bool, Optional[str]]:
        """
        Establish SSH connection if needed.
        
        Returns:
            Tuple of (success, error_message)
        """
        if self.ssh_handler is not None:
            return True, None
            
        try:
            # Get password
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
            
            if not success:
                self.ssh_handler = None
                return False, f"SSH connection failed: {error}"
                
            # Initialize components
            self.file_comparator = FileComparator(self.ssh_handler)
            self.sync_ops = SyncOperations(
                self.ssh_handler,
                self.backup_manager,
                self.local_base,
                Config.SSH_REMOTE_PATH
            )
            
            return True, None
            
        except Exception as e:
            self.logger.error("Connection error", exc_info=True)
            return False, str(e)
            
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