' Open the workbook in Excel, recalculate it, and dump the cells that prove the
' native formulas work. Nothing is saved.
'
'   cscript //nologo tools\verify_workbook.vbs <workbook.xlsx> <output.txt>
Option Explicit

Dim excel, book, out, fso, sheet, values, r, c, errors, cells, name
Set fso = CreateObject("Scripting.FileSystemObject")
Set out = fso.CreateTextFile(WScript.Arguments(1), True)

Set excel = CreateObject("Excel.Application")
excel.Visible = False
excel.DisplayAlerts = False
Set book = excel.Workbooks.Open(WScript.Arguments(0), 0, True)
excel.CalculateFull

out.WriteLine "excel_version=" & excel.Version

For Each sheet In book.Worksheets
    values = sheet.UsedRange.Value
    errors = 0
    cells = 0
    If IsArray(values) Then
        For r = LBound(values, 1) To UBound(values, 1)
            For c = LBound(values, 2) To UBound(values, 2)
                If Not IsEmpty(values(r, c)) Then
                    cells = cells + 1
                    If VarType(values(r, c)) = vbError Then errors = errors + 1
                End If
            Next
        Next
    End If
    out.WriteLine "sheet=" & sheet.Name & "|cells=" & cells & "|errors=" & errors
Next

Sub Dump(sheetName, address)
    Dim area, cell
    Set area = book.Worksheets(sheetName).Range(address)
    For Each cell In area.Cells
        If VarType(cell.Value) = vbError Then
            out.WriteLine "cell=" & sheetName & "!" & cell.Address(False, False) & "|#ERROR"
        Else
            out.WriteLine "cell=" & sheetName & "!" & cell.Address(False, False) & "|" & CStr(cell.Value2)
        End If
    Next
End Sub

Dump "Parameters", "B4:B16"
Dump "OLS_Native_Formulas", "B6:G7"
Dump "OLS_Native_Formulas", "B15:K20"
Dump "OLS_Native_Formulas", "B33:D46"
Dump "Summary_Dashboard", "B5:I10"
Dump "Summary_Dashboard", "B24:B28"
Dump "Summary_Dashboard", "B31:B40"
Dump "Data_and_Residuals", "I2:Q4"

' A low-paid profile, so the floor and spillover branches of the calculator run.
With book.Worksheets("Summary_Dashboard")
    .Range("B24").Value = 2.5
    .Range("B25").Value = 3
    .Range("B26").Value = 0
    .Range("B27").Value = 0
End With
excel.Calculate
out.WriteLine "profile=low"
Dump "Summary_Dashboard", "B31:B40"

For Each name In book.Names
    out.WriteLine "name=" & name.Name & "|" & name.RefersTo
Next

book.Close False
excel.Quit
out.Close
