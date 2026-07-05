' run_silent.vbs
' Runs the Discord bot silently (no console window).
' Called by the Startup shortcut created by install_startup.vbs

Dim shell, botPath, cmd

Set shell = CreateObject("WScript.Shell")

' Get the folder where this script is located
botPath = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)

' Run the bot hidden (0 = hide window)
cmd = "cmd /c cd /d """ & botPath & """ && python main.py"
shell.Run cmd, 0, False