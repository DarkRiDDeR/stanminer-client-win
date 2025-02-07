@echo off

set scriptFolderPath=%~dp0
set cmd=".\start.ps1"

powershell -Command "Start-Process powershell \"-ExecutionPolicy Bypass -NoProfile -NoExit -Command `\"cd \`\"%scriptFolderPath%`\"; & \`\"%cmd%\`\"`\"\" -Verb RunAs"