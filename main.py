import sys
import platform
import psutil
import sqlite3
import json
from datetime import datetime
from pathlib import Path
import subprocess
import re
import time
import random
import hashlib
import base64
from typing import Dict, List, Tuple, Optional
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                              QWidget, QPushButton, QLabel, QTabWidget, QTextEdit, 
                              QTableWidget, QTableWidgetItem, QGroupBox, QLineEdit,
                              QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox,
                              QDateEdit, QFormLayout, QMessageBox, QSplitter,
                              QHeaderView, QProgressBar, QListWidget, QListWidgetItem,
                              QDialog, QDialogButtonBox, QTextBrowser, QFileDialog)
from PySide6.QtCore import Qt, QDate, QTimer
from PySide6.QtGui import QFont, QPixmap, QPainter
import pandas as pd
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

class LoginDialog(QDialog):
    """Simple login dialog with encrypted password storage"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("COA Laptop Inspector - Login")
        self.setModal(True)
        self.setFixedSize(350, 200)
        
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Commission on Audit")
        title.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        subtitle = QLabel("Laptop Inspection System")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        
        layout.addSpacing(20)
        
        # Username
        form_layout = QFormLayout()
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")
        form_layout.addRow("Username:", self.username_input)
        
        # Password
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.returnPressed.connect(self.attempt_login)
        form_layout.addRow("Password:", self.password_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.attempt_login)
        self.login_button.setDefault(True)
        
        self.setup_button = QPushButton("First Time Setup")
        self.setup_button.clicked.connect(self.first_time_setup)
        
        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.setup_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        self.authenticated = False
        self.user_info = {}
        
        # Check if credentials already exist and hide setup button if they do
        self.check_and_update_setup_button()
    
    def check_and_update_setup_button(self):
        """Check if credentials exist and update setup button visibility"""
        creds_file = Path("coa_credentials.dat")
        if creds_file.exists():
            # Credentials already exist, hide the setup button
            self.setup_button.setVisible(False)
        else:
            # No credentials, show setup button
            self.setup_button.setVisible(True)
    
    def attempt_login(self):
        """Attempt to authenticate user"""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username or not password:
            QMessageBox.warning(self, "Input Error", "Please enter both username and password.")
            return
        
        # Check credentials
        if self.verify_credentials(username, password):
            self.authenticated = True
            self.user_info = {'username': username, 'role': 'inspector'}
            self.accept()
        else:
            QMessageBox.warning(self, "Login Failed", "Invalid username or password.")
            self.password_input.clear()
            self.password_input.setFocus()
    
    def first_time_setup(self):
        """First time setup for creating credentials"""
        # Check if credentials already exist
        creds_file = Path("coa_credentials.dat")
        if creds_file.exists():
            QMessageBox.warning(
                self, 
                "Account Already Exists", 
                "An account already exists.\n\nIf you forgot your password, please contact your system administrator or delete the 'coa_credentials.dat' file to reset."
            )
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("First Time Setup")
        dialog.setModal(True)
        
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        username_input = QLineEdit()
        password_input = QLineEdit()
        password_input.setEchoMode(QLineEdit.Password)
        confirm_password = QLineEdit()
        confirm_password.setEchoMode(QLineEdit.Password)
        
        form_layout.addRow("Username:", username_input)
        form_layout.addRow("Password:", password_input)
        form_layout.addRow("Confirm Password:", confirm_password)
        
        layout.addLayout(form_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec():
            username = username_input.text().strip()
            password = password_input.text()
            confirm = confirm_password.text()
            
            if not username or not password:
                QMessageBox.warning(self, "Error", "Username and password cannot be empty.")
                return
            
            if password != confirm:
                QMessageBox.warning(self, "Error", "Passwords do not match.")
                return
            
            if len(password) < 6:
                QMessageBox.warning(self, "Error", "Password must be at least 6 characters.")
                return
            
            # Save credentials
            if self.save_credentials(username, password):
                QMessageBox.information(self, "Success", "Account created successfully! Please login.")
                self.username_input.setText(username)
                self.password_input.setFocus()
                # Hide the setup button now that account is created
                self.setup_button.setVisible(False)
            else:
                QMessageBox.warning(self, "Error", "Failed to create account.")
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def save_credentials(self, username: str, password: str) -> bool:
        """Save encrypted credentials to file"""
        try:
            creds_file = Path("coa_credentials.dat")
            hashed_password = self.hash_password(password)
            
            credentials = {
                'username': username,
                'password': hashed_password,
                'created': datetime.now().isoformat()
            }
            
            # Encode to base64 for basic obfuscation
            encoded = base64.b64encode(json.dumps(credentials).encode()).decode()
            creds_file.write_text(encoded)
            return True
        except Exception as e:
            print(f"Error saving credentials: {e}")
            return False
    
    def verify_credentials(self, username: str, password: str) -> bool:
        """Verify user credentials"""
        try:
            creds_file = Path("coa_credentials.dat")
            if not creds_file.exists():
                return False
            
            encoded = creds_file.read_text()
            credentials = json.loads(base64.b64decode(encoded).decode())
            
            return (credentials['username'] == username and 
                    credentials['password'] == self.hash_password(password))
        except Exception as e:
            print(f"Error verifying credentials: {e}")
            return False

class DigitalSignatureDialog(QDialog):
    """Enhanced digital signature dialog with certificate generation"""
    def __init__(self, parent=None, username=""):
        super().__init__(parent)
        self.setWindowTitle("Digital Signature & Certificate")
        self.setModal(True)
        self.setFixedSize(500, 400)
        self.username = username
        
        layout = QVBoxLayout()
        
        # Info section
        info_label = QLabel("Digital signatures provide authenticity and integrity to inspection reports.")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        layout.addSpacing(10)
        
        # Signature section
        sig_group = QGroupBox("Signatures")
        sig_layout = QFormLayout()
        
        self.inspector_signature = QLineEdit()
        self.inspector_signature.setPlaceholderText("Enter your full name as signature")
        self.inspector_signature.setText(username)
        sig_layout.addRow("Inspector Name:*", self.inspector_signature)
        
        self.inspector_id = QLineEdit()
        self.inspector_id.setPlaceholderText("Employee ID or License Number")
        sig_layout.addRow("Inspector ID:", self.inspector_id)
        
        self.approver_signature = QLineEdit()
        self.approver_signature.setPlaceholderText("Approver's full name (optional)")
        sig_layout.addRow("Approver Name:", self.approver_signature)
        
        self.approver_id = QLineEdit()
        self.approver_id.setPlaceholderText("Approver's ID (optional)")
        sig_layout.addRow("Approver ID:", self.approver_id)
        
        sig_group.setLayout(sig_layout)
        layout.addWidget(sig_group)
        
        # Certificate section
        cert_group = QGroupBox("Digital Certificate")
        cert_layout = QVBoxLayout()
        
        self.generate_cert_check = QCheckBox("Generate digital certificate for this inspection")
        self.generate_cert_check.setChecked(True)
        cert_layout.addWidget(self.generate_cert_check)
        
        self.cert_info = QLabel("A unique certificate ID will be generated and embedded in the report.")
        self.cert_info.setWordWrap(True)
        self.cert_info.setStyleSheet("color: #666; font-size: 9pt;")
        cert_layout.addWidget(self.cert_info)
        
        cert_group.setLayout(cert_layout)
        layout.addWidget(cert_group)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        self.certificate_id = None
    
    def validate_and_accept(self):
        """Validate inputs and generate certificate"""
        if not self.inspector_signature.text().strip():
            QMessageBox.warning(self, "Required Field", "Inspector name is required.")
            return
        
        if self.generate_cert_check.isChecked():
            self.certificate_id = self.generate_certificate()
        
        self.accept()
    
    def generate_certificate(self) -> str:
        """Generate a unique certificate ID for this inspection"""
        timestamp = datetime.now().isoformat()
        data = f"{self.inspector_signature.text()}{timestamp}{random.randint(1000, 9999)}"
        cert_hash = hashlib.sha256(data.encode()).hexdigest()[:16].upper()
        return f"COA-CERT-{cert_hash}"
    
    def get_signatures(self) -> Tuple[str, str, str, str, str, Optional[str]]:
        """Return signature data and certificate ID"""
        return (
            self.inspector_signature.text(),
            self.inspector_id.text(),
            self.approver_signature.text(),
            self.approver_id.text(),
            datetime.now().isoformat(),
            self.certificate_id
        )

class PRTemplateDialog(QDialog):
    """Dialog for creating and managing PR templates"""
    def __init__(self, parent=None, template_data=None):
        super().__init__(parent)
        self.setWindowTitle("PR Template Manager")
        self.setModal(True)
        self.setFixedSize(500, 450)
        
        layout = QVBoxLayout()
        
        # Template info
        info_group = QGroupBox("Template Information")
        info_layout = QFormLayout()
        
        self.template_name = QLineEdit()
        self.template_name.setPlaceholderText("e.g., 'Standard Office Laptop 2025'")
        info_layout.addRow("Template Name:*", self.template_name)
        
        self.agency_name = QLineEdit()
        self.agency_name.setPlaceholderText("Agency or Department")
        info_layout.addRow("Agency:", self.agency_name)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Specifications
        specs_group = QGroupBox("Purchase Request Specifications")
        specs_layout = QFormLayout()
        
        self.pr_cpu = QLineEdit()
        self.pr_cpu.setPlaceholderText("e.g., Intel Core i5")
        specs_layout.addRow("Required CPU:*", self.pr_cpu)
        
        self.pr_ram = QLineEdit()
        self.pr_ram.setPlaceholderText("e.g., 8GB")
        specs_layout.addRow("Required RAM:*", self.pr_ram)
        
        self.pr_storage = QLineEdit()
        self.pr_storage.setPlaceholderText("e.g., 256GB SSD")
        specs_layout.addRow("Required Storage:*", self.pr_storage)
        
        self.pr_graphics = QLineEdit()
        self.pr_graphics.setPlaceholderText("e.g., Intel UHD Graphics")
        specs_layout.addRow("Graphics:", self.pr_graphics)
        
        self.pr_wifi = QLineEdit()
        self.pr_wifi.setPlaceholderText("e.g., WiFi 6 (802.11ax)")
        specs_layout.addRow("WiFi:", self.pr_wifi)
        
        self.pr_notes = QLineEdit()
        self.pr_notes.setPlaceholderText("Additional notes...")
        specs_layout.addRow("Notes:", self.pr_notes)
        
        specs_group.setLayout(specs_layout)
        layout.addWidget(specs_group)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        
        # Load existing template data if provided
        if template_data:
            self.load_template(template_data)
    
    def validate_and_accept(self):
        """Validate required fields"""
        if not self.template_name.text().strip():
            QMessageBox.warning(self, "Required", "Template name is required.")
            return
        if not all([self.pr_cpu.text().strip(), self.pr_ram.text().strip(), 
                   self.pr_storage.text().strip()]):
            QMessageBox.warning(self, "Required", "CPU, RAM, and Storage are required.")
            return
        self.accept()
    
    def load_template(self, data):
        """Load template data into form"""
        self.template_name.setText(data.get('template_name', ''))
        self.agency_name.setText(data.get('agency_name', ''))
        self.pr_cpu.setText(data.get('pr_cpu', ''))
        self.pr_ram.setText(data.get('pr_ram', ''))
        self.pr_storage.setText(data.get('pr_storage', ''))
        self.pr_graphics.setText(data.get('pr_graphics', ''))
        self.pr_wifi.setText(data.get('pr_wifi', ''))
        self.pr_notes.setText(data.get('pr_notes', ''))
    
    def get_template_data(self):
        """Return template data as dictionary"""
        return {
            'template_name': self.template_name.text().strip(),
            'agency_name': self.agency_name.text().strip(),
            'pr_cpu': self.pr_cpu.text().strip(),
            'pr_ram': self.pr_ram.text().strip(),
            'pr_storage': self.pr_storage.text().strip(),
            'pr_graphics': self.pr_graphics.text().strip(),
            'pr_wifi': self.pr_wifi.text().strip(),
            'pr_notes': self.pr_notes.text().strip()
        }

class PendingInspectionDialog(QDialog):
    """Dialog for creating pending inspections"""
    def __init__(self, parent=None, templates=None, pending_data=None):
        super().__init__(parent)
        self.setWindowTitle("Create Pending Inspection")
        self.setModal(True)
        self.setFixedSize(550, 550)
        self.templates = templates or []
        
        layout = QVBoxLayout()
        
        # Template selection
        template_group = QGroupBox("Load from Template (Optional)")
        template_layout = QHBoxLayout()
        
        self.template_combo = QComboBox()
        self.template_combo.addItem("-- Select a template --", None)
        for template in self.templates:
            self.template_combo.addItem(template['template_name'], template)
        self.template_combo.currentIndexChanged.connect(self.load_from_template)
        template_layout.addWidget(self.template_combo)
        
        template_group.setLayout(template_layout)
        layout.addWidget(template_group)
        
        # Inspection details
        details_group = QGroupBox("Inspection Details")
        details_layout = QFormLayout()
        
        self.agency_name = QLineEdit()
        details_layout.addRow("Agency Name:*", self.agency_name)
        
        self.pr_number = QLineEdit()
        details_layout.addRow("PR Number:*", self.pr_number)
        
        self.laptop_model = QLineEdit()
        self.laptop_model.setPlaceholderText("Optional - can be filled during inspection")
        details_layout.addRow("Laptop Model:", self.laptop_model)
        
        self.expected_serial = QLineEdit()
        self.expected_serial.setPlaceholderText("Optional - if known in advance")
        details_layout.addRow("Serial Number:", self.expected_serial)
        
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
        
        # PR Specifications
        specs_group = QGroupBox("Purchase Request Specifications")
        specs_layout = QFormLayout()
        
        self.pr_cpu = QLineEdit()
        specs_layout.addRow("Required CPU:*", self.pr_cpu)
        
        self.pr_ram = QLineEdit()
        specs_layout.addRow("Required RAM:*", self.pr_ram)
        
        self.pr_storage = QLineEdit()
        specs_layout.addRow("Required Storage:*", self.pr_storage)
        
        self.pr_graphics = QLineEdit()
        specs_layout.addRow("Graphics:", self.pr_graphics)
        
        self.pr_wifi = QLineEdit()
        specs_layout.addRow("WiFi:", self.pr_wifi)
        
        self.pr_notes = QLineEdit()
        specs_layout.addRow("Notes:", self.pr_notes)
        
        specs_group.setLayout(specs_layout)
        layout.addWidget(specs_group)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        
        # Load pending data if editing
        if pending_data:
            self.load_pending_data(pending_data)
    
    def load_from_template(self):
        """Load specs from selected template"""
        template = self.template_combo.currentData()
        if template:
            self.agency_name.setText(template.get('agency_name', ''))
            self.pr_cpu.setText(template.get('pr_cpu', ''))
            self.pr_ram.setText(template.get('pr_ram', ''))
            self.pr_storage.setText(template.get('pr_storage', ''))
            self.pr_graphics.setText(template.get('pr_graphics', ''))
            self.pr_wifi.setText(template.get('pr_wifi', ''))
            self.pr_notes.setText(template.get('pr_notes', ''))
    
    def validate_and_accept(self):
        """Validate required fields"""
        if not all([self.agency_name.text().strip(), self.pr_number.text().strip()]):
            QMessageBox.warning(self, "Required", "Agency Name and PR Number are required.")
            return
        if not all([self.pr_cpu.text().strip(), self.pr_ram.text().strip(), 
                   self.pr_storage.text().strip()]):
            QMessageBox.warning(self, "Required", "CPU, RAM, and Storage specifications are required.")
            return
        self.accept()
    
    def load_pending_data(self, data):
        """Load pending inspection data"""
        self.agency_name.setText(data.get('agency_name', ''))
        self.pr_number.setText(data.get('pr_number', ''))
        self.laptop_model.setText(data.get('laptop_model', ''))
        self.expected_serial.setText(data.get('expected_serial', ''))
        self.pr_cpu.setText(data.get('pr_cpu', ''))
        self.pr_ram.setText(data.get('pr_ram', ''))
        self.pr_storage.setText(data.get('pr_storage', ''))
        self.pr_graphics.setText(data.get('pr_graphics', ''))
        self.pr_wifi.setText(data.get('pr_wifi', ''))
        self.pr_notes.setText(data.get('pr_notes', ''))
    
    def get_pending_data(self):
        """Return pending inspection data"""
        return {
            'agency_name': self.agency_name.text().strip(),
            'pr_number': self.pr_number.text().strip(),
            'laptop_model': self.laptop_model.text().strip(),
            'expected_serial': self.expected_serial.text().strip(),
            'pr_cpu': self.pr_cpu.text().strip(),
            'pr_ram': self.pr_ram.text().strip(),
            'pr_storage': self.pr_storage.text().strip(),
            'pr_graphics': self.pr_graphics.text().strip(),
            'pr_wifi': self.pr_wifi.text().strip(),
            'pr_notes': self.pr_notes.text().strip()
        }

class NetworkTestDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Network Connectivity Test")
        self.setModal(True)
        self.setFixedSize(500, 400)
        
        layout = QVBoxLayout()
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        layout.addWidget(self.results_text)
        
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        self.test_button = QPushButton("Run Comprehensive Network Tests")
        self.test_button.clicked.connect(self.run_network_tests)
        layout.addWidget(self.test_button)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def run_network_tests(self):
        self.results_text.setText("Running network tests...\n")
        self.progress_bar.setValue(25)
        QApplication.processEvents()
        
        try:
            # Test basic connectivity
            result = subprocess.run(['ping', '-n', '4', '8.8.8.8'], 
                                  capture_output=True, text=True, shell=True, timeout=30)
            self.results_text.append("✓ Basic connectivity test completed")
            self.progress_bar.setValue(50)
            
            # Test DNS resolution
            result = subprocess.run(['nslookup', 'google.com'], 
                                  capture_output=True, text=True, shell=True, timeout=10)
            self.results_text.append("✓ DNS resolution test completed")
            self.progress_bar.setValue(75)
            
            # Get detailed network info
            interfaces = psutil.net_if_addrs()
            stats = psutil.net_if_stats()
            
            self.results_text.append("\n=== Network Interfaces ===")
            for interface, addrs in interfaces.items():
                status = "UP" if interface in stats and stats[interface].isup else "DOWN"
                self.results_text.append(f"{interface}: {status}")
                for addr in addrs:
                    if addr.family == 2:  # IPv4
                        self.results_text.append(f"  IPv4: {addr.address}")
            
            self.progress_bar.setValue(100)
            self.results_text.append("\n✓ All network tests completed successfully")
            
        except Exception as e:
            self.results_text.append(f"✗ Network test error: {str(e)}")

class LaptopInspectorApp(QMainWindow):
    def __init__(self, user_info: Dict):
        super().__init__()
        self.setWindowTitle(f"COA Laptop Inspection System v2.5 - User: {user_info['username']}")
        self.setGeometry(100, 100, 1400, 900)
        
        # User information
        self.user_info = user_info
        
        # Initialize database
        self.db_path = Path("coa_inspections.db")
        self.init_database()
        
        self.setup_ui()
        self.current_inspection = {}
        self.inspection_results = {}
        self.current_pending_id = None  # Track if inspection is from pending queue
        
        # Set default inspector name
        QTimer.singleShot(100, lambda: self.inspector_name.setText(user_info['username']))
    
    def init_database(self):
        """Initialize SQLite database for storing inspections"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inspections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inspection_date TEXT,
                inspector_name TEXT,
                inspector_signature TEXT,
                inspector_id TEXT,
                approver_signature TEXT,
                approver_id TEXT,
                certificate_id TEXT,
                signature_timestamp TEXT,
                agency_name TEXT,
                pr_number TEXT,
                serial_number TEXT,
                laptop_model TEXT,
                inspection_data TEXT,
                overall_status TEXT,
                created_at TEXT,
                created_by TEXT
            )
        ''')
        
        # Create audit log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT,
                username TEXT,
                details TEXT,
                timestamp TEXT
            )
        ''')
        
        # Create PR templates table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pr_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_name TEXT UNIQUE,
                agency_name TEXT,
                pr_cpu TEXT,
                pr_ram TEXT,
                pr_storage TEXT,
                pr_graphics TEXT,
                pr_wifi TEXT,
                pr_notes TEXT,
                created_by TEXT,
                created_at TEXT
            )
        ''')
        
        # Create pending inspections table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pending_inspections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agency_name TEXT,
                pr_number TEXT,
                laptop_model TEXT,
                expected_serial TEXT,
                pr_cpu TEXT,
                pr_ram TEXT,
                pr_storage TEXT,
                pr_graphics TEXT,
                pr_wifi TEXT,
                pr_notes TEXT,
                status TEXT DEFAULT 'pending',
                created_by TEXT,
                created_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def log_action(self, action: str, details: str = ""):
        """Log user actions for audit trail"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO audit_log (action, username, details, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (action, self.user_info['username'], details, datetime.now().isoformat()))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error logging action: {e}")

    def setup_ui(self):
        # Create menu bar
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        export_db_action = file_menu.addAction('📦 Export Database')
        export_db_action.triggered.connect(self.export_database)
        
        import_db_action = file_menu.addAction('📥 Import Database')
        import_db_action.triggered.connect(self.import_database)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction('Exit')
        exit_action.triggered.connect(self.close)
        
        # Tools menu
        tools_menu = menubar.addMenu('Tools')
        
        backup_action = tools_menu.addAction('💾 Backup Database')
        backup_action.triggered.connect(self.backup_database)
        
        audit_log_action = tools_menu.addAction('📋 View Audit Log')
        audit_log_action.triggered.connect(self.view_audit_log)
        
        tools_menu.addSeparator()
        
        change_password_action = tools_menu.addAction('🔑 Change Password')
        change_password_action.triggered.connect(self.change_password)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        about_action = help_menu.addAction('About')
        about_action.triggered.connect(self.show_about)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Create tabs
        tabs = QTabWidget()
        main_layout.addWidget(tabs)
        
        # Tab 1: New Inspection
        tabs.addTab(self.create_inspection_tab(), "New Inspection")
        
        # Tab 2: PR Templates
        tabs.addTab(self.create_templates_tab(), "📋 PR Templates")
        
        # Tab 3: Pending Inspections
        tabs.addTab(self.create_pending_tab(), "⏳ Pending Inspections")
        
        # Tab 4: Inspection History
        tabs.addTab(self.create_history_tab(), "Inspection History")
        
        # Tab 5: Comparison Reports
        tabs.addTab(self.create_comparison_tab(), "Spec Comparison")
        
        # Tab 6: Analytics
        tabs.addTab(self.create_analytics_tab(), "Analytics")
        
    def create_inspection_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Quick Actions at top
        quick_actions_layout = QHBoxLayout()
        
        self.load_pending_button = QPushButton("⏳ Load Pending Inspection")
        self.load_pending_button.clicked.connect(self.quick_load_pending)
        self.load_pending_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        
        self.load_template_button = QPushButton("📋 Load from Template")
        self.load_template_button.clicked.connect(self.quick_load_template)
        self.load_template_button.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 8px;")
        
        quick_actions_layout.addWidget(self.load_pending_button)
        quick_actions_layout.addWidget(self.load_template_button)
        quick_actions_layout.addStretch()
        
        layout.addLayout(quick_actions_layout)
        
        # Inspection Header
        header_group = QGroupBox("Inspection Details")
        header_layout = QFormLayout()
        header_group.setLayout(header_layout)
        
        self.inspector_name = QLineEdit()
        self.agency_name = QLineEdit()
        self.pr_number = QLineEdit()
        self.serial_number = QLineEdit()
        self.laptop_model = QLineEdit()
        self.inspection_date = QDateEdit()
        self.inspection_date.setDate(QDate.currentDate())
        
        header_layout.addRow("Inspector Name:*", self.inspector_name)
        header_layout.addRow("Agency Name:*", self.agency_name)
        header_layout.addRow("Purchase Request #:*", self.pr_number)
        header_layout.addRow("Laptop Serial #:*", self.serial_number)
        header_layout.addRow("Laptop Model:*", self.laptop_model)
        header_layout.addRow("Inspection Date:", self.inspection_date)
        
        layout.addWidget(header_group)
        
        # Main content splitter
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Left: Detection and Testing
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)
        
        # Auto-detection
        auto_group = QGroupBox("Automatic Hardware Detection")
        auto_layout = QVBoxLayout()
        auto_group.setLayout(auto_layout)
        
        detect_button_layout = QHBoxLayout()
        self.detect_button = QPushButton("🔍 Auto-Detect Hardware Specs")
        self.detect_button.clicked.connect(self.detect_hardware)
        self.network_test_button = QPushButton("🌐 Test Network Connectivity")
        self.network_test_button.clicked.connect(self.show_network_test_dialog)
        
        detect_button_layout.addWidget(self.detect_button)
        detect_button_layout.addWidget(self.network_test_button)
        auto_layout.addLayout(detect_button_layout)
        
        self.specs_display = QTextEdit()
        self.specs_display.setReadOnly(True)
        auto_layout.addWidget(self.specs_display)
        
        left_layout.addWidget(auto_group)
        
        # Performance testing
        perf_group = QGroupBox("Performance Testing")
        perf_layout = QVBoxLayout()
        perf_group.setLayout(perf_layout)
        
        self.test_perf_button = QPushButton("Run Comprehensive Performance Tests")
        self.test_perf_button.clicked.connect(self.run_comprehensive_performance_tests)
        perf_layout.addWidget(self.test_perf_button)
        
        self.perf_results = QTextEdit()
        self.perf_results.setReadOnly(True)
        perf_layout.addWidget(self.perf_results)
        
        left_layout.addWidget(perf_group)
        
        # Right: Manual Input and Assessment
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_widget.setLayout(right_layout)
        
        # Physical Condition Assessment
        physical_group = QGroupBox("Physical Condition Assessment")
        physical_layout = QFormLayout()
        physical_group.setLayout(physical_layout)
        
        self.chassis_condition = QComboBox()
        self.chassis_condition.addItems(["Excellent", "Good", "Fair", "Poor", "Damaged"])
        self.screen_condition = QComboBox()
        self.screen_condition.addItems(["Excellent", "Good", "Fair", "Poor", "Cracked"])
        self.keyboard_condition = QComboBox()
        self.keyboard_condition.addItems(["Excellent", "Good", "Fair", "Poor", "Non-functional"])
        self.ports_condition = QComboBox()
        self.ports_condition.addItems(["All Working", "Some Issues", "Major Issues"])
        self.physical_notes = QLineEdit()
        self.physical_notes.setPlaceholderText("Additional physical condition notes...")
        
        physical_layout.addRow("Chassis Condition:", self.chassis_condition)
        physical_layout.addRow("Screen Condition:", self.screen_condition)
        physical_layout.addRow("Keyboard Condition:", self.keyboard_condition)
        physical_layout.addRow("Ports Condition:", self.ports_condition)
        physical_layout.addRow("Additional Notes:", self.physical_notes)
        
        right_layout.addWidget(physical_group)
        
        # Purchase Request Specs
        pr_group = QGroupBox("Purchase Request Specifications")
        pr_layout = QFormLayout()
        pr_group.setLayout(pr_layout)
        
        self.pr_cpu = QLineEdit()
        self.pr_ram = QLineEdit()
        self.pr_storage = QLineEdit()
        self.pr_graphics = QLineEdit()
        self.pr_wifi = QLineEdit()
        self.pr_notes = QLineEdit()
        
        pr_layout.addRow("Required CPU:*", self.pr_cpu)
        pr_layout.addRow("Required RAM:*", self.pr_ram)
        pr_layout.addRow("Required Storage:*", self.pr_storage)
        pr_layout.addRow("Required Graphics:", self.pr_graphics)
        pr_layout.addRow("Required WiFi:", self.pr_wifi)
        pr_layout.addRow("PR Notes:", self.pr_notes)
        
        right_layout.addWidget(pr_group)
        
        # Comparison and Validation
        validation_group = QGroupBox("Specification Validation")
        validation_layout = QVBoxLayout()
        validation_group.setLayout(validation_layout)
        
        self.validate_button = QPushButton("✅ Validate Specifications")
        self.validate_button.clicked.connect(self.validate_specifications)
        validation_layout.addWidget(self.validate_button)
        
        self.validation_results = QTextEdit()
        self.validation_results.setReadOnly(True)
        validation_layout.addWidget(self.validation_results)
        
        right_layout.addWidget(validation_group)
        
        main_splitter.addWidget(left_widget)
        main_splitter.addWidget(right_widget)
        main_splitter.setSizes([700, 500])
        
        layout.addWidget(main_splitter)
        
        # Action Buttons
        button_layout = QHBoxLayout()
        
        self.signature_button = QPushButton("🖊️ Add Digital Signatures")
        self.signature_button.clicked.connect(self.add_digital_signatures)
        
        self.save_button = QPushButton("💾 Save Inspection")
        self.save_button.clicked.connect(self.save_inspection)
        
        self.report_button = QPushButton("📊 Generate PDF Report")
        self.report_button.clicked.connect(self.generate_comprehensive_pdf_report)
        
        self.excel_button = QPushButton("📈 Export to Excel")
        self.excel_button.clicked.connect(self.export_to_excel)
        
        button_layout.addWidget(self.signature_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.report_button)
        button_layout.addWidget(self.excel_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        return widget

    def create_templates_tab(self):
        """Create PR Templates management tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Header with buttons
        header_layout = QHBoxLayout()
        
        title = QLabel("PR Specification Templates")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        self.new_template_button = QPushButton("➕ New Template")
        self.new_template_button.clicked.connect(self.create_new_template)
        self.new_template_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px;")
        header_layout.addWidget(self.new_template_button)
        
        layout.addLayout(header_layout)
        
        # Templates table
        self.templates_table = QTableWidget()
        self.templates_table.setColumnCount(6)
        self.templates_table.setHorizontalHeaderLabels([
            "Template Name", "Agency", "CPU", "RAM", "Storage", "Actions"
        ])
        self.templates_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.templates_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.templates_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.templates_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.templates_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.templates_table.setColumnWidth(5, 280)  # Fixed width for Actions column
        self.templates_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        layout.addWidget(self.templates_table)
        
        # Load templates
        self.load_templates()
        
        return widget
    
    def create_pending_tab(self):
        """Create Pending Inspections management tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Header with buttons
        header_layout = QHBoxLayout()
        
        title = QLabel("Pending Inspections Queue")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        self.new_pending_button = QPushButton("➕ New Pending Inspection")
        self.new_pending_button.clicked.connect(self.create_new_pending)
        self.new_pending_button.setStyleSheet("background-color: #FF9800; color: white; padding: 8px;")
        header_layout.addWidget(self.new_pending_button)
        
        layout.addLayout(header_layout)
        
        # Info label
        info_label = QLabel("💡 Tip: Create multiple pending inspections in advance, then complete them one by one as you inspect each laptop.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("background-color: #E3F2FD; padding: 8px; border-radius: 4px;")
        layout.addWidget(info_label)
        
        # Pending inspections table
        self.pending_table = QTableWidget()
        self.pending_table.setColumnCount(7)
        self.pending_table.setHorizontalHeaderLabels([
            "PR Number", "Agency", "Model", "CPU", "RAM", "Storage", "Actions"
        ])
        self.pending_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.pending_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.pending_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.pending_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.pending_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.pending_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.pending_table.setColumnWidth(6, 250)  # Fixed width for Actions column
        self.pending_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        layout.addWidget(self.pending_table)
        
        # Statistics
        self.pending_stats_label = QLabel()
        self.pending_stats_label.setStyleSheet("font-weight: bold; padding: 8px;")
        layout.addWidget(self.pending_stats_label)
        
        # Load pending inspections
        self.load_pending_inspections()
        
        return widget

    def create_history_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Search/filter area
        search_layout = QHBoxLayout()
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Search by serial number, PR number, or agency...")
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.load_inspections)
        search_layout.addWidget(self.search_field)
        search_layout.addWidget(self.search_button)
        
        layout.addLayout(search_layout)
        
        # Inspections list
        self.inspections_list = QListWidget()
        self.inspections_list.itemDoubleClicked.connect(self.view_inspection_details)
        layout.addWidget(self.inspections_list)
        
        self.load_inspections()
        
        return widget

    def create_comparison_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Comparison table
        self.comparison_table = QTableWidget()
        self.comparison_table.setColumnCount(4)
        self.comparison_table.setHorizontalHeaderLabels([
            "Component", "Purchase Request", "Actual Spec", "Status"
        ])
        layout.addWidget(self.comparison_table)
        
        return widget

    def create_analytics_tab(self):
        """Create analytics tab for historical data analysis"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        analytics_group = QGroupBox("Inspection Analytics")
        analytics_layout = QVBoxLayout()
        analytics_group.setLayout(analytics_layout)
        
        self.analytics_text = QTextBrowser()
        analytics_layout.addWidget(self.analytics_text)
        
        self.generate_analytics_button = QPushButton("Generate Analytics Report")
        self.generate_analytics_button.clicked.connect(self.generate_analytics)
        analytics_layout.addWidget(self.generate_analytics_button)
        
        layout.addWidget(analytics_group)
        
        return widget

    # === HARDWARE DETECTION METHODS ===
    
    def detect_hardware(self):
        """Enhanced hardware detection with comprehensive system information"""
        try:
            self.specs_display.setText("Detecting hardware specifications...\n")
            QApplication.processEvents()
            
            specs = {}
            
            # CPU Information
            cpu_freq = psutil.cpu_freq()
            specs['CPU'] = {
                'Name': platform.processor(),
                'Cores': psutil.cpu_count(logical=False),
                'Threads': psutil.cpu_count(logical=True),
                'Max Frequency': f"{cpu_freq.max:.2f} MHz" if cpu_freq else "N/A",
                'Current Frequency': f"{cpu_freq.current:.2f} MHz" if cpu_freq else "N/A"
            }
            
            # RAM Information with details
            memory = psutil.virtual_memory()
            specs['RAM'] = {
                'Total': f"{memory.total // (1024**3)} GB",
                'Available': f"{memory.available // (1024**3)} GB",
                'Used': f"{memory.used // (1024**3)} GB",
                'Usage Percent': f"{memory.percent}%"
            }
            specs['RAM'].update(self.get_ram_details())
            
            # Storage Information
            specs['Storage'] = self.get_storage_info()
            
            # Graphics Information
            specs['Graphics'] = self.get_graphics_info()
            
            # Display Information (NEW)
            specs['Display'] = self.get_display_info()
            
            # Network Information with connectivity test
            specs['Network'] = self.get_network_info()
            specs['Network']['Connectivity_Test'] = self.test_network_connectivity()
            
            # Peripheral Devices (NEW)
            specs['Peripherals'] = self.get_peripheral_devices()
            
            # Battery Information (if available)
            specs['Battery'] = self.get_battery_info()
            
            # System Information
            specs['System'] = {
                'OS': f"{platform.system()} {platform.version()}",
                'Architecture': platform.architecture()[0],
                'Hostname': platform.node(),
                'System Serial': self.get_system_serial_number()
            }
            
            # BIOS/Firmware Information
            specs['BIOS'] = self.get_bios_info()
            
            # Warranty Information (NEW)
            specs['Warranty'] = self.get_warranty_info(specs['System']['System Serial'])
            
            self.display_specs(specs)
            self.current_inspection['detected_specs'] = specs
            
            self.log_action("Hardware Detection", f"Serial: {specs['System']['System Serial']}")
            QMessageBox.information(self, "Success", "Hardware detection completed successfully!")
            
        except Exception as e:
            error_msg = f"Error detecting hardware: {str(e)}"
            self.specs_display.setText(error_msg)
            QMessageBox.critical(self, "Detection Error", error_msg)

    def get_storage_info(self):
        """Get storage device information"""
        storage_info = {}
        partitions = psutil.disk_partitions()
        
        for i, partition in enumerate(partitions):
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                storage_info[f'Drive_{i+1}'] = {
                    'Device': partition.device,
                    'FileSystem': partition.fstype,
                    'Total': f"{usage.total // (1024**3)} GB",
                    'Free': f"{usage.free // (1024**3)} GB",
                    'Used': f"{usage.used // (1024**3)} GB"
                }
            except PermissionError:
                continue
        
        return storage_info

    def get_graphics_info(self):
        """Get graphics card information"""
        graphics_info = {}
        
        try:
            if platform.system() == "Windows":
                # Windows WMI query for graphics cards
                result = subprocess.run([
                    'wmic', 'path', 'win32_VideoController', 'get', 'name'
                ], capture_output=True, text=True, shell=True)
                
                cards = [line.strip() for line in result.stdout.split('\n') 
                        if line.strip() and line.strip() != 'Name']
                graphics_info['Cards'] = cards if cards else ["Unable to detect graphics cards"]
            else:
                graphics_info['Cards'] = ["Graphics detection available on Windows only"]
                
        except Exception as e:
            graphics_info['Error'] = f"Could not detect graphics cards: {str(e)}"
        
        return graphics_info

    def get_network_info(self):
        """Get network adapter information"""
        network_info = {}
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        
        for interface, addresses in addrs.items():
            for addr in addresses:
                if addr.family == 2:  # IPv4
                    network_info[interface] = {
                        'IP Address': addr.address,
                        'Netmask': addr.netmask,
                        'Status': 'Up' if interface in stats and stats[interface].isup else 'Down'
                    }
                    break  # Only show first IPv4 address per interface
        
        return network_info

    def get_battery_info(self):
        """Get battery information if available"""
        try:
            battery = psutil.sensors_battery()
            if battery:
                return {
                    'Percent': f"{battery.percent}%",
                    'Power Plugged': "Yes" if battery.power_plugged else "No",
                    'Time Left': f"{battery.secsleft // 3600}h {(battery.secsleft % 3600) // 60}m" if battery.secsleft != psutil.POWER_TIME_UNLIMITED else "Unknown"
                }
            else:
                return {'Status': 'No battery detected'}
        except:
            return {'Status': 'Battery info unavailable'}

    def get_bios_info(self):
        """Get comprehensive BIOS information"""
        try:
            if platform.system() == "Windows":
                # First try the WMI method
                bios_info = {}
                
                # Get BIOS Serial Number
                result = subprocess.run([
                    'wmic', 'bios', 'get', 'serialnumber'
                ], capture_output=True, text=True, shell=True)
                
                lines = [line.strip() for line in result.stdout.split('\n') 
                        if line.strip() and 'SerialNumber' not in line]
                bios_serial = lines[0] if lines else None
                
                # Get BIOS Version
                result = subprocess.run([
                    'wmic', 'bios', 'get', 'version'
                ], capture_output=True, text=True, shell=True)
                
                lines = [line.strip() for line in result.stdout.split('\n') 
                        if line.strip() and 'Version' not in line]
                bios_version = lines[0] if lines else None
                
                # If WMI failed, try PowerShell
                if not bios_serial or bios_serial in ['', '0', 'None', 'To be filled by O.E.M.']:
                    ps_bios_info = self.get_bios_info_powershell()
                    if 'Serial Number' in ps_bios_info and ps_bios_info['Serial Number'] not in ['Not available', '']:
                        return ps_bios_info
                
                # Continue with WMI data if we have valid info
                bios_info['Serial Number'] = bios_serial if bios_serial and bios_serial not in ['', '0', 'None', 'To be filled by O.E.M.'] else "Not available"
                bios_info['Version'] = bios_version if bios_version else "Not available"
                
                # Get BIOS Manufacturer
                result = subprocess.run([
                    'wmic', 'bios', 'get', 'manufacturer'
                ], capture_output=True, text=True, shell=True)
                
                lines = [line.strip() for line in result.stdout.split('\n') 
                        if line.strip() and 'Manufacturer' not in line]
                bios_info['Manufacturer'] = lines[0] if lines else "Not available"
                
                # Get BIOS Release Date
                result = subprocess.run([
                    'wmic', 'bios', 'get', 'releasedate'
                ], capture_output=True, text=True, shell=True)
                
                lines = [line.strip() for line in result.stdout.split('\n') 
                        if line.strip() and 'ReleaseDate' not in line]
                if lines and lines[0]:
                    # Format date from YYYYMMDD to YYYY-MM-DD
                    date_str = lines[0]
                    if len(date_str) >= 8:
                        formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                        bios_info['Release Date'] = formatted_date
                    else:
                        bios_info['Release Date'] = lines[0]
                else:
                    bios_info['Release Date'] = "Not available"
                
                return bios_info
            else:
                return {'Info': 'BIOS info available on Windows only'}
        except Exception as e:
            # If WMI fails, try PowerShell as fallback
            try:
                return self.get_bios_info_powershell()
            except:
                return {'Error': f'Could not retrieve BIOS info: {str(e)}'}

    def get_bios_info_powershell(self):
        """Get BIOS information using PowerShell (more reliable on some systems)"""
        try:
            if platform.system() == "Windows":
                # Use PowerShell to get BIOS information
                ps_script = """
                Get-CimInstance -ClassName Win32_BIOS | Select-Object SerialNumber, Version, Manufacturer, ReleaseDate | ConvertTo-Json
                """
                
                result = subprocess.run([
                    'powershell', '-Command', ps_script
                ], capture_output=True, text=True, shell=True)
                
                if result.returncode == 0 and result.stdout.strip():
                    bios_data = json.loads(result.stdout)
                    bios_info = {
                        'Serial Number': bios_data.get('SerialNumber', 'Not available'),
                        'Version': bios_data.get('Version', 'Not available'),
                        'Manufacturer': bios_data.get('Manufacturer', 'Not available'),
                        'Release Date': bios_data.get('ReleaseDate', 'Not available')
                    }
                    return bios_info
                
            return {'Info': 'BIOS info available on Windows only'}
        except Exception as e:
            return {'Error': f'Could not retrieve BIOS info: {str(e)}'}

    def get_system_serial_number(self):
        """Get system serial number using multiple methods for better compatibility"""
        try:
            if platform.system() == "Windows":
                # Try multiple WMI queries to get serial number
                wmi_queries = [
                    ['wmic', 'bios', 'get', 'serialnumber'],
                    ['wmic', 'csproduct', 'get', 'identifyingnumber'],
                    ['wmic', 'systemenclosure', 'get', 'serialnumber']
                ]
                
                for query in wmi_queries:
                    result = subprocess.run(query, capture_output=True, text=True, shell=True)
                    lines = [line.strip() for line in result.stdout.split('\n') 
                            if line.strip() and not any(keyword in line.lower() for keyword in ['serialnumber', 'identifyingnumber'])]
                    
                    if lines and lines[0] and lines[0] not in ['', '0', 'None', 'To be filled by O.E.M.']:
                        return lines[0]
                
                return "Not available"
            return "Windows only"
        except:
            return "Error retrieving"

    def test_network_connectivity(self):
        """Test basic network connectivity"""
        try:
            # Test internet connectivity
            result = subprocess.run(['ping', '-n', '1', '8.8.8.8'], 
                                  capture_output=True, text=True, timeout=10, shell=True)
            return "Internet: Connected" if result.returncode == 0 else "Internet: No Connection"
        except:
            return "Internet: Test Failed"
    
    def get_ram_details(self) -> Dict:
        """Get detailed RAM information including type and speed"""
        ram_details = {}
        try:
            if platform.system() == "Windows":
                # Get RAM type and speed
                result = subprocess.run([
                    'wmic', 'memorychip', 'get', 'capacity,speed,memorytype'
                ], capture_output=True, text=True, shell=True)
                
                lines = [line.strip() for line in result.stdout.split('\n') 
                        if line.strip() and 'Capacity' not in line]
                
                if lines:
                    # Parse RAM details
                    total_modules = len(lines)
                    speeds = []
                    types = []
                    
                    for line in lines:
                        parts = line.split()
                        if len(parts) >= 2:
                            speeds.append(parts[1] if len(parts) > 1 else "Unknown")
                            types.append(self.get_memory_type_name(parts[2] if len(parts) > 2 else "0"))
                    
                    ram_details['Modules'] = total_modules
                    ram_details['Speed'] = f"{speeds[0]} MHz" if speeds else "Unknown"
                    ram_details['Type'] = types[0] if types else "Unknown"
        except Exception as e:
            ram_details['Details'] = f"Could not retrieve RAM details: {str(e)}"
        
        return ram_details
    
    def get_memory_type_name(self, type_code: str) -> str:
        """Convert memory type code to name"""
        memory_types = {
            "20": "DDR",
            "21": "DDR2",
            "24": "DDR3",
            "26": "DDR4",
            "34": "DDR5"
        }
        return memory_types.get(type_code, f"Type {type_code}")
    
    def get_display_info(self) -> Dict:
        """Get display/monitor information"""
        display_info = {}
        try:
            if platform.system() == "Windows":
                # Get monitor information
                result = subprocess.run([
                    'wmic', 'path', 'Win32_DesktopMonitor', 'get', 'ScreenHeight,ScreenWidth,Name'
                ], capture_output=True, text=True, shell=True)
                
                lines = [line.strip() for line in result.stdout.split('\n') 
                        if line.strip() and 'Name' not in line and 'ScreenHeight' not in line]
                
                if lines and lines[0]:
                    parts = lines[0].split()
                    if len(parts) >= 2:
                        display_info['Resolution'] = f"{parts[1]}x{parts[0]}" if parts[0].isdigit() else "Unable to detect"
                        display_info['Name'] = ' '.join(parts[2:]) if len(parts) > 2 else "Built-in Display"
                else:
                    display_info['Resolution'] = "Unable to detect"
                    display_info['Name'] = "Built-in Display"
                
                # Try to get more details using PowerShell
                ps_script = """
                Add-Type -AssemblyName System.Windows.Forms
                [System.Windows.Forms.Screen]::PrimaryScreen | Select-Object -ExpandProperty Bounds | ConvertTo-Json
                """
                result = subprocess.run([
                    'powershell', '-Command', ps_script
                ], capture_output=True, text=True, shell=True, timeout=5)
                
                if result.returncode == 0 and result.stdout.strip():
                    try:
                        screen_data = json.loads(result.stdout)
                        display_info['Resolution'] = f"{screen_data.get('Width', 0)}x{screen_data.get('Height', 0)}"
                    except:
                        pass
                        
        except Exception as e:
            display_info['Error'] = f"Could not detect display: {str(e)}"
        
        return display_info if display_info else {'Info': 'Display detection unavailable'}
    
    def get_peripheral_devices(self) -> Dict:
        """Detect peripheral devices (webcam, audio, USB devices)"""
        peripherals = {}
        try:
            if platform.system() == "Windows":
                # Detect webcams
                result = subprocess.run([
                    'wmic', 'path', 'Win32_PnPEntity', 'where', '"Name like \'%camera%\'"', 'get', 'Name'
                ], capture_output=True, text=True, shell=True, timeout=10)
                
                cameras = [line.strip() for line in result.stdout.split('\n') 
                          if line.strip() and 'Name' not in line]
                peripherals['Webcam'] = cameras[0] if cameras else "No webcam detected"
                
                # Detect audio devices
                result = subprocess.run([
                    'wmic', 'sounddev', 'get', 'name'
                ], capture_output=True, text=True, shell=True, timeout=10)
                
                audio = [line.strip() for line in result.stdout.split('\n') 
                        if line.strip() and 'Name' not in line]
                peripherals['Audio Devices'] = audio[:2] if audio else ["No audio devices"]
                
                # Detect USB devices
                result = subprocess.run([
                    'wmic', 'path', 'Win32_USBControllerDevice', 'get', 'Dependent'
                ], capture_output=True, text=True, shell=True, timeout=10)
                
                usb_count = len([line for line in result.stdout.split('\n') 
                               if 'USB' in line.upper()])
                peripherals['USB Devices'] = f"{usb_count} USB devices connected"
                
                # Detect Bluetooth
                result = subprocess.run([
                    'wmic', 'path', 'Win32_PnPEntity', 'where', '"Name like \'%bluetooth%\'"', 'get', 'Name'
                ], capture_output=True, text=True, shell=True, timeout=10)
                
                bluetooth = [line.strip() for line in result.stdout.split('\n') 
                           if line.strip() and 'Name' not in line]
                peripherals['Bluetooth'] = "Available" if bluetooth else "Not detected"
                
        except Exception as e:
            peripherals['Error'] = f"Could not detect peripherals: {str(e)}"
        
        return peripherals if peripherals else {'Info': 'Peripheral detection unavailable'}
    
    def get_warranty_info(self, serial_number: str) -> Dict:
        """Get warranty information (basic implementation)"""
        warranty_info = {}
        try:
            if platform.system() == "Windows":
                # Get system manufacturer
                result = subprocess.run([
                    'wmic', 'computersystem', 'get', 'manufacturer,model'
                ], capture_output=True, text=True, shell=True)
                
                lines = [line.strip() for line in result.stdout.split('\n') 
                        if line.strip() and 'Manufacturer' not in line]
                
                if lines and lines[0]:
                    parts = lines[0].split(maxsplit=1)
                    warranty_info['Manufacturer'] = parts[0] if parts else "Unknown"
                    warranty_info['Model'] = parts[1] if len(parts) > 1 else "Unknown"
                
                warranty_info['Serial Number'] = serial_number
                warranty_info['Note'] = "Check manufacturer website for warranty details"
                
        except Exception as e:
            warranty_info['Error'] = f"Could not retrieve warranty info: {str(e)}"
        
        return warranty_info if warranty_info else {'Info': 'Warranty info unavailable'}

    def display_specs(self, specs):
        """Display the collected specifications"""
        display_text = "=== LAPTOP HARDWARE SPECIFICATIONS ===\n\n"
        
        for category, details in specs.items():
            display_text += f"{category}:\n"
            if isinstance(details, dict):
                for key, value in details.items():
                    if isinstance(value, (list, dict)):
                        display_text += f"  {key}:\n"
                        if isinstance(value, list):
                            for item in value:
                                display_text += f"    - {item}\n"
                        else:
                            for subkey, subvalue in value.items():
                                display_text += f"    {subkey}: {subvalue}\n"
                    else:
                        display_text += f"  {key}: {value}\n"
            display_text += "\n"
        
        self.specs_display.setText(display_text)

    # === PERFORMANCE TESTING METHODS ===

    def run_comprehensive_performance_tests(self):
        """Run comprehensive performance tests"""
        self.perf_results.setText("Running comprehensive performance tests...\n")
        QApplication.processEvents()
        
        try:
            # CPU Performance Test
            start_time = time.time()
            # Simple CPU-intensive calculation
            for i in range(1000000):
                _ = i * i * i
            cpu_time = time.time() - start_time
            
            # Memory Performance Test
            start_time = time.time()
            test_list = [random.random() for _ in range(100000)]
            sorted_list = sorted(test_list)
            memory_time = time.time() - start_time
            
            # Disk Performance Test
            start_time = time.time()
            test_file = Path("temp_perf_test.dat")
            try:
                with open(test_file, 'wb') as f:
                    f.write(b"0" * 5000000)  # Write 5MB
                disk_write_time = time.time() - start_time
                
                start_time = time.time()
                with open(test_file, 'rb') as f:
                    data = f.read()
                disk_read_time = time.time() - start_time
                
                test_file.unlink()  # Cleanup
            except Exception as e:
                disk_write_time = float('inf')
                disk_read_time = float('inf')
            
            # Assessment
            cpu_assessment = 'Excellent' if cpu_time < 0.5 else 'Good' if cpu_time < 2.0 else 'Poor'
            memory_assessment = 'Excellent' if memory_time < 0.5 else 'Good' if memory_time < 2.0 else 'Poor'
            disk_assessment = 'Excellent' if disk_write_time < 1.0 else 'Good' if disk_write_time < 3.0 else 'Poor'
            
            results = f"""Performance Test Results:
            
CPU Test (1M calculations): {cpu_time:.3f} seconds - {cpu_assessment}
Memory Test (100K sort): {memory_time:.3f} seconds - {memory_assessment}
Disk Write Test (5MB): {disk_write_time:.3f} seconds - {disk_assessment}
Disk Read Test (5MB): {disk_read_time:.3f} seconds

Overall Performance: {cpu_assessment}
"""
            self.perf_results.setText(results)
            self.current_inspection['performance_tests'] = results
            
        except Exception as e:
            self.perf_results.setText(f"Performance test error: {str(e)}")

    # === VALIDATION AND COMPARISON METHODS ===

    def show_network_test_dialog(self):
        """Show network testing dialog"""
        dialog = NetworkTestDialog(self)
        dialog.exec()

    def add_digital_signatures(self):
        """Add digital signatures and certificate to inspection"""
        dialog = DigitalSignatureDialog(self, self.user_info['username'])
        if dialog.exec():
            sig_data = dialog.get_signatures()
            self.current_inspection['inspector_signature'] = sig_data[0]
            self.current_inspection['inspector_id'] = sig_data[1]
            self.current_inspection['approver_signature'] = sig_data[2]
            self.current_inspection['approver_id'] = sig_data[3]
            self.current_inspection['signature_timestamp'] = sig_data[4]
            self.current_inspection['certificate_id'] = sig_data[5]
            
            msg = "Digital signatures added successfully!"
            if sig_data[5]:
                msg += f"\n\nCertificate ID: {sig_data[5]}"
            QMessageBox.information(self, "Success", msg)
            
            self.log_action("Add Signatures", f"Certificate: {sig_data[5]}")

    def validate_specifications(self):
        """Comprehensive specification validation with pass/fail"""
        if not self.current_inspection.get('detected_specs'):
            QMessageBox.warning(self, "No Data", "Please detect hardware specs first.")
            return
        
        detected = self.current_inspection['detected_specs']
        pr_specs = {
            'cpu': self.pr_cpu.text().upper(),
            'ram': self.pr_ram.text().upper(),
            'storage': self.pr_storage.text().upper(),
            'graphics': self.pr_graphics.text().upper(),
            'wifi': self.pr_wifi.text().upper()
        }
        
        validation_results = []
        overall_status = "PASS"
        
        # CPU Validation
        cpu_result = self.validate_cpu(pr_specs['cpu'], detected['CPU'])
        validation_results.append(cpu_result)
        if cpu_result['status'] == "FAIL":
            overall_status = "FAIL"
        
        # RAM Validation
        ram_result = self.validate_ram(pr_specs['ram'], detected['RAM'])
        validation_results.append(ram_result)
        if ram_result['status'] == "FAIL":
            overall_status = "FAIL"
        
        # Storage Validation
        storage_result = self.validate_storage(pr_specs['storage'], detected['Storage'])
        validation_results.append(storage_result)
        if storage_result['status'] == "FAIL":
            overall_status = "FAIL"
        
        # Display results
        self.display_validation_results(validation_results, overall_status)
        self.inspection_results['validation'] = validation_results
        self.inspection_results['overall_status'] = overall_status

    def validate_cpu(self, pr_cpu: str, actual_cpu: Dict) -> Dict:
        """Validate CPU specifications with 'equal or better' logic"""
        if not pr_cpu:
            return {'component': 'CPU', 'status': 'PASS', 'details': 'No PR specification provided'}
        
        actual_name = actual_cpu['Name'].upper()
        pr_upper = pr_cpu.upper()
        
        # CPU tier comparison (higher is better)
        cpu_tiers = {
            'I9': 9, 'RYZEN 9': 9,
            'I7': 7, 'RYZEN 7': 7, 'CORE I7': 7,
            'I5': 5, 'RYZEN 5': 5, 'CORE I5': 5,
            'I3': 3, 'RYZEN 3': 3, 'CORE I3': 3
        }
        
        pr_tier = None
        actual_tier = None
        
        for cpu_name, tier_value in cpu_tiers.items():
            if cpu_name in pr_upper:
                pr_tier = tier_value
            if cpu_name in actual_name:
                actual_tier = tier_value
        
        # If we can compare tiers
        if pr_tier and actual_tier:
            if actual_tier >= pr_tier:
                return {
                    'component': 'CPU',
                    'status': 'PASS',
                    'details': f"✓ Actual CPU (tier {actual_tier}) meets or exceeds PR requirement (tier {pr_tier})"
                }
            else:
                return {
                    'component': 'CPU',
                    'status': 'FAIL',
                    'details': f"✗ Actual CPU (tier {actual_tier}) is below PR requirement (tier {pr_tier})"
                }
        
        # Fallback to string matching
        if pr_upper in actual_name:
            return {'component': 'CPU', 'status': 'PASS', 'details': f"✓ Exact match: {actual_name}"}
        else:
            return {
                'component': 'CPU',
                'status': 'WARNING',
                'details': f"⚠ Cannot verify: PR: {pr_cpu}, Actual: {actual_name}"
            }

    def validate_ram(self, pr_ram: str, actual_ram: Dict) -> Dict:
        """Validate RAM specifications with 'equal or better' logic"""
        if not pr_ram:
            return {'component': 'RAM', 'status': 'PASS', 'details': 'No PR specification provided'}
        
        try:
            # Extract numbers from strings
            pr_gb = self.extract_gb(pr_ram)
            actual_gb = self.extract_gb(actual_ram['Total'])
            
            if pr_gb and actual_gb:
                if actual_gb >= pr_gb:
                    status_icon = "✓" if actual_gb == pr_gb else "✓✓"
                    extra = f" (exceeds by {actual_gb - pr_gb}GB)" if actual_gb > pr_gb else ""
                    return {
                        'component': 'RAM',
                        'status': 'PASS',
                        'details': f"{status_icon} Actual ({actual_gb}GB) meets or exceeds PR requirement ({pr_gb}GB){extra}"
                    }
                else:
                    return {
                        'component': 'RAM',
                        'status': 'FAIL',
                        'details': f"✗ Actual ({actual_gb}GB) is {pr_gb - actual_gb}GB less than PR requirement ({pr_gb}GB)"
                    }
        except:
            pass
        
        return {
            'component': 'RAM',
            'status': 'WARNING',
            'details': f"⚠ Could not validate: PR: {pr_ram}, Actual: {actual_ram['Total']}"
        }

    def validate_storage(self, pr_storage: str, actual_storage: Dict) -> Dict:
        """Validate storage specifications"""
        if not pr_storage:
            return {'component': 'Storage', 'status': 'PASS', 'details': 'No PR specification provided'}
        
        try:
            pr_gb = self.extract_gb(pr_storage)
            if not pr_gb:
                return {'component': 'Storage', 'status': 'CHECK', 'details': 'Could not parse PR storage spec'}
            
            # Calculate total actual storage
            total_actual_gb = 0
            for drive, info in actual_storage.items():
                if 'Total' in info:
                    drive_gb = self.extract_gb(info['Total'])
                    if drive_gb:
                        total_actual_gb += drive_gb
            
            if total_actual_gb >= pr_gb:
                return {
                    'component': 'Storage', 
                    'status': 'PASS', 
                    'details': f"Actual ({total_actual_gb}GB) meets PR requirement ({pr_gb}GB)"
                }
            else:
                return {
                    'component': 'Storage', 
                    'status': 'FAIL', 
                    'details': f"Actual ({total_actual_gb}GB) less than PR requirement ({pr_gb}GB)"
                }
                
        except Exception as e:
            return {
                'component': 'Storage', 
                'status': 'CHECK', 
                'details': f"Validation error: {str(e)}"
            }

    def extract_gb(self, text: str) -> int:
        """Extract GB number from text"""
        if not text:
            return None
        match = re.search(r'(\d+)\s*GB?', text.upper())
        return int(match.group(1)) if match else None

    def display_validation_results(self, results: List[Dict], overall_status: str):
        """Display validation results"""
        result_text = f"=== SPECIFICATION VALIDATION RESULTS ===\n"
        result_text += f"Overall Status: {overall_status}\n\n"
        
        for result in results:
            status_icon = "✅" if result['status'] == 'PASS' else "❌" if result['status'] == 'FAIL' else "⚠️"
            result_text += f"{status_icon} {result['component']}: {result['status']}\n"
            result_text += f"   Details: {result['details']}\n\n"
        
        self.validation_results.setText(result_text)

    # === DATA MANAGEMENT METHODS ===

    def save_inspection(self):
        """Save inspection to database"""
        try:
            if not all([self.inspector_name.text(), self.serial_number.text()]):
                QMessageBox.warning(self, "Missing Data", "Please fill in required fields.")
                return
            
            inspection_data = {
                'detected_specs': self.current_inspection.get('detected_specs', {}),
                'physical_condition': {
                    'chassis': self.chassis_condition.currentText(),
                    'screen': self.screen_condition.currentText(),
                    'keyboard': self.keyboard_condition.currentText(),
                    'ports': self.ports_condition.currentText(),
                    'notes': self.physical_notes.text()
                },
                'purchase_request_specs': {
                    'cpu': self.pr_cpu.text(),
                    'ram': self.pr_ram.text(),
                    'storage': self.pr_storage.text(),
                    'graphics': self.pr_graphics.text(),
                    'wifi': self.pr_wifi.text(),
                    'notes': self.pr_notes.text()
                },
                'performance_tests': self.current_inspection.get('performance_tests', ''),
                'validation_results': self.inspection_results
            }
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO inspections 
                (inspection_date, inspector_name, inspector_signature, inspector_id,
                 approver_signature, approver_id, certificate_id, signature_timestamp,
                 agency_name, pr_number, serial_number, laptop_model, inspection_data, 
                 overall_status, created_at, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.inspection_date.date().toString("yyyy-MM-dd"),
                self.inspector_name.text(),
                self.current_inspection.get('inspector_signature', ''),
                self.current_inspection.get('inspector_id', ''),
                self.current_inspection.get('approver_signature', ''),
                self.current_inspection.get('approver_id', ''),
                self.current_inspection.get('certificate_id', ''),
                self.current_inspection.get('signature_timestamp', ''),
                self.agency_name.text(),
                self.pr_number.text(),
                self.serial_number.text(),
                self.laptop_model.text(),
                json.dumps(inspection_data),
                self.inspection_results.get('overall_status', 'NOT_VALIDATED'),
                datetime.now().isoformat(),
                self.user_info['username']
            ))
            
            conn.commit()
            conn.close()
            
            # Mark pending inspection as completed if it was loaded from pending
            if hasattr(self, 'current_pending_id') and self.current_pending_id:
                try:
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE pending_inspections 
                        SET status = 'completed' 
                        WHERE id = ?
                    ''', (self.current_pending_id,))
                    conn.commit()
                    conn.close()
                    self.current_pending_id = None
                    self.load_pending_inspections()  # Refresh pending list
                except:
                    pass  # Don't fail the save if pending update fails
            
            self.log_action("Save Inspection", f"S/N: {self.serial_number.text()}, PR: {self.pr_number.text()}")
            QMessageBox.information(self, "Success", "Inspection saved successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Error saving inspection: {str(e)}")

    def load_inspections(self):
        """Load inspection history"""
        self.inspections_list.clear()
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            search_term = f"%{self.search_field.text()}%"
            cursor.execute('''
                SELECT id, inspection_date, inspector_name, agency_name, 
                       pr_number, serial_number, laptop_model, overall_status
                FROM inspections 
                WHERE serial_number LIKE ? OR pr_number LIKE ? OR agency_name LIKE ?
                ORDER BY inspection_date DESC
            ''', (search_term, search_term, search_term))
            
            for row in cursor.fetchall():
                status_icon = "✅" if row[7] == "PASS" else "❌" if row[7] == "FAIL" else "⚠️"
                item_text = f"{status_icon} {row[1]} | {row[3]} | PR: {row[4]} | S/N: {row[5]}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, row[0])  # Store ID
                self.inspections_list.addItem(item)
            
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Error loading inspections: {str(e)}")

    def view_inspection_details(self, item):
        """View details of a specific inspection"""
        inspection_id = item.data(Qt.UserRole)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM inspections WHERE id = ?', (inspection_id,))
            inspection = cursor.fetchone()
            conn.close()
            
            if inspection:
                self.show_inspection_dialog(inspection)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading inspection: {str(e)}")

    def show_inspection_dialog(self, inspection):
        """Show inspection details in a dialog"""
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Inspection Details")
        
        # Parse inspection data
        inspection_data = json.loads(inspection[9])  # inspection_data field
        
        details_text = f"""
        Inspection ID: {inspection[0]}
        Date: {inspection[1]}
        Inspector: {inspection[2]}
        Agency: {inspection[4]}
        PR Number: {inspection[5]}
        Serial Number: {inspection[6]}
        Overall Status: {inspection[10]}
        """
        
        dialog.setText(details_text)
        
        # Show detailed data
        detailed_text = f"Full inspection data:\n{json.dumps(inspection_data, indent=2)}"
        dialog.setDetailedText(detailed_text)
        dialog.exec()

    # === REPORTING METHODS ===

    def generate_comprehensive_pdf_report(self):
        """Generate comprehensive PDF report with all details"""
        try:
            if not self.serial_number.text():
                QMessageBox.warning(self, "Missing Data", "Please enter serial number first.")
                return
                
            filename = f"COA_Comprehensive_Inspection_{self.serial_number.text()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            doc = SimpleDocTemplate(filename, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=30,
                alignment=1  # Center
            )
            title = Paragraph("COMMISSION ON AUDIT<br/>LAPTOP INSPECTION REPORT", title_style)
            story.append(title)
            
            # Inspection Details
            details_data = [
                ['Inspector:', self.inspector_name.text()],
                ['Agency:', self.agency_name.text()],
                ['PR Number:', self.pr_number.text()],
                ['Serial Number:', self.serial_number.text()],
                ['Model:', self.laptop_model.text()],
                ['Inspection Date:', self.inspection_date.date().toString("yyyy-MM-dd")],
                ['Overall Status:', self.inspection_results.get('overall_status', 'Not Validated')]
            ]
            
            details_table = Table(details_data, colWidths=[200, 300])
            details_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(details_table)
            story.append(Spacer(1, 20))
            
            # Add validation results table if available
            if self.inspection_results.get('validation'):
                validation_data = [['Component', 'Status', 'Details']]
                for result in self.inspection_results['validation']:
                    validation_data.append([
                        result['component'],
                        result['status'],
                        result['details']
                    ])
                
                validation_table = Table(validation_data, colWidths=[100, 80, 320])
                validation_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(Paragraph("Specification Validation Results", styles['Heading2']))
                story.append(validation_table)
                story.append(Spacer(1, 20))
            
            doc.build(story)
            QMessageBox.information(self, "PDF Generated", f"Comprehensive report saved as {filename}")
            
        except Exception as e:
            QMessageBox.critical(self, "PDF Error", f"Error generating PDF: {str(e)}")

    def export_to_excel(self):
        """Export inspection to Excel format"""
        try:
            if not self.serial_number.text():
                QMessageBox.warning(self, "Missing Data", "Please enter serial number first.")
                return
                
            filename = f"COA_Inspection_{self.serial_number.text()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            # Create Excel file with inspection data
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Summary sheet
                summary_data = {
                    'Field': ['Inspector', 'Agency', 'PR Number', 'Serial Number', 'Model', 'Inspection Date', 'Overall Status'],
                    'Value': [
                        self.inspector_name.text(),
                        self.agency_name.text(),
                        self.pr_number.text(),
                        self.serial_number.text(),
                        self.laptop_model.text(),
                        self.inspection_date.date().toString("yyyy-MM-dd"),
                        self.inspection_results.get('overall_status', 'Not Validated')
                    ]
                }
                pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
                
                # Hardware specs sheet
                if self.current_inspection.get('detected_specs'):
                    hardware_data = []
                    for category, specs in self.current_inspection['detected_specs'].items():
                        if isinstance(specs, dict):
                            for key, value in specs.items():
                                hardware_data.append([category, key, str(value)])
                    
                    pd.DataFrame(hardware_data, columns=['Category', 'Spec', 'Value']).to_excel(
                        writer, sheet_name='Hardware_Specs', index=False)
                
            QMessageBox.information(self, "Excel Export", f"Data exported to {filename}")
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Error exporting to Excel: {str(e)}")

    def generate_analytics(self):
        """Generate analytics from historical data"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get basic statistics
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM inspections")
            total_inspections = cursor.fetchone()[0]
            
            cursor.execute("SELECT overall_status, COUNT(*) FROM inspections GROUP BY overall_status")
            status_counts = cursor.fetchall()
            
            analytics_text = f"=== INSPECTION ANALYTICS ===\n\n"
            analytics_text += f"Total Inspections: {total_inspections}\n\n"
            analytics_text += "Status Distribution:\n"
            
            for status, count in status_counts:
                percentage = (count / total_inspections * 100) if total_inspections > 0 else 0
                analytics_text += f"  {status}: {count} ({percentage:.1f}%)\n"
            
            self.analytics_text.setText(analytics_text)
            conn.close()
            
        except Exception as e:
            self.analytics_text.setText(f"Error generating analytics: {str(e)}")
    
    def export_database(self):
        """Export database to a file"""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Export Database",
                f"coa_inspections_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
                "Database Files (*.db);;All Files (*)"
            )
            
            if filename:
                import shutil
                shutil.copy2(self.db_path, filename)
                self.log_action("Export Database", f"Exported to: {filename}")
                QMessageBox.information(self, "Success", f"Database exported successfully to:\n{filename}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Error exporting database: {str(e)}")
    
    def import_database(self):
        """Import database from a file"""
        try:
            reply = QMessageBox.question(
                self,
                "Import Database",
                "WARNING: Importing will replace your current database.\nMake sure you have a backup!\n\nContinue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                filename, _ = QFileDialog.getOpenFileName(
                    self,
                    "Import Database",
                    "",
                    "Database Files (*.db);;All Files (*)"
                )
                
                if filename:
                    import shutil
                    # Create backup before import
                    backup_name = f"coa_inspections_backup_before_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                    shutil.copy2(self.db_path, backup_name)
                    
                    # Import new database
                    shutil.copy2(filename, self.db_path)
                    
                    self.log_action("Import Database", f"Imported from: {filename}")
                    QMessageBox.information(
                        self,
                        "Success",
                        f"Database imported successfully!\nBackup saved as: {backup_name}"
                    )
                    
                    # Reload inspections
                    self.load_inspections()
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Error importing database: {str(e)}")
    
    def backup_database(self):
        """Create a backup of the database"""
        try:
            backup_name = f"coa_inspections_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            import shutil
            shutil.copy2(self.db_path, backup_name)
            
            self.log_action("Backup Database", f"Backup created: {backup_name}")
            QMessageBox.information(
                self,
                "Backup Created",
                f"Database backup created successfully:\n{backup_name}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Backup Error", f"Error creating backup: {str(e)}")
    
    def view_audit_log(self):
        """View audit log of all actions"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT timestamp, username, action, details 
                FROM audit_log 
                ORDER BY timestamp DESC 
                LIMIT 100
            ''')
            
            logs = cursor.fetchall()
            conn.close()
            
            # Create dialog to display logs
            dialog = QDialog(self)
            dialog.setWindowTitle("Audit Log")
            dialog.resize(800, 600)
            
            layout = QVBoxLayout()
            
            log_table = QTableWidget()
            log_table.setColumnCount(4)
            log_table.setHorizontalHeaderLabels(["Timestamp", "User", "Action", "Details"])
            log_table.setRowCount(len(logs))
            
            for row, log in enumerate(logs):
                for col, value in enumerate(log):
                    log_table.setItem(row, col, QTableWidgetItem(str(value)))
            
            log_table.resizeColumnsToContents()
            layout.addWidget(log_table)
            
            close_button = QPushButton("Close")
            close_button.clicked.connect(dialog.accept)
            layout.addWidget(close_button)
            
            dialog.setLayout(layout)
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error viewing audit log: {str(e)}")
    
    def show_about(self):
        """Show about dialog"""
        about_text = """
        <h2>COA Laptop Inspection System</h2>
        <p><b>Version:</b> 2.5</p>
        <p><b>Developer:</b> Commission on Audit</p>
        <p><b>Purpose:</b> Comprehensive laptop hardware inspection and validation system</p>
        <br>
        <p><b>Features:</b></p>
        <ul>
            <li>Automatic hardware detection</li>
            <li>Purchase request validation</li>
            <li>Digital signatures with certificates</li>
            <li>Performance testing</li>
            <li>Comprehensive reporting (PDF & Excel)</li>
            <li>Database backup and export</li>
            <li>Audit logging</li>
        </ul>
        <br>
        <p><i>© 2025 Commission on Audit. All rights reserved.</i></p>
        """
        
        QMessageBox.about(self, "About", about_text)
    
    def change_password(self):
        """Change user password"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Change Password")
        dialog.setModal(True)
        dialog.setFixedSize(400, 250)
        
        layout = QVBoxLayout()
        
        info_label = QLabel(f"Change password for user: {self.user_info['username']}")
        info_label.setStyleSheet("font-weight: bold; padding: 8px;")
        layout.addWidget(info_label)
        
        form_layout = QFormLayout()
        
        current_password = QLineEdit()
        current_password.setEchoMode(QLineEdit.Password)
        current_password.setPlaceholderText("Enter current password")
        form_layout.addRow("Current Password:*", current_password)
        
        new_password = QLineEdit()
        new_password.setEchoMode(QLineEdit.Password)
        new_password.setPlaceholderText("Enter new password (min 6 chars)")
        form_layout.addRow("New Password:*", new_password)
        
        confirm_password = QLineEdit()
        confirm_password.setEchoMode(QLineEdit.Password)
        confirm_password.setPlaceholderText("Re-enter new password")
        form_layout.addRow("Confirm Password:*", confirm_password)
        
        layout.addLayout(form_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec():
            current_pass = current_password.text()
            new_pass = new_password.text()
            confirm_pass = confirm_password.text()
            
            # Validate inputs
            if not all([current_pass, new_pass, confirm_pass]):
                QMessageBox.warning(self, "Error", "All fields are required.")
                return
            
            # Verify current password
            creds_file = Path("coa_credentials.dat")
            if not creds_file.exists():
                QMessageBox.critical(self, "Error", "Credentials file not found.")
                return
            
            try:
                encoded = creds_file.read_text()
                credentials = json.loads(base64.b64decode(encoded).decode())
                current_hash = hashlib.sha256(current_pass.encode()).hexdigest()
                
                if credentials['password'] != current_hash:
                    QMessageBox.warning(self, "Error", "Current password is incorrect.")
                    return
                
                # Validate new password
                if len(new_pass) < 6:
                    QMessageBox.warning(self, "Error", "New password must be at least 6 characters.")
                    return
                
                if new_pass != confirm_pass:
                    QMessageBox.warning(self, "Error", "New passwords do not match.")
                    return
                
                if current_pass == new_pass:
                    QMessageBox.warning(self, "Error", "New password must be different from current password.")
                    return
                
                # Save new password
                new_hash = hashlib.sha256(new_pass.encode()).hexdigest()
                credentials['password'] = new_hash
                credentials['last_changed'] = datetime.now().isoformat()
                
                encoded = base64.b64encode(json.dumps(credentials).encode()).decode()
                creds_file.write_text(encoded)
                
                self.log_action("Change Password", "Password changed successfully")
                QMessageBox.information(
                    self, 
                    "Success", 
                    "Password changed successfully!\n\nPlease remember your new password."
                )
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error changing password: {str(e)}")
    
    # === TEMPLATE MANAGEMENT METHODS ===
    
    def load_templates(self):
        """Load all PR templates from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, template_name, agency_name, pr_cpu, pr_ram, pr_storage
                FROM pr_templates
                ORDER BY template_name
            ''')
            templates = cursor.fetchall()
            conn.close()
            
            self.templates_table.setRowCount(len(templates))
            
            for row, template in enumerate(templates):
                template_id, name, agency, cpu, ram, storage = template
                
                self.templates_table.setItem(row, 0, QTableWidgetItem(name))
                self.templates_table.setItem(row, 1, QTableWidgetItem(agency or "N/A"))
                self.templates_table.setItem(row, 2, QTableWidgetItem(cpu))
                self.templates_table.setItem(row, 3, QTableWidgetItem(ram))
                self.templates_table.setItem(row, 4, QTableWidgetItem(storage))
                
                # Actions buttons
                actions_widget = QWidget()
                actions_layout = QHBoxLayout()
                actions_layout.setContentsMargins(2, 2, 2, 2)
                actions_layout.setSpacing(4)
                
                use_btn = QPushButton("▶️ Use")
                use_btn.clicked.connect(lambda checked, tid=template_id: self.use_template(tid))
                use_btn.setStyleSheet("padding: 6px 8px; background-color: #4CAF50; color: white; font-weight: bold;")
                use_btn.setMinimumWidth(70)
                
                edit_btn = QPushButton("✏️ Edit")
                edit_btn.clicked.connect(lambda checked, tid=template_id: self.edit_template(tid))
                edit_btn.setStyleSheet("padding: 6px 8px;")
                edit_btn.setMinimumWidth(70)
                
                delete_btn = QPushButton("🗑️")
                delete_btn.clicked.connect(lambda checked, tid=template_id: self.delete_template(tid))
                delete_btn.setStyleSheet("padding: 6px 8px; background-color: #f44336; color: white;")
                delete_btn.setMinimumWidth(40)
                delete_btn.setToolTip("Delete Template")
                
                actions_layout.addWidget(use_btn)
                actions_layout.addWidget(edit_btn)
                actions_layout.addWidget(delete_btn)
                actions_layout.addStretch()
                actions_widget.setLayout(actions_layout)
                
                self.templates_table.setCellWidget(row, 5, actions_widget)
            
            self.templates_table.resizeRowsToContents()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading templates: {str(e)}")
    
    def create_new_template(self):
        """Create a new PR template"""
        dialog = PRTemplateDialog(self)
        if dialog.exec():
            template_data = dialog.get_template_data()
            
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO pr_templates 
                    (template_name, agency_name, pr_cpu, pr_ram, pr_storage, pr_graphics, pr_wifi, pr_notes, created_by, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    template_data['template_name'],
                    template_data['agency_name'],
                    template_data['pr_cpu'],
                    template_data['pr_ram'],
                    template_data['pr_storage'],
                    template_data['pr_graphics'],
                    template_data['pr_wifi'],
                    template_data['pr_notes'],
                    self.user_info['username'],
                    datetime.now().isoformat()
                ))
                conn.commit()
                conn.close()
                
                self.log_action("Create Template", f"Template: {template_data['template_name']}")
                QMessageBox.information(self, "Success", "Template created successfully!")
                self.load_templates()
                
            except sqlite3.IntegrityError:
                QMessageBox.warning(self, "Duplicate", "A template with this name already exists.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error creating template: {str(e)}")
    
    def edit_template(self, template_id):
        """Edit an existing template"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM pr_templates WHERE id = ?', (template_id,))
            template = cursor.fetchone()
            conn.close()
            
            if template:
                template_data = {
                    'template_name': template[1],
                    'agency_name': template[2],
                    'pr_cpu': template[3],
                    'pr_ram': template[4],
                    'pr_storage': template[5],
                    'pr_graphics': template[6],
                    'pr_wifi': template[7],
                    'pr_notes': template[8]
                }
                
                dialog = PRTemplateDialog(self, template_data)
                if dialog.exec():
                    updated_data = dialog.get_template_data()
                    
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE pr_templates 
                        SET template_name=?, agency_name=?, pr_cpu=?, pr_ram=?, pr_storage=?, 
                            pr_graphics=?, pr_wifi=?, pr_notes=?
                        WHERE id=?
                    ''', (
                        updated_data['template_name'],
                        updated_data['agency_name'],
                        updated_data['pr_cpu'],
                        updated_data['pr_ram'],
                        updated_data['pr_storage'],
                        updated_data['pr_graphics'],
                        updated_data['pr_wifi'],
                        updated_data['pr_notes'],
                        template_id
                    ))
                    conn.commit()
                    conn.close()
                    
                    self.log_action("Edit Template", f"Template: {updated_data['template_name']}")
                    QMessageBox.information(self, "Success", "Template updated successfully!")
                    self.load_templates()
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error editing template: {str(e)}")
    
    def delete_template(self, template_id):
        """Delete a template"""
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this template?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('DELETE FROM pr_templates WHERE id = ?', (template_id,))
                conn.commit()
                conn.close()
                
                self.log_action("Delete Template", f"Template ID: {template_id}")
                QMessageBox.information(self, "Success", "Template deleted successfully!")
                self.load_templates()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error deleting template: {str(e)}")
    
    def use_template(self, template_id):
        """Load template specs into new inspection tab"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM pr_templates WHERE id = ?', (template_id,))
            template = cursor.fetchone()
            conn.close()
            
            if template:
                self.agency_name.setText(template[2] or "")
                self.pr_cpu.setText(template[3])
                self.pr_ram.setText(template[4])
                self.pr_storage.setText(template[5])
                self.pr_graphics.setText(template[6] or "")
                self.pr_wifi.setText(template[7] or "")
                self.pr_notes.setText(template[8] or "")
                
                # Switch to inspection tab
                tabs = self.centralWidget().findChild(QTabWidget)
                if tabs:
                    tabs.setCurrentIndex(0)
                
                QMessageBox.information(self, "Template Loaded", f"Template '{template[1]}' loaded successfully!\nFill in PR Number and Serial Number to continue.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error using template: {str(e)}")
    
    # === PENDING INSPECTIONS MANAGEMENT METHODS ===
    
    def load_pending_inspections(self):
        """Load all pending inspections from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, pr_number, agency_name, laptop_model, pr_cpu, pr_ram, pr_storage, status
                FROM pending_inspections
                WHERE status = 'pending'
                ORDER BY created_at DESC
            ''')
            pending = cursor.fetchall()
            conn.close()
            
            self.pending_table.setRowCount(len(pending))
            
            for row, inspection in enumerate(pending):
                insp_id, pr_num, agency, model, cpu, ram, storage, status = inspection
                
                self.pending_table.setItem(row, 0, QTableWidgetItem(pr_num))
                self.pending_table.setItem(row, 1, QTableWidgetItem(agency))
                self.pending_table.setItem(row, 2, QTableWidgetItem(model or "TBD"))
                self.pending_table.setItem(row, 3, QTableWidgetItem(cpu))
                self.pending_table.setItem(row, 4, QTableWidgetItem(ram))
                self.pending_table.setItem(row, 5, QTableWidgetItem(storage))
                
                # Actions buttons
                actions_widget = QWidget()
                actions_layout = QHBoxLayout()
                actions_layout.setContentsMargins(2, 2, 2, 2)
                actions_layout.setSpacing(4)
                
                start_btn = QPushButton("▶️ Start")
                start_btn.clicked.connect(lambda checked, pid=insp_id: self.start_pending_inspection(pid))
                start_btn.setStyleSheet("padding: 6px 8px; background-color: #4CAF50; color: white; font-weight: bold;")
                start_btn.setMinimumWidth(80)
                
                edit_btn = QPushButton("✏️")
                edit_btn.clicked.connect(lambda checked, pid=insp_id: self.edit_pending(pid))
                edit_btn.setStyleSheet("padding: 6px 8px;")
                edit_btn.setMinimumWidth(40)
                edit_btn.setToolTip("Edit Pending Inspection")
                
                delete_btn = QPushButton("🗑️")
                delete_btn.clicked.connect(lambda checked, pid=insp_id: self.delete_pending(pid))
                delete_btn.setStyleSheet("padding: 6px 8px; background-color: #f44336; color: white;")
                delete_btn.setMinimumWidth(40)
                delete_btn.setToolTip("Delete Pending Inspection")
                
                actions_layout.addWidget(start_btn)
                actions_layout.addWidget(edit_btn)
                actions_layout.addWidget(delete_btn)
                actions_layout.addStretch()
                actions_widget.setLayout(actions_layout)
                
                self.pending_table.setCellWidget(row, 6, actions_widget)
            
            self.pending_table.resizeRowsToContents()
            
            # Update statistics
            self.pending_stats_label.setText(f"📊 Total Pending Inspections: {len(pending)}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading pending inspections: {str(e)}")
    
    def create_new_pending(self):
        """Create a new pending inspection"""
        # Get templates for dropdown
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT id, template_name, agency_name, pr_cpu, pr_ram, pr_storage, pr_graphics, pr_wifi, pr_notes FROM pr_templates')
            templates = [dict(zip(['id', 'template_name', 'agency_name', 'pr_cpu', 'pr_ram', 'pr_storage', 'pr_graphics', 'pr_wifi', 'pr_notes'], row)) for row in cursor.fetchall()]
            conn.close()
            
            dialog = PendingInspectionDialog(self, templates)
            if dialog.exec():
                pending_data = dialog.get_pending_data()
                
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO pending_inspections 
                    (agency_name, pr_number, laptop_model, expected_serial, pr_cpu, pr_ram, pr_storage, 
                     pr_graphics, pr_wifi, pr_notes, status, created_by, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                ''', (
                    pending_data['agency_name'],
                    pending_data['pr_number'],
                    pending_data['laptop_model'],
                    pending_data['expected_serial'],
                    pending_data['pr_cpu'],
                    pending_data['pr_ram'],
                    pending_data['pr_storage'],
                    pending_data['pr_graphics'],
                    pending_data['pr_wifi'],
                    pending_data['pr_notes'],
                    self.user_info['username'],
                    datetime.now().isoformat()
                ))
                conn.commit()
                conn.close()
                
                self.log_action("Create Pending Inspection", f"PR: {pending_data['pr_number']}")
                QMessageBox.information(self, "Success", "Pending inspection created successfully!")
                self.load_pending_inspections()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error creating pending inspection: {str(e)}")
    
    def edit_pending(self, pending_id):
        """Edit a pending inspection"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM pending_inspections WHERE id = ?', (pending_id,))
            pending = cursor.fetchone()
            
            # Get templates
            cursor.execute('SELECT id, template_name, agency_name, pr_cpu, pr_ram, pr_storage, pr_graphics, pr_wifi, pr_notes FROM pr_templates')
            templates = [dict(zip(['id', 'template_name', 'agency_name', 'pr_cpu', 'pr_ram', 'pr_storage', 'pr_graphics', 'pr_wifi', 'pr_notes'], row)) for row in cursor.fetchall()]
            conn.close()
            
            if pending:
                pending_data = {
                    'agency_name': pending[1],
                    'pr_number': pending[2],
                    'laptop_model': pending[3],
                    'expected_serial': pending[4],
                    'pr_cpu': pending[5],
                    'pr_ram': pending[6],
                    'pr_storage': pending[7],
                    'pr_graphics': pending[8],
                    'pr_wifi': pending[9],
                    'pr_notes': pending[10]
                }
                
                dialog = PendingInspectionDialog(self, templates, pending_data)
                if dialog.exec():
                    updated_data = dialog.get_pending_data()
                    
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE pending_inspections 
                        SET agency_name=?, pr_number=?, laptop_model=?, expected_serial=?, 
                            pr_cpu=?, pr_ram=?, pr_storage=?, pr_graphics=?, pr_wifi=?, pr_notes=?
                        WHERE id=?
                    ''', (
                        updated_data['agency_name'],
                        updated_data['pr_number'],
                        updated_data['laptop_model'],
                        updated_data['expected_serial'],
                        updated_data['pr_cpu'],
                        updated_data['pr_ram'],
                        updated_data['pr_storage'],
                        updated_data['pr_graphics'],
                        updated_data['pr_wifi'],
                        updated_data['pr_notes'],
                        pending_id
                    ))
                    conn.commit()
                    conn.close()
                    
                    self.log_action("Edit Pending Inspection", f"Pending ID: {pending_id}")
                    QMessageBox.information(self, "Success", "Pending inspection updated successfully!")
                    self.load_pending_inspections()
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error editing pending inspection: {str(e)}")
    
    def delete_pending(self, pending_id):
        """Delete a pending inspection"""
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this pending inspection?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('DELETE FROM pending_inspections WHERE id = ?', (pending_id,))
                conn.commit()
                conn.close()
                
                self.log_action("Delete Pending Inspection", f"Pending ID: {pending_id}")
                QMessageBox.information(self, "Success", "Pending inspection deleted successfully!")
                self.load_pending_inspections()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error deleting pending inspection: {str(e)}")
    
    def start_pending_inspection(self, pending_id):
        """Start a pending inspection - load data into inspection tab"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM pending_inspections WHERE id = ?', (pending_id,))
            pending = cursor.fetchone()
            conn.close()
            
            if pending:
                # Load data into inspection form
                self.agency_name.setText(pending[1])
                self.pr_number.setText(pending[2])
                self.laptop_model.setText(pending[3] or "")
                self.serial_number.setText(pending[4] or "")
                self.pr_cpu.setText(pending[5])
                self.pr_ram.setText(pending[6])
                self.pr_storage.setText(pending[7])
                self.pr_graphics.setText(pending[8] or "")
                self.pr_wifi.setText(pending[9] or "")
                self.pr_notes.setText(pending[10] or "")
                
                # Store pending ID for later marking as completed
                self.current_pending_id = pending_id
                
                # Switch to inspection tab
                tabs = self.centralWidget().findChild(QTabWidget)
                if tabs:
                    tabs.setCurrentIndex(0)
                
                QMessageBox.information(
                    self,
                    "Inspection Started",
                    f"Pending inspection loaded!\n\nPR: {pending[2]}\nAgency: {pending[1]}\n\nNext steps:\n1. Fill in Serial Number (if not yet entered)\n2. Auto-Detect Hardware\n3. Validate & Complete"
                )
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error starting inspection: {str(e)}")
    
    def quick_load_pending(self):
        """Quick load from pending inspections"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, pr_number, agency_name 
                FROM pending_inspections 
                WHERE status = 'pending'
                ORDER BY created_at DESC
            ''')
            pending_list = cursor.fetchall()
            conn.close()
            
            if not pending_list:
                QMessageBox.information(self, "No Pending", "No pending inspections found.\n\nGo to 'Pending Inspections' tab to create some!")
                return
            
            # Create selection dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("Select Pending Inspection")
            dialog.setModal(True)
            dialog.resize(400, 300)
            
            layout = QVBoxLayout()
            
            label = QLabel("Select a pending inspection to load:")
            layout.addWidget(label)
            
            list_widget = QListWidget()
            for pid, pr_num, agency in pending_list:
                item = QListWidgetItem(f"{pr_num} - {agency}")
                item.setData(Qt.UserRole, pid)
                list_widget.addItem(item)
            
            list_widget.itemDoubleClicked.connect(dialog.accept)
            layout.addWidget(list_widget)
            
            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)
            
            dialog.setLayout(layout)
            
            if dialog.exec() and list_widget.currentItem():
                selected_id = list_widget.currentItem().data(Qt.UserRole)
                self.start_pending_inspection(selected_id)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading pending inspection: {str(e)}")
    
    def quick_load_template(self):
        """Quick load from templates"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT id, template_name, agency_name FROM pr_templates ORDER BY template_name')
            templates_list = cursor.fetchall()
            conn.close()
            
            if not templates_list:
                QMessageBox.information(self, "No Templates", "No templates found.\n\nGo to 'PR Templates' tab to create some!")
                return
            
            # Create selection dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("Select PR Template")
            dialog.setModal(True)
            dialog.resize(400, 300)
            
            layout = QVBoxLayout()
            
            label = QLabel("Select a template to load:")
            layout.addWidget(label)
            
            list_widget = QListWidget()
            for tid, template_name, agency in templates_list:
                item = QListWidgetItem(f"{template_name} ({agency or 'No Agency'})")
                item.setData(Qt.UserRole, tid)
                list_widget.addItem(item)
            
            list_widget.itemDoubleClicked.connect(dialog.accept)
            layout.addWidget(list_widget)
            
            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)
            
            dialog.setLayout(layout)
            
            if dialog.exec() and list_widget.currentItem():
                selected_id = list_widget.currentItem().data(Qt.UserRole)
                self.use_template(selected_id)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading template: {str(e)}")
            
    def create_comparison_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Comparison controls
        controls_layout = QHBoxLayout()
        
        # Inspection selection
        controls_layout.addWidget(QLabel("Select Inspection:"))
        self.inspection_combo = QComboBox()
        self.inspection_combo.currentTextChanged.connect(self.load_selected_inspection)
        controls_layout.addWidget(self.inspection_combo)
        
        # Refresh button
        self.refresh_comparison_btn = QPushButton("🔄 Refresh")
        self.refresh_comparison_btn.clicked.connect(self.load_inspection_combo)
        controls_layout.addWidget(self.refresh_comparison_btn)
        
        # Compare current button
        self.compare_current_btn = QPushButton("⚡ Compare Current Inspection")
        self.compare_current_btn.clicked.connect(self.compare_current_inspection)
        controls_layout.addWidget(self.compare_current_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Comparison table
        self.comparison_table = QTableWidget()
        self.comparison_table.setColumnCount(5)
        self.comparison_table.setHorizontalHeaderLabels([
            "Component", "Purchase Request", "Actual Spec", "Status", "Notes"
        ])
        
        # Set column widths
        header = self.comparison_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Component
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # PR Spec
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # Actual Spec
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Status
        header.setSectionResizeMode(4, QHeaderView.Stretch)  # Notes
        
        layout.addWidget(self.comparison_table)
        
        # Summary section
        summary_group = QGroupBox("Comparison Summary")
        summary_layout = QVBoxLayout()
        summary_group.setLayout(summary_layout)
        
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setMaximumHeight(120)
        summary_layout.addWidget(self.summary_text)
        
        layout.addWidget(summary_group)
        
        # Load inspections combo
        self.load_inspection_combo()
        
        return widget

    def load_inspection_combo(self):
        """Load inspections into the combo box"""
        self.inspection_combo.clear()
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, inspection_date, agency_name, pr_number, serial_number, laptop_model 
                FROM inspections 
                ORDER BY inspection_date DESC
            ''')
            
            for row in cursor.fetchall():
                display_text = f"{row[1]} - {row[2]} - PR:{row[3]} - S/N:{row[4]}"
                self.inspection_combo.addItem(display_text, row[0])  # Store ID as user data
            
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Error loading inspections: {str(e)}")

    def load_selected_inspection(self):
        """Load and display the selected inspection for comparison"""
        inspection_id = self.inspection_combo.currentData()
        if not inspection_id:
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT inspection_data FROM inspections WHERE id = ?', (inspection_id,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                inspection_data = json.loads(result[0])
                self.display_comparison_results(inspection_data)
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading inspection: {str(e)}")

    def compare_current_inspection(self):
        """Compare the current (unsaved) inspection data"""
        if not self.current_inspection.get('detected_specs'):
            QMessageBox.warning(self, "No Data", "Please detect hardware specs first.")
            return
        
        # Create a mock inspection data structure from current inputs
        current_data = {
            'detected_specs': self.current_inspection.get('detected_specs', {}),
            'purchase_request_specs': {
                'cpu': self.pr_cpu.text(),
                'ram': self.pr_ram.text(),
                'storage': self.pr_storage.text(),
                'graphics': self.pr_graphics.text(),
                'wifi': self.pr_wifi.text()
            },
            'physical_condition': {
                'chassis': self.chassis_condition.currentText(),
                'screen': self.screen_condition.currentText(),
                'keyboard': self.keyboard_condition.currentText(),
                'ports': self.ports_condition.currentText()
            }
        }
        
        self.display_comparison_results(current_data)

    def display_comparison_results(self, inspection_data):
        """Display comprehensive comparison results in the table"""
        detected_specs = inspection_data.get('detected_specs', {})
        pr_specs = inspection_data.get('purchase_request_specs', {})
        physical_condition = inspection_data.get('physical_condition', {})
        
        # Prepare comparison data
        comparison_data = []
        
        # === HARDWARE COMPARISON ===
        
        # CPU Comparison
        cpu_result = self.compare_cpu_specs(pr_specs.get('cpu', ''), detected_specs.get('CPU', {}))
        comparison_data.append(cpu_result)
        
        # RAM Comparison
        ram_result = self.compare_ram_specs(pr_specs.get('ram', ''), detected_specs.get('RAM', {}))
        comparison_data.append(ram_result)
        
        # Storage Comparison
        storage_result = self.compare_storage_specs(pr_specs.get('storage', ''), detected_specs.get('Storage', {}))
        comparison_data.append(storage_result)
        
        # Graphics Comparison
        graphics_result = self.compare_graphics_specs(pr_specs.get('graphics', ''), detected_specs.get('Graphics', {}))
        comparison_data.append(graphics_result)
        
        # Network/WiFi Comparison
        wifi_result = self.compare_wifi_specs(pr_specs.get('wifi', ''), detected_specs.get('Network', {}))
        comparison_data.append(wifi_result)
        
        # === PHYSICAL CONDITION ASSESSMENT ===
        
        # Chassis Condition
        chassis_result = self.assess_physical_condition("Chassis", physical_condition.get('chassis', ''))
        comparison_data.append(chassis_result)
        
        # Screen Condition
        screen_result = self.assess_physical_condition("Screen", physical_condition.get('screen', ''))
        comparison_data.append(screen_result)
        
        # Keyboard Condition
        keyboard_result = self.assess_physical_condition("Keyboard", physical_condition.get('keyboard', ''))
        comparison_data.append(keyboard_result)
        
        # Ports Condition
        ports_result = self.assess_physical_condition("Ports", physical_condition.get('ports', ''))
        comparison_data.append(ports_result)
        
        # === SYSTEM INFORMATION ===
        
        # OS Information
        if 'System' in detected_specs:
            os_info = detected_specs['System'].get('OS', 'Unknown')
            comparison_data.append({
                'component': 'Operating System',
                'pr_spec': 'N/A',
                'actual_spec': os_info,
                'status': 'INFO',
                'notes': 'Detected operating system'
            })
        
        # Battery Information
        if 'Battery' in detected_specs:
            battery_info = detected_specs['Battery']
            battery_status = f"{battery_info.get('Percent', 'N/A')} - {battery_info.get('Power Plugged', 'N/A')}"
            comparison_data.append({
                'component': 'Battery',
                'pr_spec': 'N/A',
                'actual_spec': battery_status,
                'status': 'INFO',
                'notes': 'Battery status'
            })
        
        # Populate the table
        self.populate_comparison_table(comparison_data)
        self.update_comparison_summary(comparison_data)

    def compare_cpu_specs(self, pr_cpu: str, actual_cpu: dict) -> dict:
        """Compare CPU specifications"""
        actual_name = actual_cpu.get('Name', 'Not detected')
        actual_cores = actual_cpu.get('Cores', 'N/A')
        actual_threads = actual_cpu.get('Threads', 'N/A')
        
        if not pr_cpu:
            return {
                'component': 'CPU',
                'pr_spec': 'Not specified',
                'actual_spec': f"{actual_name} ({actual_cores} cores, {actual_threads} threads)",
                'status': 'INFO',
                'notes': 'No PR specification provided'
            }
        
        # Enhanced CPU matching
        pr_upper = pr_cpu.upper()
        actual_upper = actual_name.upper()
        
        # Check for model number matches (e.g., i7, i5, Ryzen 7, etc.)
        common_indicators = ['I7', 'I5', 'I3', 'RYZEN 7', 'RYZEN 5', 'RYZEN 3', 'CORE I7', 'CORE I5', 'CORE I3']
        
        pr_indicator = next((ind for ind in common_indicators if ind in pr_upper), None)
        actual_indicator = next((ind for ind in common_indicators if ind in actual_upper), None)
        
        if pr_indicator and actual_indicator and pr_indicator == actual_indicator:
            return {
                'component': 'CPU',
                'pr_spec': pr_cpu,
                'actual_spec': f"{actual_name} ({actual_cores} cores, {actual_threads} threads)",
                'status': 'PASS',
                'notes': f'CPU tier matches: {pr_indicator}'
            }
        elif pr_upper in actual_upper:
            return {
                'component': 'CPU',
                'pr_spec': pr_cpu,
                'actual_spec': f"{actual_name} ({actual_cores} cores, {actual_threads} threads)",
                'status': 'PASS',
                'notes': 'Exact CPU model match'
            }
        else:
            return {
                'component': 'CPU',
                'pr_spec': pr_cpu,
                'actual_spec': f"{actual_name} ({actual_cores} cores, {actual_threads} threads)",
                'status': 'FAIL',
                'notes': 'CPU specification does not match PR requirements'
            }

    def compare_ram_specs(self, pr_ram: str, actual_ram: dict) -> dict:
        """Compare RAM specifications"""
        actual_total = actual_ram.get('Total', 'Not detected')
        
        if not pr_ram:
            return {
                'component': 'RAM',
                'pr_spec': 'Not specified',
                'actual_spec': actual_total,
                'status': 'INFO',
                'notes': 'No PR specification provided'
            }
        
        pr_gb = self.extract_gb(pr_ram)
        actual_gb = self.extract_gb(actual_total)
        
        if pr_gb and actual_gb:
            if actual_gb >= pr_gb:
                return {
                    'component': 'RAM',
                    'pr_spec': pr_ram,
                    'actual_spec': actual_total,
                    'status': 'PASS',
                    'notes': f'RAM capacity meets requirement ({actual_gb}GB >= {pr_gb}GB)'
                }
            else:
                return {
                    'component': 'RAM',
                    'pr_spec': pr_ram,
                    'actual_spec': actual_total,
                    'status': 'FAIL',
                    'notes': f'RAM capacity insufficient ({actual_gb}GB < {pr_gb}GB)'
                }
        
        return {
            'component': 'RAM',
            'pr_spec': pr_ram,
            'actual_spec': actual_total,
            'status': 'WARNING',
            'notes': 'Could not parse RAM specifications for comparison'
        }

    def compare_storage_specs(self, pr_storage: str, actual_storage: dict) -> dict:
        """Compare storage specifications"""
        if not pr_storage:
            return {
                'component': 'Storage',
                'pr_spec': 'Not specified',
                'actual_spec': self.format_storage_info(actual_storage),
                'status': 'INFO',
                'notes': 'No PR specification provided'
            }
        
        pr_gb = self.extract_gb(pr_storage)
        total_actual_gb = 0
        
        # Calculate total storage from all drives
        for drive, info in actual_storage.items():
            if 'Total' in info:
                drive_gb = self.extract_gb(info['Total'])
                if drive_gb:
                    total_actual_gb += drive_gb
        
        if pr_gb and total_actual_gb > 0:
            if total_actual_gb >= pr_gb:
                return {
                    'component': 'Storage',
                    'pr_spec': pr_storage,
                    'actual_spec': self.format_storage_info(actual_storage),
                    'status': 'PASS',
                    'notes': f'Total storage meets requirement ({total_actual_gb}GB >= {pr_gb}GB)'
                }
            else:
                return {
                    'component': 'Storage',
                    'pr_spec': pr_storage,
                    'actual_spec': self.format_storage_info(actual_storage),
                    'status': 'FAIL',
                    'notes': f'Total storage insufficient ({total_actual_gb}GB < {pr_gb}GB)'
                }
        
        return {
            'component': 'Storage',
            'pr_spec': pr_storage,
            'actual_spec': self.format_storage_info(actual_storage),
            'status': 'WARNING',
            'notes': 'Could not parse storage specifications'
        }

    def compare_graphics_specs(self, pr_graphics: str, actual_graphics: dict) -> dict:
        """Compare graphics specifications"""
        actual_cards = actual_graphics.get('Cards', ['Not detected'])
        actual_display = ", ".join(actual_cards) if isinstance(actual_cards, list) else str(actual_cards)
        
        if not pr_graphics:
            return {
                'component': 'Graphics',
                'pr_spec': 'Not specified',
                'actual_spec': actual_display,
                'status': 'INFO',
                'notes': 'No PR specification provided'
            }
        
        pr_upper = pr_graphics.upper()
        actual_upper = actual_display.upper()
        
        # Check for graphics card family matches
        common_families = ['GEFORCE', 'RADEON', 'INTEL HD', 'INTEL UHD', 'IRIS XE']
        
        pr_family = next((fam for fam in common_families if fam in pr_upper), None)
        actual_family = next((fam for fam in common_families if fam in actual_upper), None)
        
        if pr_family and actual_family:
            if pr_family in actual_family or actual_family in pr_family:
                return {
                    'component': 'Graphics',
                    'pr_spec': pr_graphics,
                    'actual_spec': actual_display,
                    'status': 'PASS',
                    'notes': f'Graphics family matches: {pr_family}'
                }
        
        if pr_upper in actual_upper:
            return {
                'component': 'Graphics',
                'pr_spec': pr_graphics,
                'actual_spec': actual_display,
                'status': 'PASS',
                'notes': 'Exact graphics card match'
            }
        
        return {
            'component': 'Graphics',
            'pr_spec': pr_graphics,
            'actual_spec': actual_display,
            'status': 'FAIL',
            'notes': 'Graphics specification does not match PR requirements'
        }

    def compare_wifi_specs(self, pr_wifi: str, actual_network: dict) -> dict:
        """Compare WiFi specifications"""
        # Extract WiFi adapters from network info
        wifi_adapters = []
        for interface, info in actual_network.items():
            if any(wifi_keyword in interface.upper() for wifi_keyword in ['WIFI', 'WIRELESS', '802.11']):
                wifi_adapters.append(interface)
        
        actual_display = ", ".join(wifi_adapters) if wifi_adapters else "No WiFi adapters detected"
        
        if not pr_wifi:
            return {
                'component': 'WiFi',
                'pr_spec': 'Not specified',
                'actual_spec': actual_display,
                'status': 'INFO',
                'notes': 'No PR specification provided'
            }
        
        # Basic WiFi standard checking
        wifi_standards = ['802.11AX', 'WIFI 6', '802.11AC', 'WIFI 5', '802.11N', 'WIFI 4']
        
        pr_upper = pr_wifi.upper()
        actual_upper = actual_display.upper()
        
        pr_standard = next((std for std in wifi_standards if std in pr_upper), None)
        actual_standard = next((std for std in wifi_standards if std in actual_upper), None)
        
        if pr_standard and actual_standard:
            # Compare WiFi standards (higher is better)
            pr_index = wifi_standards.index(pr_standard)
            actual_index = wifi_standards.index(actual_standard)
            
            if actual_index <= pr_index:  # Lower index means better standard
                return {
                    'component': 'WiFi',
                    'pr_spec': pr_wifi,
                    'actual_spec': actual_display,
                    'status': 'PASS',
                    'notes': f'WiFi standard meets requirement: {actual_standard}'
                }
            else:
                return {
                    'component': 'WiFi',
                    'pr_spec': pr_wifi,
                    'actual_spec': actual_display,
                    'status': 'FAIL',
                    'notes': f'WiFi standard insufficient: {actual_standard} vs required {pr_standard}'
                }
        
        return {
            'component': 'WiFi',
            'pr_spec': pr_wifi,
            'actual_spec': actual_display,
            'status': 'WARNING',
            'notes': 'Could not verify WiFi specifications'
        }

    def assess_physical_condition(self, component: str, condition: str) -> dict:
        """Assess physical condition and return comparison result"""
        condition_map = {
            'Excellent': 'PASS',
            'Good': 'PASS', 
            'Fair': 'WARNING',
            'Poor': 'FAIL',
            'Damaged': 'FAIL',
            'Cracked': 'FAIL',
            'Non-functional': 'FAIL',
            'All Working': 'PASS',
            'Some Issues': 'WARNING',
            'Major Issues': 'FAIL'
        }
        
        status = condition_map.get(condition, 'INFO')
        
        return {
            'component': f'Physical {component}',
            'pr_spec': 'Good Condition',
            'actual_spec': condition,
            'status': status,
            'notes': f'Physical condition assessment: {condition}'
        }

    def format_storage_info(self, storage_info: dict) -> str:
        """Format storage information for display"""
        if not storage_info:
            return "No storage devices detected"
        
        drives = []
        for drive, info in storage_info.items():
            if 'Total' in info:
                drives.append(f"{info.get('Device', drive)}: {info['Total']}")
        
        return " | ".join(drives) if drives else "Storage info unavailable"

    def populate_comparison_table(self, comparison_data):
        """Populate the comparison table with data"""
        self.comparison_table.setRowCount(len(comparison_data))
        
        for row, data in enumerate(comparison_data):
            # Component
            self.comparison_table.setItem(row, 0, QTableWidgetItem(data['component']))
            
            # PR Spec
            self.comparison_table.setItem(row, 1, QTableWidgetItem(data['pr_spec']))
            
            # Actual Spec
            self.comparison_table.setItem(row, 2, QTableWidgetItem(data['actual_spec']))
            
            # Status with colored icons
            status_item = QTableWidgetItem(data['status'])
            
            # Set background color based on status
            if data['status'] == 'PASS':
                status_item.setBackground(Qt.green)
            elif data['status'] == 'FAIL':
                status_item.setBackground(Qt.red)
            elif data['status'] == 'WARNING':
                status_item.setBackground(Qt.yellow)
            elif data['status'] == 'INFO':
                status_item.setBackground(Qt.blue)
            
            self.comparison_table.setItem(row, 3, status_item)
            
            # Notes
            self.comparison_table.setItem(row, 4, QTableWidgetItem(data['notes']))
        
        # Resize columns to content
        self.comparison_table.resizeColumnsToContents()

    def update_comparison_summary(self, comparison_data):
        """Update the comparison summary text"""
        total_components = len(comparison_data)
        pass_count = sum(1 for item in comparison_data if item['status'] == 'PASS')
        fail_count = sum(1 for item in comparison_data if item['status'] == 'FAIL')
        warning_count = sum(1 for item in comparison_data if item['status'] == 'WARNING')
        info_count = sum(1 for item in comparison_data if item['status'] == 'INFO')
        
        pass_percentage = (pass_count / total_components * 100) if total_components > 0 else 0
        
        summary_text = f"""
    === COMPARISON SUMMARY ===

    Total Components Checked: {total_components}
    ✅ PASS: {pass_count} ({pass_percentage:.1f}%)
    ❌ FAIL: {fail_count}
    ⚠️ WARNING: {warning_count}
    ℹ️ INFO: {info_count}

    Overall Status: {'PASS' if fail_count == 0 else 'FAIL'}
    """
        
        if fail_count > 0:
            failed_components = [item['component'] for item in comparison_data if item['status'] == 'FAIL']
            summary_text += f"\nFailed Components: {', '.join(failed_components)}"
        
        self.summary_text.setText(summary_text.strip())

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Show login dialog first
    login_dialog = LoginDialog()
    if login_dialog.exec():
        if login_dialog.authenticated:
            window = LaptopInspectorApp(login_dialog.user_info)
            window.show()
            sys.exit(app.exec())
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()