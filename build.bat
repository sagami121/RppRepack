@echo off
setlocal

cd /d "%~dp0"

set "APP_NAME=RppRepack"
set "CLI_NAME=RppRepack-cli"
set "OUTPUT_DIR=nuitka_dist"
set "PACKAGE_DIR=%OUTPUT_DIR%\%APP_NAME%"
set "ICON_FILE=app_icon.ico"
set "NUITKA_CACHE_DIR=%CD%\.nuitka-cache"
if not exist "%NUITKA_CACHE_DIR%" mkdir "%NUITKA_CACHE_DIR%"

if not exist "main.py" (
  echo [ERROR] main.py not found.
  exit /b 1
)

if not exist "cli.py" (
  echo [ERROR] cli.py not found.
  exit /b 1
)

if not exist "assets" (
  echo [ERROR] assets directory not found.
  exit /b 1
)

echo [START] Build GUI: %APP_NAME%
@REM アイコンファイルがある場合のみアイコンを指定する判定
set "ICON_OPT="
if exist "%ICON_FILE%" (
    set "ICON_OPT=--windows-icon-from-ico="%ICON_FILE%""
)

python -m nuitka --standalone --disable-cache=all --assume-yes-for-downloads --enable-plugin=pyqt6 --windows-console-mode=disable %ICON_OPT% --output-dir="%OUTPUT_DIR%" --output-filename="%APP_NAME%.exe" --include-data-dir=assets=assets main.py

if errorlevel 1 (
  echo [ERROR] GUI Build failed.
  exit /b 1
)

echo [START] Build CLI: %CLI_NAME%
python -m nuitka --standalone --disable-cache=all --assume-yes-for-downloads --windows-console-mode=force %ICON_OPT% --output-dir="%OUTPUT_DIR%" --output-filename="%CLI_NAME%.exe" cli.py

if errorlevel 1 (
  echo [ERROR] CLI Build failed.
  exit /b 1
)

echo [DONE] Build completed

echo [START] Package output
if not exist "%PACKAGE_DIR%" mkdir "%PACKAGE_DIR%"

@REM main.dist の中身（GUIと依存関係）をパッケージディレクトリにコピー
xcopy /E /I /Y "%OUTPUT_DIR%\main.dist\*" "%PACKAGE_DIR%\" >nul
@REM cli.dist の中身（CLI）をパッケージディレクトリにコピー（共通のDLLは上書きされます）
xcopy /E /I /Y "%OUTPUT_DIR%\cli.dist\*" "%PACKAGE_DIR%\" >nul

if errorlevel 1 (
  echo [ERROR] Copy to package directory failed.
  exit /b 1
)

echo [DONE] Package output

echo.
echo Build completed: %PACKAGE_DIR%
echo (Includes %APP_NAME%.exe and %CLI_NAME%.exe)
echo.
pause
exit /b 0
