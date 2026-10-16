"""P54-V6: Excel + Wind plugin availability test"""
import win32com.client as wc
import time

print("=" * 60)
print("DSHA-P54 V6: Excel + Wind Plugin Availability Test")
print("=" * 60)

# Create new Excel instance
excel = wc.Dispatch('Excel.Application')
excel.Visible = True
time.sleep(3)

print(f"\nExcel reopened, version: {excel.Version}")
print(f"Caption: {excel.Caption}")
print(f"Windows: {excel.Windows.Count}")

# Check add-ins
print(f"\n=== Excel Add-ins ({excel.AddIns.Count}) ===")
for i in range(1, excel.AddIns.Count + 1):
    try:
        ai = excel.AddIns.Item(i)
        print(f"  [{i}] Name={ai.Name}")
    except Exception as e:
        print(f"  [{i}] ERROR: {e}")

# Check custom UI / ribbon tabs
print(f"\n=== Custom UI / Ribbon ===")
try:
    print(f"CustomUIs count: {excel.CustomUIs.Count}")
    for i in range(1, excel.CustomUIs.Count + 1):
        try:
            cu = excel.CustomUIs.Item(i)
            print(f"  [{i}] Name={cu.Name}")
        except:
            pass
except Exception as e:
    print(f"  CustomUIs not accessible: {e}")

# Check workbook functions
wb = excel.Workbooks.Add()
ws = wb.ActiveSheet

print(f"\n=== Testing Basic Excel Functions ===")
ws.Range('A1').Value = 'Test Data'
ws.Range('A2').Value = 12345
ws.Range('A3').Formula = '=1+1'
ws.Range('A3').Calculate()
print(f"A3 value: {ws.Range('A3').Value}")

# Try WSS function - this is a macro function from Wind add-in
print("\n=== Testing WSS Function ===")
try:
    ws.Range('A5').Formula = '=WSS("CU.SHF","close")'
    time.sleep(2)
    val = ws.Range('A5').Value
    print(f"WSS returned: {repr(val)}")
except Exception as e:
    print(f"WSS error: {e}")

# Try WSD function
print("\n=== Testing WSD Function ===")
try:
    ws.Range('A6').Formula = '=WSD("CU.SHF","close","2025-01-01","2025-01-02")'
    time.sleep(2)
    val = ws.Range('A6').Value
    print(f"WSD returned: {repr(val)}")
except Exception as e:
    print(f"WSD error: {e}")

# Try a simpler approach - use the WindExcel COM object if available
print("\n=== Testing WindExcel COM Object ===")
try:
    wdf = wc.Dispatch('WindExcel.WDF')
    print(f"WindExcel COM: OK ({wdf})")
except Exception as e:
    print(f"WindExcel COM: NOT AVAILABLE ({e})")

try:
    wdf = wc.Dispatch('WDF.DataFeed')
    print(f"WDF.DataFeed COM: OK ({wdf})")
except Exception as e:
    print(f"WDF.DataFeed COM: NOT AVAILABLE ({e})")

# Try checking the function count or available functions
print("\n=== Checking Wind function availability ===")
# In Excel, external/macro functions return #NAME? if not available
# Let's check what error codes we get
print("Checking for #NAME? error...")
ws.CalculateFull()
time.sleep(1)
print(f"A5 (WSS) value: {repr(ws.Range('A5').Value)}")
print(f"A6 (WSD) value: {repr(ws.Range('A6').Value)}")

# Clean up
wb.Close(SaveChanges=False)
excel.Quit()
print("\nExcel closed")
print("=" * 60)
