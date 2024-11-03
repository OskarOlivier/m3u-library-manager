# gui/dialogs/credentials_dialog.py

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QPushButton, QFormLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from dataclasses import dataclass

__all__ = ['PasswordDialog', 'SSHCredentialsResult']  # Export these names

@dataclass
class SSHCredentialsResult:
    """Stores the result of credential input"""
    accepted: bool
    password: str = ""

class PasswordDialog(QDialog):
    """Dialog for SSH password input"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SSH Password")
        self.setFixedWidth(400)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Info label
        info_label = QLabel("Enter password for pi@192.168.178.43")
        info_label.setFont(QFont("Segoe UI", 11))
        layout.addWidget(info_label)
        
        # Password input
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("SSH password")
        
        form = QFormLayout()
        form.addRow("Password:", self.password_input)
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
                password=self.password_input.text()
            )
        return SSHCredentialsResult(accepted=False)