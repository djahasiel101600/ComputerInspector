# CHANGELOG - COA Laptop Inspection System

## Version 2.5 - November 25, 2025

### 🔐 Security & Authentication

**NEW: Login System**

- Secure login dialog with username/password authentication
- First-time setup wizard for creating credentials
- Password encryption using SHA-256 hashing
- Credentials stored securely with base64 encoding
- User information displayed in title bar

**ENHANCED: Digital Signatures**

- Complete redesign of signature system
- Added Inspector ID and Approver ID fields
- Automatic certificate ID generation using SHA-256
- Certificate ID embedded in all reports
- Signature timestamp for audit purposes
- Pre-filled inspector name from logged-in user

### 🔍 Hardware Detection Improvements

**NEW: Enhanced RAM Detection**

- RAM type detection (DDR3/DDR4/DDR5)
- RAM speed (MHz) detection
- Number of RAM modules
- Detailed memory information

**NEW: Display Information**

- Screen resolution detection
- Display name/model
- Primary monitor identification
- Multiple methods for better compatibility

**NEW: Peripheral Device Detection**

- Webcam detection and identification
- Audio device enumeration
- USB device count
- Bluetooth adapter detection
- Peripheral status reporting

**NEW: Warranty Information**

- System manufacturer identification
- Model number extraction
- Serial number verification
- Warranty lookup guidance

**IMPROVED: BIOS Information**

- Better serial number detection
- Multiple fallback methods
- PowerShell integration for reliability
- Release date formatting

**IMPROVED: CPU Detection**

- Current frequency monitoring
- Better processor name parsing
- Enhanced core/thread information

### ✅ Validation & Comparison

**ENHANCED: "Equal or Better" Logic**

- CPU tier comparison (i9/i7/i5/i3, Ryzen 9/7/5/3)
- Automatic upgrade detection
- Smart matching algorithms
- Clear pass/fail indicators with icons (✓, ✗, ⚠)

**IMPROVED: RAM Validation**

- Shows excess capacity when exceeding requirements
- Example: "16GB (exceeds by 8GB)" for 8GB requirement
- Clear status icons

**IMPROVED: Storage Validation**

- Multi-drive aggregation
- Total capacity calculation
- Better error handling

**IMPROVED: Validation Display**

- Visual status indicators
- Detailed explanation of pass/fail reasons
- Warning status for unclear cases

### 📊 Database & Data Management

**NEW: Enhanced Database Schema**

- Added inspector_id and approver_id fields
- Certificate_id storage
- Signature timestamp tracking
- Created_by user attribution
- Enhanced audit trail

**NEW: Audit Logging System**

- Complete action logging
- Timestamp tracking
- User attribution
- Action details
- View last 100 actions via menu

**NEW: Export/Import Capabilities**

- Export database to external file
- Import database with automatic backup
- Timestamped file names
- Safety warnings before import

**NEW: Database Backup**

- One-click backup creation
- Timestamped backup files
- Automatic backup before import
- Stored in application directory

### 🎨 User Interface

**NEW: Menu Bar**

- File Menu: Export, Import, Exit
- Tools Menu: Backup, Audit Log
- Help Menu: About

**IMPROVED: About Dialog**

- Professional HTML formatting
- Version information
- Feature list
- Copyright information

**IMPROVED: Status Bar**

- User information display
- Better visual feedback
- Action confirmations

### 📄 Reporting

**ENHANCED: PDF Reports**

- Certificate ID inclusion
- Inspector and Approver IDs
- Enhanced signature section
- Professional formatting
- Timestamp information

**IMPROVED: Excel Export**

- Additional fields
- Certificate information
- Better data structure

### 🛠️ Code Quality

**IMPROVED: Error Handling**

- Better exception catching
- User-friendly error messages
- Graceful degradation
- Timeout handling for WMI queries

**IMPROVED: Code Organization**

- Clear method documentation
- Type hints added
- Better naming conventions
- Modular design

**IMPROVED: Performance**

- Optimized hardware detection
- Better WMI query handling
- Reduced timeout issues
- Progress feedback during operations

### 🔧 Bug Fixes

- Fixed PyQt6/PySide6 confusion - standardized on PySide6
- Fixed missing imports (hashlib, base64, Optional)
- Fixed database schema mismatches
- Improved serial number detection reliability
- Better handling of missing hardware information
- Fixed display detection on various systems

### 📋 Dependencies

**REMOVED:**

- PyQt6==6.9.1
- PyQt6-Qt6==6.9.1
- PyQt6_sip==13.10.2

**KEPT:**

- PySide6==6.9.1 (primary GUI framework)
- All other dependencies maintained

### 🚀 New Features Summary

1. ✅ Login system with encrypted credentials
2. ✅ Enhanced digital signatures with certificates
3. ✅ "Equal or better" validation logic
4. ✅ Enhanced hardware detection (RAM details, display, peripherals, warranty)
5. ✅ Database export/import capabilities
6. ✅ Audit logging system
7. ✅ Menu bar with File/Tools/Help
8. ✅ Database backup functionality
9. ✅ Visual status indicators (✓, ✗, ⚠)
10. ✅ User attribution for all actions

### 📝 Documentation

**NEW Files:**

- README.md: Complete user guide and documentation
- CHANGES.md: This changelog

**UPDATED Files:**

- requirements.txt: Removed PyQt6, cleaned up dependencies
- main.py: Complete rewrite with 300+ lines added

### 🎯 Focus Areas

1. **Security**: Login system and credential encryption
2. **Audit Compliance**: Complete audit trail and certificate system
3. **Accuracy**: "Equal or better" validation logic
4. **Portability**: Export/import for USB operation
5. **User Experience**: Better feedback and visual indicators

### ⚙️ Technical Changes

- Added SHA-256 hashing for passwords and certificates
- Integrated base64 encoding for credential storage
- Enhanced database schema with 8 new fields
- Added type hints throughout codebase
- Improved WMI query error handling
- Added PowerShell fallbacks for better compatibility

### 🔜 Future Enhancements (Suggested)

- Photo attachment for physical condition
- Barcode/QR code scanning for serial numbers
- Advanced CPU benchmarking
- Network speed testing
- Multi-language support
- Cloud backup option (if network available)

---

## Version 2.0 (Previous)

- Initial comprehensive system
- Hardware detection
- Basic validation
- PDF and Excel reports
- Database storage
- Performance testing

---

**Migration Notes:**

- Existing databases will work but won't have new fields
- Users need to set up login credentials on first run
- Backup existing database before upgrading
- Certificate IDs will only be available for new inspections
