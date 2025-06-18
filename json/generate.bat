@echo off
setlocal enabledelayedexpansion

set "listfile=listofjsonfiles.txt"

rem Delete old list file if it exists
if exist %listfile% del %listfile%

rem Count .json files
set count=0

for %%f in (*.json) do (
    echo "%%f" >> %listfile%
    set /a count+=1
)

if %count% equ 0 (
    echo ⚠️ No .json files found in this directory.
) else (
    echo ✅ %listfile% created with %count% JSON file(s):
    type %listfile%
)

pause
