# gui/dialogs/credentials_dialog.py
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QPushButton, QFormLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from dataclasses import dataclass

@dataclass
class SSHCredentialsResult:
    """Stores the result of credential input"""
    accepted: bool
    host: str = ""
    username: str = ""
    password: str = ""
    remote_path: str = ""

class CredentialsDialog(QDialog):
    """Dialog for SSH credential input"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SSH Connection Details")
        self.setFixedWidth(400)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Form layout for inputs
        form = QFormLayout()
        form.setSpacing(12)
        
        # Host input
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("e.g., example.com or 192.168.1.100")
        form.addRow("Host:", self.host_input)
        
        # Username input
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("SSH username")
        form.addRow("Username:", self.username_input)
        
        # Password input
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("SSH password")
        form.addRow("Password:", self.password_input)
        
        # Remote path input
        self.remote_path_input = QLineEdit()
        self.remote_path_input.setPlaceholderText("e.g., /home/user/music")
        form.addRow("Remote Path:", self.remote_path_input)
        
        layout.addLayout(form)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setDefault(True)
        self.connect_btn.clicked.connect(self.accept)
        
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.connect_btn)
        
        layout.addLayout(button_layout)
        
        # Style
        self.setStyleSheet("""
            QDialog {
                background-color: #202020;
            }
            QLabel {
                color: white;
                font-family: 'Segoe UI';
                font-size: 11pt;
            }
            QLineEdit {
                background-color: #2D2D2D;
                border: none;
                border-radius: 2px;
                padding: 8px;
                color: white;
                font-family: 'Segoe UI';
                font-size: 11pt;
            }
            QLineEdit:focus {
                background-color: #333333;
            }
            QPushButton {
                background-color: #2D2D2D;
                border: none;
                border-radius: 2px;
                padding: 8px 16px;
                color: white;
                font-family: 'Segoe UI';
                font-size: 11pt;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #404040;
            }
            QPushButton:pressed {
                background-color: #505050;
            }
            QPushButton:default {
                background-color: #0078D4;
            }
            QPushButton:default:hover {
                background-color: #1982D4;
            }
            QPushButton:default:pressed {
                background-color: #106EBE;
            }
        """)
        
    def get_credentials(self) -> SSHCredentialsResult:
        """Show dialog and return credentials"""
        if self.exec() == QDialog.DialogCode.Accepted:
            return SSHCredentialsResult(
                accepted=True,
                host=self.host_input.text().strip(),
                username=self.username_input.text().strip(),
                password=self.password_input.text(),
                remote_path=self.remote_path_input.text().strip()
            )
        return SSHCredentialsResult(accepted=False)