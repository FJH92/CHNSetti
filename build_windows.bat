@echo off
rem Build CHNSetti.exe on a Windows development computer (Python 3.10+ required here only).
rem Users who receive CHNSetti.exe do not need Python or any package.
cd /d "%~dp0"
py -m pip install --upgrade PySide6 openpyxl pyinstaller
if errorlevel 1 goto failed
py src\chnsetti.py --check-demo
if errorlevel 1 goto failed
py src\chnsetti.py --make-exe
if errorlevel 1 goto failed
echo.
echo CHNSetti.exe was created. See the message above for its location.
pause
exit /b 0
:failed
echo.
echo The build did not finish. Read the message above.
pause
exit /b 1
