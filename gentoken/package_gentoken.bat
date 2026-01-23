@echo off
cd /d "%~dp0"
echo ==========================================
echo Starting Build Process for GenToken GUI
echo ==========================================

echo.
echo 1. Cleaning up previous build artifacts...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

echo.
echo 2. Running PyInstaller with Spec File...
python -m PyInstaller --noconfirm --distpath "dist" --workpath "build" "gentoken.spec"

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] PyInstaller failed!
    pause
    exit /b 1
)

echo.
echo 3. Copying required pkg file...
if exist "build\gentoken\gentoken.pkg" (
    copy "build\gentoken\gentoken.pkg" "dist\gentoken.pkg"
    echo [OK] Pkg file copied.
) else (
    echo [WARNING] gentoken.pkg not found in build directory.
)

echo.
echo ==========================================
echo Build Complete!
echo Output directory: %~dp0dist
echo ==========================================
pause
