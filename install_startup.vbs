' install_startup.vbs
' Adds the Discord bot to Windows startup (runs silently, no console window)
' Double-click this file once to install.

Dim shell, shortcut, startupPath, botPath

Set shell = CreateObject("WScript.Shell")

' Get the Startup folder path
startupPath = shell.SpecialFolders("Startup")

' Get the path to this script's folder (the bot folder)
botPath = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)

' Create a shortcut in the Startup folder
Set shortcut = shell.CreateShortcut(startupPath & "\DiscordRoleBot.lnk")

' Point to wscript.exe which runs VBS silently, and pass run.vbs as argument
shortcut.TargetPath = "wscript.exe"
shortcut.Arguments = """" & botPath & "\run_silent.vbs"""
shortcut.WorkingDirectory = botPath
shortcut.Description = "Discord Role Bot - Auto-starts on login"
shortcut.WindowStyle = 7  ' Minimized
shortcut.Save

MsgBox "Bot added to Windows Startup!" & vbCrLf & vbCrLf & _
       "It will start automatically next time you log in.", vbInformation, "Discord Role Bot"