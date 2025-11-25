# PR Templates & Pending Inspections Feature Guide

## Overview

This new feature allows you to prepare inspection data in advance, making it easy to inspect multiple laptops efficiently. Perfect for batch inspections where multiple computers arrive together!

## Two Main Components

### 1. 📋 PR Templates

Reusable specification templates for common Purchase Request types.

**Use Case:**

- You often receive laptops with the same specs (e.g., "Standard Office Laptop 2025")
- Save the specs once, reuse for multiple inspections

**Benefits:**

- No need to re-type the same specs repeatedly
- Consistent specification entry
- Quick setup for new inspections

### 2. ⏳ Pending Inspections

Pre-created inspection jobs ready to be completed.

**Use Case:**

- You know you'll inspect 10 laptops tomorrow
- Create all 10 pending inspections in advance with PR details
- When inspecting, just load each one, detect hardware, and save

**Benefits:**

- Prepare everything in the office before going to the field
- Sequential workflow: create → inspect → complete
- Track what's been done and what's pending

---

## How to Use PR Templates

### Creating a Template

1. Go to **"📋 PR Templates"** tab
2. Click **"➕ New Template"**
3. Fill in:
   - **Template Name**: e.g., "Standard Office Laptop 2025"
   - **Agency**: (optional) Default agency name
   - **Required Specs**:
     - CPU (e.g., "Intel Core i5")
     - RAM (e.g., "8GB")
     - Storage (e.g., "256GB SSD")
     - Graphics (optional)
     - WiFi (optional)
     - Notes (optional)
4. Click **OK** to save

### Using a Template

**Method 1: From Templates Tab**

1. Go to **"📋 PR Templates"** tab
2. Find your template
3. Click **"▶️ Use"**
4. System loads specs into "New Inspection" tab
5. Fill in PR Number and Serial Number
6. Continue with hardware detection

**Method 2: Quick Load Button**

1. Stay on **"New Inspection"** tab
2. Click **"📋 Load from Template"** at the top
3. Select template from list
4. Specs are loaded instantly

### Managing Templates

- **✏️ Edit**: Modify template specifications
- **🗑️ Delete**: Remove template (with confirmation)
- **▶️ Use**: Load template into new inspection

---

## How to Use Pending Inspections

### Creating Pending Inspections

1. Go to **"⏳ Pending Inspections"** tab
2. Click **"➕ New Pending Inspection"**
3. **Optional**: Select a template to auto-fill specs
4. Fill in:
   - **Agency Name** (required)
   - **PR Number** (required)
   - **Laptop Model** (optional - can fill later)
   - **Serial Number** (optional - can fill later)
   - **Required Specs** (CPU, RAM, Storage - required)
5. Click **OK** to save

**💡 Tip**: Create multiple pending inspections at once for batch work!

### Starting a Pending Inspection

**Method 1: From Pending Tab**

1. Go to **"⏳ Pending Inspections"** tab
2. Find the inspection you want to work on
3. Click **"▶️ Start"**
4. System loads all data into "New Inspection" tab
5. Continue with:
   - Fill/verify Serial Number
   - Auto-Detect Hardware
   - Physical Inspection
   - Validate & Save

**Method 2: Quick Load Button**

1. Stay on **"New Inspection"** tab
2. Click **"⏳ Load Pending Inspection"** at the top
3. Select from list of pending inspections
4. Data is loaded instantly

### Managing Pending Inspections

- **▶️ Start**: Begin the inspection (loads into inspection tab)
- **✏️ Edit**: Modify pending inspection details
- **🗑️ Delete**: Remove pending inspection

### Auto-Completion

When you save an inspection that was loaded from pending:

- ✅ Pending inspection automatically marked as "completed"
- ✅ Removed from pending list
- ✅ Saved to inspection history

---

## Typical Workflows

### Workflow 1: Using Templates for Quick Inspections

```
1. Create template once: "Standard Office Laptop 2025"
   - CPU: Intel Core i5
   - RAM: 8GB
   - Storage: 256GB SSD

2. For each new laptop inspection:
   a. Load template (2 seconds)
   b. Enter PR # and Serial #
   c. Auto-detect hardware
   d. Validate & save
```

**Time Saved**: ~30 seconds per inspection (no retyping specs)

### Workflow 2: Batch Inspection with Pending Queue

```
Day 1 - Office Preparation:
1. Receive notification: 15 laptops arriving tomorrow
2. Create 15 pending inspections:
   - PR #12345 - Agency A - i5/8GB/256GB
   - PR #12346 - Agency A - i5/8GB/256GB
   - PR #12347 - Agency B - i7/16GB/512GB
   ... (15 total)

Day 2 - Field Inspection:
For each laptop:
1. Load next pending inspection
2. Enter/verify serial number
3. Auto-detect hardware
4. Physical assessment
5. Validate & save
6. Repeat for next laptop

Result: All data pre-entered, just execute inspections!
```

