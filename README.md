# COA Laptop Inspection System v2.5

## Overview

A comprehensive laptop hardware inspection and validation system designed for the Commission on Audit (COA) to verify hardware specifications against Purchase Requests and Purchase Orders.

## Key Features

### 🔐 Security & Authentication

- **Login System**: Secure authentication with encrypted password storage
- **Digital Signatures**: Enhanced signature system with certificate generation
- **Audit Logging**: Complete audit trail of all user actions

### 🔍 Hardware Detection

- **CPU**: Full processor details including cores, threads, and frequency
- **RAM**: Memory capacity, type (DDR3/DDR4/DDR5), and speed
- **Storage**: All drives with capacity and file system details
- **Graphics**: Video card detection
- **Display**: Monitor resolution and specifications
- **Peripherals**: Webcam, audio devices, USB devices, Bluetooth
- **Network**: Network adapters and connectivity testing
- **Battery**: Battery status and health (for laptops)
- **BIOS/Firmware**: Complete BIOS information
- **Warranty**: Basic warranty information with manufacturer details

### ✅ Validation & Comparison

- **Equal or Better Logic**: Validates that actual specs meet or exceed Purchase Request requirements
- **Smart CPU Comparison**: Understands CPU tiers (i3/i5/i7/i9, Ryzen 3/5/7/9)
- **Memory Validation**: Checks if RAM meets or exceeds requirements
- **Storage Validation**: Validates total storage capacity
- **Comprehensive Reports**: Detailed pass/fail status for all components

### 📊 Reporting & Export

- **PDF Reports**: Professional inspection reports with digital certificates
- **Excel Export**: Data export for further analysis
- **Database Export/Import**: Full database backup and portability
- **Analytics**: Historical data analysis and statistics

### 🛠️ Performance Testing

- CPU performance benchmarks
- Memory performance tests
- Disk read/write speed tests

## Installation

### Requirements

- Windows 10/11 (64-bit)
- Python 3.13.1
- USB drive (for portable operation)

### Setup Instructions

1. **Install Python Dependencies**

   ```powershell
   pip install -r requirements.txt
   ```

2. **First Run**

   - Launch the application: `python main.py`
   - Click "First Time Setup" on the login screen
   - Create your username and password (minimum 6 characters)
   - Login with your credentials

3. **For Portable USB Operation**
   - Copy the entire application folder to your USB drive
   - Run `python main.py` directly from the USB
   - All data (database, credentials) will be stored on the USB

## Usage Guide

### Starting an Inspection

1. **Login**: Enter your credentials
2. **Fill Inspection Details**:

   - Inspector Name (auto-filled with your username)
   - Agency Name
   - Purchase Request Number
   - Serial Number
   - Laptop Model
   - Inspection Date

3. **Auto-Detect Hardware**:

   - Click "🔍 Auto-Detect Hardware Specs"
   - Wait for detection to complete
   - Review detected specifications

4. **Enter Purchase Request Specs**:

   - Fill in the required specifications from the PR/PO
   - Include CPU, RAM, Storage, Graphics, WiFi requirements

5. **Physical Inspection**:

   - Assess chassis, screen, keyboard, and ports condition
   - Add notes for any physical issues

6. **Run Tests** (Optional):

   - Click "Run Comprehensive Performance Tests"
   - Click "🌐 Test Network Connectivity"

7. **Validate Specifications**:

   - Click "✅ Validate Specifications"
   - Review pass/fail results
   - System uses "equal or better" logic

8. **Add Digital Signatures**:

   - Click "🖊️ Add Digital Signatures"
   - Enter inspector and approver information
   - System generates a unique certificate ID

9. **Save & Generate Report**:
   - Click "💾 Save Inspection" to store in database
   - Click "📊 Generate PDF Report" for official documentation
   - Click "📈 Export to Excel" for data analysis

### Comparison Tab

- View side-by-side comparison of PR specs vs actual specs
- Visual pass/fail indicators
- Comprehensive summary statistics

### Inspection History

- Search past inspections by serial number, PR number, or agency
- Double-click to view full details
- Export or backup database

### Analytics

- View inspection statistics
- Pass/fail distribution
- Historical trends

## Menu Options

### File Menu

- **📦 Export Database**: Export entire database to file
- **📥 Import Database**: Import database (creates automatic backup)
- **Exit**: Close application

### Tools Menu

- **💾 Backup Database**: Create timestamped backup
- **📋 View Audit Log**: View all user actions
  - Shows last 100 actions
  - Includes timestamp, user, action, and details

### Help Menu

- **About**: Application information and version

## Data Storage

All data is stored locally:

- `coa_inspections.db`: Main database with all inspections
- `coa_credentials.dat`: Encrypted user credentials
- `coa_inspections_backup_*.db`: Automatic backups

## Validation Logic

### CPU Validation

- Recognizes processor tiers (i9 > i7 > i5 > i3)
- Validates equal or higher tier
- Example: i7 meets i5 requirement ✓

### RAM Validation

- Compares actual GB vs required GB
- Passes if actual >= required
- Example: 16GB meets 8GB requirement ✓

### Storage Validation

- Calculates total storage across all drives
- Validates total capacity
- Example: 512GB SSD meets 256GB requirement ✓

## Security Features

### Password Encryption

- SHA-256 hashing
- Base64 encoding for storage
- No plaintext passwords

### Digital Certificates

- Unique certificate ID per inspection
- SHA-256 based generation
- Embedded in PDF reports

### Audit Trail

- All actions logged with timestamp
- User attribution
- Cannot be deleted or modified by user

## Troubleshooting

### Hardware Detection Issues

- **Run as Administrator**: Some hardware queries require elevated privileges
- **Windows Management Instrumentation**: Ensure WMI service is running
- **Antivirus**: May block hardware queries

### Database Issues

- **Locked Database**: Close other instances of the application
- **Corrupted Database**: Use database import to restore from backup

### Performance Issues

- **Slow Detection**: Normal on older systems
- **Network Tests**: Requires internet connection

## Building Portable Executable

To create a standalone executable:

```powershell
pyinstaller --onefile --windowed --name "COA_Laptop_Inspector" main.py
```

The executable will be in the `dist` folder.

## Best Practices

1. **Regular Backups**: Use "Backup Database" before import operations
2. **Export Database**: Export monthly to external storage
3. **Complete Signatures**: Always add digital signatures before generating reports
4. **Physical Inspection**: Don't rely solely on automated detection
5. **USB Operation**: Keep application and data on USB for portability

## System Requirements

### Minimum

- Windows 10 (64-bit)
- 4GB RAM
- 500MB free disk space
- USB 2.0 port

### Recommended

- Windows 11 (64-bit)
- 8GB RAM
- 1GB free disk space
- USB 3.0 port

## Support & Updates

Version: 2.5
Last Updated: November 25, 2025
Developed for: Commission on Audit

## License

© 2025 Commission on Audit. All rights reserved.
Internal use only.
