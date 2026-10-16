"""P54-V6: Deep dive on Wind Excel add-in availability"""
import win32com.client as wc
import time
import os

print("=" * 60)
print("DSHA-P54 V6: Deep Dive - Wind Excel Add-in")
print("=" * 60)

# Step 1: Check if WDF can be loaded manually via VBA-like approach
print("\n--- Step 1: Attempting to load WDF via Excel COM ---")
excel = wc.Dispatch('Excel.Application')
excel.Visible = True
time.sleep(2)

# Check if Add-in can be manually enabled
print(f"\nLoaded add-ins: {excel.AddIns.Count}")
for i in range(1, excel.AddIns.Count + 1):
    try:
        ai = excel.AddIns.Item(i)
        print(f"  [{i}] {ai.Name}")
    except:
        pass

# Try to enable WDF.Addin through Excel's COM interface
print("\n--- Attempting to enable WDF.Addin ---")
try:
    # Try finding it in the registry-based add-ins
    for i in range(1, excel.AddIns.Count + 1):
        ai = excel.AddIns.Item(i)
        if 'WDF' in str(ai.Name).upper() or 'WIND' in str(ai.Name).upper():
            print(f"  Found WDF add-in at index {i}: {ai.Name}")
            # Try to enable it
            try:
                ai.OnLoad()
                print(f"  OnLoad() succeeded!")
            except Exception as e:
                print(f"  OnLoad() failed: {e}")
except Exception as e:
    print(f"  Error searching add-ins: {e}")

# Step 2: Try to use the WindExcel add-in through VBA automation
print("\n--- Step 2: Trying VBA to load Wind add-in ---")
try:
    excel.Application.Run('ActivateWind')
    print("  VBA ActivateWind succeeded")
except:
    print("  VBA ActivateWind not available")

# Try a basic WSD formula - if add-in loaded, this should work
print("\n--- Step 3: Testing WSD/WSS formulas ---")
wb = excel.Workbooks.Add()
ws = wb.ActiveSheet

# First check if Excel even knows about these functions
# In Excel, unknown functions return #NAME?
ws.Range('A1').Formula = '=WSS("CU.SHF","close")'
ws.Calculate()
time.sleep(2)
val_a1 = ws.Range('A1').Value
print(f"  A1 (WSS): {repr(val_a1)}")

ws.Range('A2').Formula = '=WSD("CU.SHF","close","2025-01-01","2025-01-02")'
ws.Calculate()
time.sleep(2)
val_a2 = ws.Range('A2').Value
print(f"  A2 (WSD): {repr(val_a2)}")

# #NAME? error code is -2146826259 in COM
if val_a1 == -2146826259:
    print("  >>> #NAME? - Wind functions NOT registered")
if val_a2 == -2146826259:
    print("  >>> #NAME? - Wind functions NOT registered")

# Check error value
print(f"\n  A1 Error: {ws.Range('A1').ErrorValue if ws.Range('A1').ErrorValue else 'N/A'}")
print(f"  A1 Value2: {ws.Range('A1').Value2}")

# Step 4: Try to use xlwings for a different approach
print("\n--- Step 4: Trying xlwings ---")
try:
    import xlwings as xw
    print("  xlwings imported OK")
    # Try to access the Excel app through xlwings
    app = xw.active_book()
    print(f"  xlwings active book: {app}")
except Exception as e:
    print(f"  xlwings failed: {e}")

# Step 5: Check if Wind terminal has any data export features
print("\n--- Step 5: Checking Wind terminal data export ---")
try:
    import subprocess
    # Check if Wind terminal can be queried
    result = subprocess.run(['powershell', '-Command', 
        'Get-Process wmain | Select-Object Id, MainWindowTitle, MainWindowHandle'],
        capture_output=True, text=True, timeout=10)
    print(f"  wmain info: {result.stdout.strip()}")
except Exception as e:
    print(f"  Cannot query wmain: {e}")

# Step 6: Check .wind directory state
print("\n--- Step 6: .wind directory state ---")
wind_dir = os.path.expanduser('~/.wind')
if os.path.exists(wind_dir):
    for root, dirs, files in os.walk(wind_dir):
        level = root.replace(wind_dir, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f'{indent}{os.path.basename(root)}/')
        subindent = ' ' * 2 * (level + 1)
        for f in files:
            print(f'{subindent}{f}')
else:
    print(f"  {wind_dir} does not exist")

# Step 7: Check if windlocal.exe can be started
print("\n--- Step 7: windlocal.exe status ---")
try:
    import subprocess
    result = subprocess.run(['powershell', '-Command', 
        'Get-Process windlocal -ErrorAction SilentlyContinue | Select-Object Id, ProcessName'],
        capture_output=True, text=True, timeout=10)
    print(f"  windlocal: {result.stdout.strip() if result.stdout.strip() else 'NOT RUNNING'}")
except Exception as e:
    print(f"  Error: {e}")

# Clean up
print("\n--- Cleanup ---")
wb.Close(SaveChanges=False)
excel.Quit()
print("Done")
print("=" * 60)
