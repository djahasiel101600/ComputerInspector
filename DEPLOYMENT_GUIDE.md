# PyInstaller Build Command

`pyinstaller --name="COA_Laptop_Inspector" --onefile --windowed --icon=icon.ico --add-data="icon.ico;." --hidden-import=PySide6.QtCore --hidden-import=PySide6.QtGui --hidden-import=PySide6.QtWidgets --hidden-import=reportlab --hidden-import=pandas --hidden-import=openpyxl --hidden-import=psutil --collect-all reportlab --collect-all PySide6 main.py`

# COA Laptop Inspector - Deployment Guide

## Build Process

### Quick Build

Simply run `build.bat` to compile the application into a standalone executable.

```batch
.\build.bat
```

The build process will:

1. Check for PyInstaller installation
2. Install PyInstaller if needed
3. Compile the application using the spec file
4. Generate executable in `dist\` folder

### Build Output

- **Executable**: `dist\COA_Laptop_Inspector.exe`
- **Build artifacts**: `build\` folder (can be deleted after successful build)
- **Size**: Approximately 100-150 MB (includes Python runtime and all dependencies)

## Deployment Options

### Option 1: USB Drive Deployment (Recommended)

1. Copy `COA_Laptop_Inspector.exe` to USB drive
2. On first run, the application will create:
   - `coa_inspections.db` (SQLite database)
   - `coa_credentials.dat` (encrypted credentials)
3. All data stays on the USB drive for portability

### Option 2: Network Share Deployment

1. Copy executable to network share
2. Users run directly from network
3. Database and credentials created in same folder
4. Multiple users can have separate databases

### Option 3: Local Installation

1. Copy executable to `C:\Program Files\COA_Laptop_Inspector\`
2. Create desktop shortcut
3. Database stored with executable

## First Time Setup

### Initial Run

1. Launch `COA_Laptop_Inspector.exe`
2. Click **"First Time Setup"** button
3. Create admin credentials:
   - Username (minimum 3 characters)
   - Password (minimum 6 characters)
4. Credentials are encrypted and stored securely

### Subsequent Runs

- Login screen appears automatically
- "First Time Setup" button hidden after credentials created
- Use **Tools → Change Password** to update credentials

## Testing Checklist

Before deploying to production, test the following:

### Basic Functionality

- [ ] Application launches without errors
- [ ] First Time Setup creates credentials successfully
- [ ] Login authentication works
- [ ] Hardware detection retrieves system information

### Core Features

- [ ] **New Inspection Tab**: Can create new inspections
- [ ] **PR Templates Tab**: Can create/edit/delete templates
- [ ] **Pending Inspections Tab**: Can queue inspections
- [ ] **History Tab**: Can view past inspections
- [ ] **Comparison Tab**: Can compare specs
- [ ] **Analytics Tab**: Can view reports

### Hardware Detection

- [ ] CPU information detected
- [ ] RAM details (capacity, type, speed) detected
- [ ] Storage drives detected
- [ ] Display information detected
- [ ] Network adapters detected

### Report Generation

- [ ] PDF reports generate correctly
- [ ] Excel exports work
- [ ] Digital signatures applied
- [ ] Reports saved to correct location

### Database Operations

- [ ] Inspections save to database
- [ ] Templates save and load correctly
- [ ] Pending inspections queue works
- [ ] Audit log records actions

## Troubleshooting

### Common Issues

#### Application Won't Launch

- **Error**: "Missing DLL" or "Python not found"
- **Solution**: Ensure the build was completed successfully. Re-run `build.bat` with `--clean` flag.

#### Hardware Detection Fails

- **Error**: WMI queries return no data
- **Solution**: Run as Administrator. Check Windows Management Instrumentation service is running.

#### Reports Not Generating

- **Error**: PDF or Excel export fails
- **Solution**: Check write permissions to output folder. Ensure sufficient disk space.

#### Database Locked

- **Error**: "Database is locked"
- **Solution**: Close any other instances of the application. Check file permissions.

#### Slow Performance

- **Issue**: Application takes long to start
- **Solution**: Normal for first run (30-60 seconds). Subsequent runs faster. Consider disabling antivirus scan on .exe.

### Debug Mode

To enable verbose logging for troubleshooting:

1. Open Command Prompt in the folder containing the executable
2. Run: `COA_Laptop_Inspector.exe --debug`
3. Check generated log file for errors

## System Requirements

### Minimum Requirements

- **OS**: Windows 10 (64-bit) or Windows 11
- **RAM**: 4 GB
- **Storage**: 500 MB free space
- **Display**: 1280x720 resolution
- **Permissions**: Administrator rights (for hardware detection)

### Recommended Requirements

- **OS**: Windows 11 (64-bit)
- **RAM**: 8 GB or more
- **Storage**: 1 GB free space
- **Display**: 1920x1080 resolution

## Security Considerations

### Credential Storage

- Passwords hashed using SHA-256
- Credentials encoded with base64
- Stored in `coa_credentials.dat` file
- Keep credentials file secure

### Database Security

- SQLite database not encrypted by default
- Contains inspection data and audit logs
- Restrict file permissions appropriately
- Regular backups recommended

### Audit Trail

- All actions logged in `audit_log` table
- Includes timestamps and user identification
- Certificates have unique IDs for tracking

## Backup and Recovery

### What to Backup

1. **Database**: `coa_inspections.db` (contains all inspection data)
2. **Credentials**: `coa_credentials.dat` (user authentication)
3. **Reports**: PDF and Excel files in output folders

### Backup Frequency

- **Daily**: If performing multiple inspections
- **Weekly**: For normal usage
- **Before major updates**: Always backup before upgrading

### Recovery Process

1. Copy backed-up files to application folder
2. Launch application normally
3. Login with existing credentials
4. All data restored automatically

## Updates and Maintenance

### Updating the Application

1. Backup database and credentials
2. Replace executable with new version
3. Database schema updates automatically
4. Test functionality after update

### Database Maintenance

- Vacuum database periodically: SQLite management tool
- Archive old inspections to separate database
- Keep database size under 1 GB for optimal performance

## Distribution Package

### For End Users

Create a distribution folder containing:

```
COA_Laptop_Inspector/
├── COA_Laptop_Inspector.exe
├── README.md
├── QUICKSTART.md
├── TEMPLATES_GUIDE.md
└── DEPLOYMENT_GUIDE.md (this file)
```

### Installation Instructions for Users

1. Extract folder to desired location
2. Read QUICKSTART.md for basic usage
3. Run COA_Laptop_Inspector.exe
4. Complete First Time Setup
5. Start inspecting laptops!

## Support and Documentation

- **Quick Start**: See `QUICKSTART.md`
- **Templates Guide**: See `TEMPLATES_GUIDE.md`
- **Full Documentation**: See `README.md`
- **Change Log**: See `CHANGES.md`

## Version Information

- **Application Version**: 2.0.0
- **PyInstaller Version**: 6.17.0
- **Python Version**: 3.13.1/3.14.0
- **Build Date**: Check file properties of executable

---

**Note**: This application requires Windows Management Instrumentation (WMI) for hardware detection. Run as Administrator for best results.
