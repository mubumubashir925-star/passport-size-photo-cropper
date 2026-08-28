@echo off
echo ============================================
echo Passport Photo Cropper - Mobile Capture
echo ============================================
echo.
echo This tool removes borders, table backgrounds, 
echo and white space from passport photos captured 
echo via mobile phone.
echo.

cd /d "%~dp0"

:: Run the Python script
python passport_cropper.py

pause