**Time Saved**: ~2-3 minutes per inspection (all data pre-entered)

### Workflow 3: Mixed Approach

```
1. Create templates for common configurations:
   - "Standard Office" (i5/8GB/256GB)
   - "Power User" (i7/16GB/512GB)
   - "Basic" (i3/4GB/128GB)

2. When inspections are scheduled:
   - Use template to create pending inspections
   - Modify as needed for specific PR requirements

3. During inspection:
   - Load pending one by one
   - Complete quickly with all data ready
```

---

## Best Practices

### For Templates

✅ **DO:**

- Create templates for frequently used configurations
- Use descriptive names (e.g., "2025 Standard Office Laptop")
- Include agency name if always the same
- Update templates when specs change

❌ **DON'T:**

- Create templates for one-time specs
- Use vague names like "Template 1"
- Duplicate templates unnecessarily

### For Pending Inspections

✅ **DO:**

- Create pending inspections when you know laptops are coming
- Fill in as much info as possible in advance
- Use templates to speed up creation
- Review pending list before going to inspect

❌ **DON'T:**

- Leave pending inspections unfinished for months
- Create pending for "maybe" inspections
- Forget to delete cancelled inspections

---

## Quick Reference

### From New Inspection Tab

| Button                         | Action                          |
| ------------------------------ | ------------------------------- |
| **⏳ Load Pending Inspection** | Quick select from pending queue |
| **📋 Load from Template**      | Quick load template specs       |

### PR Templates Tab

| Button              | Purpose                       |
| ------------------- | ----------------------------- |
| **➕ New Template** | Create new reusable template  |
| **▶️ Use**          | Load template into inspection |
| **✏️ Edit**         | Modify template               |
| **🗑️ Delete**       | Remove template               |

### Pending Inspections Tab

| Button                        | Purpose                       |
| ----------------------------- | ----------------------------- |
| **➕ New Pending Inspection** | Create new pending job        |
| **▶️ Start**                  | Begin inspection (loads data) |
| **✏️ Edit**                   | Modify pending details        |
| **🗑️ Delete**                 | Remove pending inspection     |

---

## Keyboard Shortcuts

- **Enter**: Confirm dialogs
- **Escape**: Cancel dialogs
- **Tab**: Navigate between fields

---

## Troubleshooting

### "No templates found"

- Go to PR Templates tab and create your first template
- Click "New Template" and fill in the specs

### "No pending inspections"

- Go to Pending Inspections tab
- Click "New Pending Inspection" to create one

### Pending inspection doesn't disappear after saving

- Make sure you loaded it using "Start" or "Load Pending"
- System tracks which pending inspection is being worked on
- Only marked complete when actually saved

### Can't edit template

- Template might be in use
- Try again or create a new one

---

## Statistics

The Pending Inspections tab shows:

- **Total Pending**: Number of inspections waiting to be completed
- Updates in real-time as you complete inspections

---

## Tips for Maximum Efficiency

1. **Start of Week**: Create all pending inspections for the week
2. **Use Templates**: Don't retype common specs
3. **Sequential Processing**: Load pending → complete → next
4. **Review Before Field**: Check pending list before leaving office
5. **Clean Up**: Delete or edit cancelled inspections

---

## Example Scenario

**Scenario**: COA will inspect 20 laptops from 3 agencies tomorrow.

**Setup (15 minutes in office):**

1. Create 3 templates:

   - "Agency A - Standard" (i5/8GB/256GB)
   - "Agency B - Standard" (i5/8GB/256GB)
   - "Agency C - Power" (i7/16GB/512GB)

2. Create 20 pending inspections:
   - 10 for Agency A (load template A)
   - 5 for Agency B (load template B)
   - 5 for Agency C (load template C)
   - Fill in PR numbers for each

**Field Work (60 minutes):**

- For each laptop:
  1. Click "Load Pending" (5 sec)
  2. Enter serial number (10 sec)
  3. Auto-detect (30 sec)
  4. Physical check (60 sec)
  5. Validate & Save (10 sec)
- Total: ~2 minutes per laptop
- 20 laptops = 40 minutes + 20 minutes buffer

**Result**: Organized, fast, zero errors in PR specs!

---

## Version Information

Feature added in: **v2.6**
Compatible with: **All existing databases**
New database tables:

- `pr_templates`
- `pending_inspections`

---

**Need Help?** Check the main README.md or About dialog for more information.
