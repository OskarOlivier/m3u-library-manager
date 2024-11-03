# gui/windows/pages/sync_page.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QListWidget, QFrame, QProgressBar,
                           QMessageBox, QApplication, QListWidgetItem)
from PyQt6.QtCore import Qt, QThread
from PyQt6.QtGui import QFont
from pathlib import Path
from typing import Set, Optional
import asyncio

from . import BasePage
from gui.dialogs.credentials_dialog import PasswordDialog, SSHCredentialsResult
from gui.workers.sync_workers import ComparisonWorker, SyncWorker
from gui.widgets.sync_widgets import FileListWidget
from core.sync.ssh_handler import SSHHandler, SSHCredentials
from core.sync.file_comparator import FileComparator
from core.sync.sync_operations import SyncOperations
from core.sync.backup_manager import BackupManager
from utils.logging.sync_logger import SyncLogger

class SyncPage(BasePage):
    """Sync page implementation"""
    def __init__(self):
        self.local_base = Path(r"E:\Albums")
        self.backup_dir = Path(r"D:\Music\Dopamine\Playlists\backups")
        self.playlists_dir = Path(r"D:\Music\Dopamine\Playlists")
        
        # Fixed SSH credentials
        self.SSH_HOST = "192.168.178.43"
        self.SSH_USERNAME = "pi"
        self.SSH_REMOTE_PATH = "/media/CHIA/Music"
        
        self.ssh_handler = None
        self.file_comparator = None
        self.sync_ops = None
        self.backup_manager = BackupManager(self.backup_dir)
        self.sync_logger = SyncLogger(self.backup_dir / "logs")
        
        self.current_playlist = None
        self.comparison_worker = None
        self.sync_worker = None
        
        super().__init__()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Left column - Playlist list
        left_column = self.create_playlist_column()
        
        # Middle column - Missing Remotely
        middle_column = self.create_missing_remote_column()
        
        # Right column - Missing Locally
        right_column = self.create_missing_local_column()
        
        # Add columns to main layout
        column_container = QHBoxLayout()
        for column in [left_column, middle_column, right_column]:
            frame = QFrame()
            frame.setLayout(column)
            frame.setStyleSheet("""
                QFrame {
                    background-color: #202020;
                    border: none;
                    border-radius: 2px;
                }
            """)
            column_container.addWidget(frame)
        
        # Create status area at bottom
        status_container = QVBoxLayout()
        status_container.setSpacing(8)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setFont(QFont("Segoe UI", 10))
        self.status_label.setStyleSheet("color: white;")
        status_container.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 2px;
                text-align: center;
                background-color: #2D2D2D;
                color: white;
                height: 8px;
            }
            QProgressBar::chunk {
                background-color: #0078D4;
                border-radius: 2px;
            }
        """)
        status_container.addWidget(self.progress_bar)
        
        # Combine layouts
        main_layout = QVBoxLayout()
        main_layout.addLayout(column_container)
        main_layout.addLayout(status_container)
        
        # Set the main layout
        container = QWidget()
        container.setLayout(main_layout)
        layout.addWidget(container)
        
        # Disable sync buttons initially
        self.set_sync_buttons_enabled(False)
        
        # Load initial playlists
        self.refresh_playlists()
        
    def set_sync_buttons_enabled(self, enabled: bool):
        """Enable or disable sync buttons"""
        for btn in [self.add_remote_btn, self.delete_local_btn,
                   self.add_local_btn, self.delete_remote_btn]:
            btn.setEnabled(enabled)
            
    def create_playlist_column(self) -> QVBoxLayout:
        """Create the playlist list column"""
        layout = QVBoxLayout()
        
        # Header
        header = QHBoxLayout()
        playlist_label = QLabel("Playlists")
        playlist_label.setFont(QFont("Segoe UI", 11))
        playlist_label.setStyleSheet("color: white;")
        header.addWidget(playlist_label)
        
        # Add Analyze All button
        self.analyze_all_btn = QPushButton("Analyze All")
        self.analyze_all_btn.clicked.connect(self.on_analyze_all_clicked)
        header.addWidget(self.analyze_all_btn)
        
        # Add playlist count label
        self.playlist_count_label = QLabel()
        self.playlist_count_label.setFont(QFont("Segoe UI", 10))
        self.playlist_count_label.setStyleSheet("color: #999999;")
        self.playlist_count_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        header.addWidget(self.playlist_count_label)
        
        layout.addLayout(header)
        
        # Playlist list
        self.playlist_list = QListWidget()
        self.playlist_list.itemClicked.connect(self.on_playlist_selected)
        self.playlist_list.setStyleSheet("""
            QListWidget {
                background-color: #2D2D2D;
                border: none;
                border-radius: 2px;
            }
            QListWidget::item {
                color: white;
                padding: 8px;
            }
            QListWidget::item:hover {
                background-color: #404040;
            }
            QListWidget::item:selected {
                background-color: #0078D4;
            }
        """)
        layout.addWidget(self.playlist_list)
        
        # Analyze button
        analyze_btn = QPushButton("Analyze")
        analyze_btn.clicked.connect(self.on_analyze_clicked)
        layout.addWidget(analyze_btn)
        
        return layout
        
    def create_missing_remote_column(self) -> QVBoxLayout:
        """Create the missing remotely column"""
        layout = QVBoxLayout()
        
        # Header
        header = QHBoxLayout()
        label = QLabel("Missing Remotely")
        label.setFont(QFont("Segoe UI", 11))
        label.setStyleSheet("color: white;")
        header.addWidget(label)
        
        # Count label
        self.remote_count_label = QLabel()
        self.remote_count_label.setFont(QFont("Segoe UI", 10))
        self.remote_count_label.setStyleSheet("color: #999999;")
        self.remote_count_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        header.addWidget(self.remote_count_label)
        
        layout.addLayout(header)
        
        # File list
        self.missing_remote_list = FileListWidget()
        layout.addWidget(self.missing_remote_list)
        
        # Action buttons
        buttons = QHBoxLayout()
        self.add_remote_btn = QPushButton("Add to Remote")
        self.add_remote_btn.clicked.connect(lambda: self.on_sync_clicked('add_remote'))
        self.delete_local_btn = QPushButton("Delete from Local")
        self.delete_local_btn.clicked.connect(lambda: self.on_sync_clicked('delete_local'))
        buttons.addWidget(self.add_remote_btn)
        buttons.addWidget(self.delete_local_btn)
        layout.addLayout(buttons)
        
        # Check buttons
        check_buttons = QHBoxLayout()
        check_all = QPushButton("Check All")
        check_all.clicked.connect(lambda: self.missing_remote_list.set_all_checked(True))
        uncheck_all = QPushButton("Uncheck All")
        uncheck_all.clicked.connect(lambda: self.missing_remote_list.set_all_checked(False))
        check_buttons.addWidget(check_all)
        check_buttons.addWidget(uncheck_all)
        layout.addLayout(check_buttons)
        
        return layout
        
    def create_missing_local_column(self) -> QVBoxLayout:
        """Create the missing locally column"""
        layout = QVBoxLayout()
        
        # Header
        header = QHBoxLayout()
        label = QLabel("Missing Locally")
        label.setFont(QFont("Segoe UI", 11))
        label.setStyleSheet("color: white;")
        header.addWidget(label)
        
        # Count label
        self.local_count_label = QLabel()
        self.local_count_label.setFont(QFont("Segoe UI", 10))
        self.local_count_label.setStyleSheet("color: #999999;")
        self.local_count_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        header.addWidget(self.local_count_label)
        
        layout.addLayout(header)
        
        # File list
        self.missing_local_list = FileListWidget()
        layout.addWidget(self.missing_local_list)
        
        # Action buttons
        buttons = QHBoxLayout()
        self.add_local_btn = QPushButton("Add to Local")
        self.add_local_btn.clicked.connect(lambda: self.on_sync_clicked('add_local'))
        self.delete_remote_btn = QPushButton("Remove from Remote")
        self.delete_remote_btn.clicked.connect(lambda: self.on_sync_clicked('delete_remote'))
        buttons.addWidget(self.add_local_btn)
        buttons.addWidget(self.delete_remote_btn)
        layout.addLayout(buttons)
        
        # Check buttons
        check_buttons = QHBoxLayout()
        check_all = QPushButton("Check All")
        check_all.clicked.connect(lambda: self.missing_local_list.set_all_checked(True))
        uncheck_all = QPushButton("Uncheck All")
        uncheck_all.clicked.connect(lambda: self.missing_local_list.set_all_checked(False))
        check_buttons.addWidget(check_all)
        check_buttons.addWidget(uncheck_all)
        layout.addLayout(check_buttons)
        
        return layout
        
    def refresh_playlists(self):
        """Load playlists into list"""
        self.playlist_list.clear()
        playlists = sorted(p for p in self.playlists_dir.glob("*.m3u") 
                         if p.name != "Love.bak.m3u")  # Skip backup playlist
        
        for playlist in playlists:
            self.add_playlist_item(playlist)
            
        # Update count
        self.playlist_count_label.setText(f"{len(playlists)} playlists")
        
    def add_playlist_item(self, playlist_path: Path, missing_remote: int = None, missing_local: int = None):
        """Add playlist item with optional sync status"""
        display_name = playlist_path.name
        if missing_remote is not None and missing_local is not None:
            display_name = f"{playlist_path.name} ({missing_remote}, {missing_local})"
            
        item = QListWidgetItem(display_name)
        item.setData(Qt.ItemDataRole.UserRole, str(playlist_path))
        self.playlist_list.addItem(item)
        
    def on_playlist_selected(self, item):
        """Handle playlist selection"""
        self.current_playlist = Path(item.data(Qt.ItemDataRole.UserRole))
        # Clear previous results
        self.missing_remote_list.clear()
        self.missing_local_list.clear()
        self.remote_count_label.setText("")
        self.local_count_label.setText("")
        self.status_label.setText(f"Selected: {self.current_playlist.name}")
        
        # Disable sync buttons until analysis is done
        self.set_sync_buttons_enabled(False)
        
    def get_ssh_connection(self) -> bool:
        """Establish SSH connection if needed"""
        if self.ssh_handler is None:
            # Show password dialog if needed
            if not SSHCredentials._cached_password:
                dialog = PasswordDialog(self)
                result = dialog.get_credentials()
                if not result.accepted:
                    return False
                password = result.password
            else:
                password = SSHCredentials._cached_password
                
            # Setup handlers
            credentials = SSHCredentials(
                host=self.SSH_HOST,
                username=self.SSH_USERNAME,
                password=password,
                remote_path=self.SSH_REMOTE_PATH
            )
            
            self.ssh_handler = SSHHandler(credentials)
            
            # Test connection
            success, error = self.ssh_handler.test_connection()
            if not success:
                self.status_label.setText("Connection failed!")
                QMessageBox.critical(self, "Connection Error", f"Failed to connect: {error}")
                return False
                
            # Setup comparator
            self.file_comparator = FileComparator(self.ssh_handler)
            
        return True
            
    def on_analyze_clicked(self):
        """Handle analyze button click"""
        if not self.current_playlist:
            QMessageBox.warning(self, "Warning", "Please select a playlist first.")
            return
            
        if not self.get_ssh_connection():
            return
            
        # Update status
        self.status_label.setText("Comparing files...")
        QApplication.processEvents()
        
        # Start comparison
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.comparison_worker = ComparisonWorker(
            self.file_comparator,
            self.current_playlist,
            self.local_base,
            self.SSH_REMOTE_PATH
        )
        
        self.comparison_worker.progress.connect(self.on_comparison_progress)
        self.comparison_worker.finished.connect(self.on_comparison_complete)
        self.comparison_worker.error.connect(self.on_comparison_error)
        self.comparison_worker.start()
        
    def on_analyze_all_clicked(self):
        """Handle analyze all button click"""
        if not self.get_ssh_connection():
            return
            
        self.status_label.setText("Analyzing all playlists...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        QApplication.processEvents()
        
        total_playlists = self.playlist_list.count()
        for i in range(total_playlists):
            item = self.playlist_list.item(i)
            playlist_path = Path(item.data(Qt.ItemDataRole.UserRole))
            
            try:
                # Update progress
                self.progress_bar.setValue(int((i / total_playlists) * 100))
                self.status_label.setText(f"Analyzing {playlist_path.name}...")
                QApplication.processEvents()
                
                # Run comparison
                result = asyncio.run(self.file_comparator.compare_locations(
                    playlist_path,
                    self.local_base,
                    self.SSH_REMOTE_PATH
                ))
                
                # Update playlist display
                self.update_playlist_item(
                    playlist_path,
                    len(result.missing_remotely),
                    len(result.missing_locally)
                )
                
            except Exception as e:
                print(f"Error analyzing {playlist_path}: {e}")
                continue
                
        # Complete
        self.progress_bar.setValue(100)
        self.status_label.setText("Analysis complete")
        self.progress_bar.setVisible(False)
        
    def on_comparison_progress(self, progress: int):
        """Handle comparison progress updates"""
        self.progress_bar.setValue(progress)
        if progress % 10 == 0:  # Update status every 10%
            self.status_label.setText(f"Comparing files... {progress}%")
        QApplication.processEvents()
            
    def update_playlist_item(self, playlist_path: Path, missing_remote: int = None, missing_local: int = None):
        """Update existing playlist item with sync status"""
        display_name = playlist_path.name
        if missing_remote is not None and missing_local is not None:
            display_name = f"{playlist_path.name} ({missing_remote}, {missing_local})"
        
        # Find existing item
        for i in range(self.playlist_list.count()):
            item = self.playlist_list.item(i)
            if Path(item.data(Qt.ItemDataRole.UserRole)) == playlist_path:
                item.setText(display_name)
                return
                
        # If not found, add new item (shouldn't happen normally)
        item = QListWidgetItem(display_name)
        item.setData(Qt.ItemDataRole.UserRole, str(playlist_path))
        self.playlist_list.addItem(item)
        
    def on_comparison_complete(self, result):
        """Handle comparison completion"""
        self.progress_bar.setVisible(False)
        
        # Update missing remotely list
        self.missing_remote_list.clear()
        for path in sorted(result.missing_remotely):
            self.missing_remote_list.add_file_item(path)
        self.remote_count_label.setText(f"{len(result.missing_remotely)} files")
            
        # Update missing locally list
        self.missing_local_list.clear()
        for path in sorted(result.missing_locally):
            self.missing_local_list.add_file_item(path)
        self.local_count_label.setText(f"{len(result.missing_locally)} files")
            
        # Enable sync buttons
        self.set_sync_buttons_enabled(True)
            
        # Update status
        total_missing = len(result.missing_remotely) + len(result.missing_locally)
        if total_missing == 0:
            self.status_label.setText("Analysis complete. Locations are in sync!")
        else:
            self.status_label.setText(
                f"Analysis complete. Found {total_missing} differences between locations."
            )
            
        # Update playlist item with counts
        self.update_playlist_item(
            self.current_playlist,
            len(result.missing_remotely),
            len(result.missing_locally)
        )
                
        # Log results
        self.sync_logger.log_comparison(
            self.current_playlist,
            result.missing_remotely,
            result.missing_locally
        )
            
    def on_comparison_error(self, error_msg):
        """Handle comparison error"""
        self.progress_bar.setVisible(False)
        self.status_label.setText("Analysis failed!")
        QMessageBox.critical(self, "Error", f"Comparison failed: {error_msg}")
        
    def on_sync_clicked(self, operation: str):
        """Handle sync button clicks"""
        if not self.ssh_handler:
            QMessageBox.warning(self, "Warning", "Please analyze first.")
            return
            
        # Get selected files based on operation
        if operation == 'add_remote':
            files = self.missing_remote_list.get_checked_files()
            if not files:
                QMessageBox.warning(self, "Warning", "No files selected to add to remote.")
                return
                
            self.status_label.setText(f"Copying {len(files)} files to remote...")
                
            # Setup sync operation
            self.sync_ops = SyncOperations(
                self.ssh_handler,
                self.backup_manager,
                self.local_base,
                self.ssh_handler.credentials.remote_path
            )
            
            # Start sync worker
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.sync_worker = SyncWorker(
                self.sync_ops,
                self.current_playlist,
                add_remote=files,
                add_local=set(),
                remove_remote=set(),
                remove_local=set()
            )
            
        elif operation == 'delete_local':
            files = self.missing_remote_list.get_checked_files()
            if not files:
                QMessageBox.warning(self, "Warning", "No files selected to delete locally.")
                return
                
            # Confirm deletion
            if not self._confirm_deletion("local", len(files)):
                return
            
            self.status_label.setText(f"Deleting {len(files)} local files...")
                
            self.sync_ops = SyncOperations(
                self.ssh_handler,
                self.backup_manager,
                self.local_base,
                self.ssh_handler.credentials.remote_path
            )
            
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.sync_worker = SyncWorker(
                self.sync_ops,
                self.current_playlist,
                add_remote=set(),
                add_local=set(),
                remove_remote=set(),
                remove_local=files
            )
            
        elif operation == 'add_local':
            files = self.missing_local_list.get_checked_files()
            if not files:
                QMessageBox.warning(self, "Warning", "No files selected to add locally.")
                return
                
            self.status_label.setText(f"Copying {len(files)} files from remote...")
                
            self.sync_ops = SyncOperations(
                self.ssh_handler,
                self.backup_manager,
                self.local_base,
                self.ssh_handler.credentials.remote_path
            )
            
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.sync_worker = SyncWorker(
                self.sync_ops,
                self.current_playlist,
                add_remote=set(),
                add_local=files,
                remove_remote=set(),
                remove_local=set()
            )
            
        elif operation == 'delete_remote':
            files = self.missing_local_list.get_checked_files()
            if not files:
                QMessageBox.warning(self, "Warning", "No files selected to remove from remote.")
                return
                
            # Confirm deletion
            if not self._confirm_deletion("remote", len(files)):
                return
            
            self.status_label.setText(f"Deleting {len(files)} remote files...")
                
            self.sync_ops = SyncOperations(
                self.ssh_handler,
                self.backup_manager,
                self.local_base,
                self.ssh_handler.credentials.remote_path
            )
            
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.sync_worker = SyncWorker(
                self.sync_ops,
                self.current_playlist,
                add_remote=set(),
                add_local=set(),
                remove_remote=files,
                remove_local=set()
            )
        
        # Connect worker signals
        if self.sync_worker:
            self.sync_worker.progress.connect(self.progress_bar.setValue)
            self.sync_worker.finished.connect(self.on_sync_complete)
            self.sync_worker.error.connect(self.on_sync_error)
            self.sync_worker.start()
            
    def on_sync_complete(self):
        """Handle sync completion"""
        self.progress_bar.setVisible(False)
        
        # Show success message
        QMessageBox.information(
            self,
            "Success",
            "Sync operation completed successfully."
        )
        
        # Update status
        self.status_label.setText("Sync complete. Refreshing analysis...")
        
        # Refresh analysis to show updated state
        self.on_analyze_clicked()
            
    def on_sync_error(self, error_msg):
        """Handle sync error"""
        self.progress_bar.setVisible(False)
        self.status_label.setText("Sync failed!")
        QMessageBox.critical(self, "Error", f"Sync operation failed: {error_msg}")
        
    def _confirm_deletion(self, location: str, count: int) -> bool:
        """Show confirmation dialog for deletions"""
        result = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete {count} files from the {location} location?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return result == QMessageBox.StandardButton.Yes