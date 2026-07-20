@echo off
setlocal enabledelayedexpansion

rem Installs the Kitsu Houdini Plugin into Houdini's user preferences
rem folder(s).
rem
rem Usage: install_windows.cmd [custom user pref folder]
rem   Run with no arguments to auto-detect every "houdini<major>.<minor>"
rem   preferences folder under %USERPROFILE% (Houdini's default
rem   HOUDINI_USER_PREF_DIR) and install into all of them. Houdini keys
rem   this folder by major.minor version, so e.g. 20.5.550 and 20.5.684
rem   already share one folder ("houdini20.5") — only a different
rem   major.minor (e.g. 21.0) needs its own. If you use a custom
rem   HOUDINI_USER_PREF_DIR, pass that folder as an argument instead.

set "SCRIPT_DIR=%~dp0"
set "SOURCE_PLUGIN=%SCRIPT_DIR%kitsu_houdini_plugin"
set "SOURCE_PACKAGE=%SCRIPT_DIR%packages\kitsu_houdini_plugin.json"

if not exist "%SOURCE_PLUGIN%\python_panels\kitsu_houdini_plugin.pypanel" (
    echo ERROR: %SOURCE_PLUGIN% not found or incomplete.
    echo Run this script from the repository root, or check your checkout.
    exit /b 1
)

set "LISTFILE=%TEMP%\kitsu_houdini_plugin_install_targets.txt"
if exist "%LISTFILE%" del "%LISTFILE%"

if not "%~1"=="" (
    echo %~1>>"%LISTFILE%"
) else (
    for /d %%D in ("%USERPROFILE%\houdini*.*") do echo %%D>>"%LISTFILE%"
)

if not exist "%LISTFILE%" (
    echo ERROR: No "%USERPROFILE%\houdini<version>" folder found.
    echo Launch Houdini at least once to create it, then re-run this
    echo script — or pass your HOUDINI_USER_PREF_DIR as an argument.
    exit /b 1
)

for /f "usebackq delims=" %%T in ("%LISTFILE%") do (
    set "TARGET=%%T"
    echo Installing Kitsu Houdini Plugin
    echo   From: %SOURCE_PLUGIN%
    echo   To:   !TARGET!\kitsu_houdini_plugin
    echo.

    if not exist "!TARGET!\packages" mkdir "!TARGET!\packages"

    rem Remove any previous install of this plugin's own folder first, for
    rem a clean, idempotent install that never leaves stale files from an
    rem older version behind.
    if exist "!TARGET!\kitsu_houdini_plugin" rmdir /s /q "!TARGET!\kitsu_houdini_plugin"

    robocopy "%SOURCE_PLUGIN%" "!TARGET!\kitsu_houdini_plugin" /E /NFL /NDL /NJH /NJS >nul
    if errorlevel 8 (
        echo ERROR: Could not copy the plugin folder to !TARGET!.
    )

    copy /y "%SOURCE_PACKAGE%" "!TARGET!\packages\kitsu_houdini_plugin.json" >nul
    if errorlevel 1 (
        echo ERROR: Could not copy the package file to !TARGET!\packages.
    )
)

del "%LISTFILE%"

echo.
echo Done. Restart Houdini - the "Kitsu" shelf tool and Python Panel
echo interface should be available (also reachable via the "+" New Pane
echo Tab Type menu of any pane).
pause
endlocal
