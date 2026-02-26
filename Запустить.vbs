Dim WshShell, fso, dir
Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
dir = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = dir
WshShell.Run "pythonw.exe main.py", 0, False
Set WshShell = Nothing
Set fso = Nothing
