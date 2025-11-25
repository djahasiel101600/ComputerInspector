# Quick Start Guide - COA Laptop Inspection System

## First Time Setup (2 minutes)

### 1. Install Dependencies

```powershell
cd "directory"
pip install -r requirements.txt
```

### 2. Launch Application

```powershell
python main.py
```

### 3. Create Your Account

1. Click **"First Time Setup"** on login screen
2. Enter your **username** (e.g., your employee ID or name)
3. Enter a **password** (minimum 6 characters)
4. Confirm password
5. Click **OK**

### 4. Login

- Enter your username and password
- Click **"Login"**

---

## Quick Inspection Workflow (5-10 minutes)

### Step 1: Fill Basic Info (1 minute)

- Inspector Name: _(auto-filled)_
- Agency Name: **Enter agency requesting laptop**
- PR Number: **Enter Purchase Request number**
- Serial Number: **Enter laptop serial number**
- Laptop Model: **Enter laptop model**

### Step 2: Auto-Detect Hardware (1-2 minutes)

Click **"🔍 Auto-Detect Hardware Specs"**

- Wait for detection to complete
- Review detected specifications in left panel

### Step 3: Enter PR Requirements (1 minute)

In "Purchase Request Specifications" section, enter:

- Required CPU (e.g., "Intel Core i5")
- Required RAM (e.g., "8GB")
- Required Storage (e.g., "256GB SSD")
- Required Graphics _(optional)_
- Required WiFi _(optional)_

### Step 4: Physical Inspection (1 minute)

Assess and select condition for:

- ✅ Chassis Condition
- ✅ Screen Condition
- ✅ Keyboard Condition
- ✅ Ports Condition
- 📝 Add any notes

### Step 5: Validate (30 seconds)

Click **"✅ Validate Specifications"**

- System compares PR vs Actual
- Shows pass/fail for each component
- Reviews results in right panel

### Step 6: Add Signatures (30 seconds)

Click **"🖊️ Add Digital Signatures"**

- Inspector Name: _(pre-filled)_
- Enter your ID/Employee Number
- Approver Name: _(if available)_
- Approver ID: _(if available)_
- Certificate will be auto-generated
- Click **OK**

### Step 7: Save & Report (1 minute)

- Click **"💾 Save Inspection"** to save to database
- Click **"📊 Generate PDF Report"** for official document
- Click **"📈 Export to Excel"** for data analysis _(optional)_

---

## Common Tasks

### View Past Inspections

1. Go to **"Inspection History"** tab
2. Type in search box (serial number, PR number, or agency)
3. Click **"Search"**
4. Double-click any inspection to view details

### Compare Specifications

1. Go to **"Spec Comparison"** tab
2. Select an inspection from dropdown
3. Or click **"⚡ Compare Current Inspection"** to compare unsaved work
4. View side-by-side comparison with pass/fail indicators

### Backup Database

1. Click **Tools** menu
2. Select **"💾 Backup Database"**
3. Backup file created with timestamp

### Export Database (For USB Portability)

1. Click **File** menu
2. Select **"📦 Export Database"**
3. Choose location (e.g., your USB drive)
4. Save file

### View Audit Log

1. Click **Tools** menu
2. Select **"📋 View Audit Log"**
3. Review last 100 actions

---

## Keyboard Shortcuts

- **Enter**: Submit login / Move to next field
- **Escape**: Close dialogs
- **Alt+F**: File menu
- **Alt+T**: Tools menu
- **Alt+H**: Help menu

---

## Validation Logic

### ✓ PASS Criteria

- **CPU**: Equal or better tier (i7 meets i5 requirement)
- **RAM**: Equal or more capacity (16GB meets 8GB requirement)
- **Storage**: Equal or more capacity (512GB meets 256GB requirement)

### ✗ FAIL Criteria

- **CPU**: Lower tier (i3 does not meet i5 requirement)
- **RAM**: Less capacity (4GB does not meet 8GB requirement)
- **Storage**: Less capacity (128GB does not meet 256GB requirement)

### ⚠ WARNING

- Cannot determine if specifications match
- Manual verification required

---

## Tips for Best Results

### Hardware Detection

- ✅ Run application as **Administrator** for better detection
- ✅ Ensure laptop is fully booted before detection
- ✅ Connect laptop to power for accurate battery info

### Physical Inspection

- 🔍 Check all ports with actual devices
- 🔍 Test keyboard keys systematically
- 🔍 Inspect screen for dead pixels in white background
- 🔍 Check chassis for cracks, dents, or damage

### Data Entry

- ✏️ Use exact PR wording when possible
- ✏️ Include units (GB, MHz, etc.)
- ✏️ Double-check serial numbers
- ✏️ Add detailed notes for any issues

### Performance Tests (Optional)

- 🧪 Click **"Run Comprehensive Performance Tests"** to test:
  - CPU calculation speed
  - Memory sorting speed
  - Disk read/write speed
- 🌐 Click **"🌐 Test Network Connectivity"** to verify internet

---

## Troubleshooting

### "Cannot detect hardware"

- ✅ Right-click application → Run as Administrator
- ✅ Check Windows Management Instrumentation (WMI) service is running

### "Login failed"

- ✅ Ensure caps lock is off
- ✅ Use "First Time Setup" if first time
- ✅ Check credentials file exists: `coa_credentials.dat`

### "Database locked"

- ✅ Close any other instances of the application
- ✅ Check if database file is open in another program

### "Cannot generate PDF"

- ✅ Ensure `reportlab` package is installed
- ✅ Check write permissions in application folder

---

## For Portable USB Operation

### Setup USB Drive

1. Copy entire application folder to USB
2. Install Python on computers you'll use OR
3. Create standalone executable with PyInstaller:
   ```powershell
   pyinstaller --onefile --windowed --name "COA_Laptop_Inspector" main.py
   ```

### Using from USB

1. Plug in USB drive
2. Run application from USB location
3. All data stays on USB (portable!)
4. Regular backups recommended

---

## Support

For issues or questions:

- Check **README.md** for detailed documentation
- Check **CHANGES.md** for version history
- Review error messages carefully
- Check audit log for action history

---

## Security Notes

🔒 **Your credentials are encrypted**

- Password hashed with SHA-256
- Stored securely in `coa_credentials.dat`
- Never stored in plaintext

🔒 **Digital certificates are unique**

- Each inspection gets unique certificate ID
- Certificate ID includes timestamp and inspector info
- Embedded in PDF reports for authenticity

🔒 **All actions are logged**

- Audit log tracks all operations
- Cannot be deleted by users
- Includes timestamp and user attribution

---

**Ready to Start!**

The system is now ready for laptop inspections. Remember:

1. ✅ Login first
2. ✅ Detect hardware
3. ✅ Enter PR specs
4. ✅ Validate
5. ✅ Sign & Save
6. ✅ Generate report

**Good luck with your inspections!** 🚀
