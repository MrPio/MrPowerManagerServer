Set oShell = CreateObject ("Wscript.Shell") 
Dim strArgs
strArgs = "cmd /c MrPowerManager.bat"
oShell.Run strArgs, 0, false