# gui/dialogs/credentials_dialog.py

from PyQt6.QtWidgets import QLabel, QLineEdit, QFormLayout, QVBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from dataclasses import dataclass

from .base_dialog import BaseDialog

@dataclass
class SSHCredentialsResult:
    """Stores the result of credential input"""
    accepted: bool
    password: str = ""

class PasswordDialog(BaseDialog):
    """Dialog for SSH password input"""
    
    def __init__(self, parent=None):
        super().__init__("SSH Password", parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the password input UI."""
        # Info label
        info_label = QLabel("Enter password for pi@192.168.178.43")
        info_label.setFont(QFont("Segoe UI", 11))
        self.content_layout.addWidget(info_label)
        
        # Password input
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("SSH password")
        self.password_input.setFont(QFont("Segoe UI", 11))
        
        # Form layout for password field
        form = QFormLayout()
        form.addRow("Password:", self.password_input)
        self.content_layout.addLayout(form)
        
        # Update button text
        self.cancel_btn.setText("Cancel")
        self.ok_btn.setText("Connect")
        
        # Set focus to password input
        self.password_input.setFocus()
        
    def get_credentials(self) -> SSHCredentialsResult:
        """Show dialog and return credentials"""
        if self.exec() == BaseDialog.DialogCode.Accepted:
            return SSHCredentialsResult(
                accepted=True,
                password=self.password_input.text()
            )
        return SSHCredentialsResult(accepted=False)