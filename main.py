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
from typing import Dict, List, Tuple
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

class DigitalSignatureDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Digital Signature")
        self.setModal(True)
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout()
        
        # Signature canvas (simplified - would need actual signature capture)
        self.signature_label = QLabel("Inspector Signature:")
        layout.addWidget(self.signature_label)
        
        self.inspector_signature = QLineEdit()
        self.inspector_signature.setPlaceholderText("Enter your full name as signature")
        layout.addWidget(self.inspector_signature)
        
        self.approver_signature = QLineEdit()
        self.approver_signature.setPlaceholderText("Approver's full name")
        layout.addWidget(self.approver_signature)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_signatures(self):
        return self.inspector_signature.text(), self.approver_signature.text()

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
    def __init__(self):
        super().__init__()
        self.setWindowTitle("COA Laptop Inspection System v2.0")
        self.setGeometry(100, 100, 1400, 900)
        
        # Initialize database
        self.db_path = Path("coa_inspections.db")
        self.init_database()
        
        self.setup_ui()
        self.current_inspection = {}
        self.inspection_results = {}
    
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
                approver_signature TEXT,
                agency_name TEXT,
                pr_number TEXT,
                serial_number TEXT,
                laptop_model TEXT,
                inspection_data TEXT,
                overall_status TEXT,
                created_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Create tabs
        tabs = QTabWidget()
        main_layout.addWidget(tabs)
        
        # Tab 1: New Inspection
        tabs.addTab(self.create_inspection_tab(), "New Inspection")
        
        # Tab 2: Inspection History
        tabs.addTab(self.create_history_tab(), "Inspection History")
        
        # Tab 3: Comparison Reports
        tabs.addTab(self.create_comparison_tab(), "Spec Comparison")
        
        # Tab 4: Analytics (NEW)
        tabs.addTab(self.create_analytics_tab(), "Analytics")
        
    def create_inspection_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
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
        """Enhanced hardware detection with network testing"""
        try:
            specs = {}
            
            # CPU Information
            cpu_freq = psutil.cpu_freq()
            specs['CPU'] = {
                'Name': platform.processor(),
                'Cores': psutil.cpu_count(logical=False),
                'Threads': psutil.cpu_count(logical=True),
                'Max Frequency': f"{cpu_freq.max:.2f} MHz" if cpu_freq else "N/A"
            }
            
            # RAM Information
            memory = psutil.virtual_memory()
            specs['RAM'] = {
                'Total': f"{memory.total // (1024**3)} GB",
                'Available': f"{memory.available // (1024**3)} GB",
                'Used': f"{memory.used // (1024**3)} GB"
            }
            
            # Storage Information
            specs['Storage'] = self.get_storage_info()
            
            # Graphics Information
            specs['Graphics'] = self.get_graphics_info()
            
            # Network Information with connectivity test
            specs['Network'] = self.get_network_info()
            specs['Network']['Connectivity_Test'] = self.test_network_connectivity()
            
            # Battery Information (if available)
            specs['Battery'] = self.get_battery_info()
            
            # System Information
            specs['System'] = {
                'OS': f"{platform.system()} {platform.version()}",
                'Architecture': platform.architecture()[0],
                'Hostname': platform.node()
            }
            
            # BIOS/Serial Information
            specs['BIOS'] = self.get_bios_info()
            
            self.display_specs(specs)
            self.current_inspection['detected_specs'] = specs
            
        except Exception as e:
            QMessageBox.critical(self, "Detection Error", f"Error detecting hardware: {str(e)}")

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
        """Get BIOS information"""
        try:
            if platform.system() == "Windows":
                result = subprocess.run([
                    'wmic', 'bios', 'get', 'serialnumber'
                ], capture_output=True, text=True, shell=True)
                
                lines = [line.strip() for line in result.stdout.split('\n') 
                        if line.strip() and 'SerialNumber' not in line]
                serial = lines[0] if lines else "Not available"
                
                return {
                    'Serial Number': serial,
                    'BIOS Version': 'Use wmic bios get version for details'
                }
            return {'Info': 'BIOS info available on Windows only'}
        except:
            return {'Error': 'Could not retrieve BIOS info'}

    def test_network_connectivity(self):
        """Test basic network connectivity"""
        try:
            # Test internet connectivity
            result = subprocess.run(['ping', '-n', '1', '8.8.8.8'], 
                                  capture_output=True, text=True, timeout=10, shell=True)
            return "Internet: Connected" if result.returncode == 0 else "Internet: No Connection"
        except:
            return "Internet: Test Failed"

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
        """Add digital signatures to inspection"""
        dialog = DigitalSignatureDialog(self)
        if dialog.exec():
            inspector_sig, approver_sig = dialog.get_signatures()
            if inspector_sig:
                self.current_inspection['inspector_signature'] = inspector_sig
            if approver_sig:
                self.current_inspection['approver_signature'] = approver_sig
            QMessageBox.information(self, "Success", "Digital signatures added successfully!")

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
        """Validate CPU specifications"""
        if not pr_cpu:
            return {'component': 'CPU', 'status': 'PASS', 'details': 'No PR specification provided'}
        
        actual_name = actual_cpu['Name'].upper()
        
        # Basic matching logic - can be enhanced
        if pr_cpu in actual_name:
            return {'component': 'CPU', 'status': 'PASS', 'details': f"Matches: {actual_name}"}
        else:
            return {
                'component': 'CPU', 
                'status': 'FAIL', 
                'details': f"PR: {pr_cpu}, Actual: {actual_name} - DOES NOT MATCH"
            }

    def validate_ram(self, pr_ram: str, actual_ram: Dict) -> Dict:
        """Validate RAM specifications"""
        if not pr_ram:
            return {'component': 'RAM', 'status': 'PASS', 'details': 'No PR specification provided'}
        
        try:
            # Extract numbers from strings
            pr_gb = self.extract_gb(pr_ram)
            actual_gb = self.extract_gb(actual_ram['Total'])
            
            if pr_gb and actual_gb:
                if actual_gb >= pr_gb:
                    return {
                        'component': 'RAM', 
                        'status': 'PASS', 
                        'details': f"Actual ({actual_gb}GB) meets PR requirement ({pr_gb}GB)"
                    }
                else:
                    return {
                        'component': 'RAM', 
                        'status': 'FAIL', 
                        'details': f"Actual ({actual_gb}GB) less than PR requirement ({pr_gb}GB)"
                    }
        except:
            pass
        
        return {
            'component': 'RAM', 
            'status': 'CHECK', 
            'details': f"Could not validate: PR: {pr_ram}, Actual: {actual_ram['Total']}"
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
                (inspection_date, inspector_name, inspector_signature, approver_signature,
                 agency_name, pr_number, serial_number, laptop_model, inspection_data, 
                 overall_status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.inspection_date.date().toString("yyyy-MM-dd"),
                self.inspector_name.text(),
                self.current_inspection.get('inspector_signature', ''),
                self.current_inspection.get('approver_signature', ''),
                self.agency_name.text(),
                self.pr_number.text(),
                self.serial_number.text(),
                self.laptop_model.text(),
                json.dumps(inspection_data),
                self.inspection_results.get('overall_status', 'NOT_VALIDATED'),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
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
    
    window = LaptopInspectorApp()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()