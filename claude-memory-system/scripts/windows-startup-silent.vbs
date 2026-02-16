' ============================================
' Claude Memory System - Silent Startup
' ============================================
' Runs the Windows startup script silently (no window)

Set WshShell = CreateObject("WScript.Shell")

' Get user profile path
userProfile = WshShell.ExpandEnvironmentStrings("%USERPROFILE%")
batFile = userProfile & "\.claude\memory\windows-startup.bat"

' Run batch file hidden (window style 0 = hidden)
WshShell.Run """" & batFile & """", 0, False

Set WshShell = Nothing
