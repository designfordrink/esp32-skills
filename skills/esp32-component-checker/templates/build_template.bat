@echo off
REM ============================================================
REM ESP-IDF Build Template for Hermes (Windows + git-bash)
REM ============================================================
REM Использование:
REM   1. Скопировать в корень проекта
REM   2. Заменить PROJECT_NAME на имя проекта
REM   3. Запустить: cmd.exe //c "build.bat"
REM
REM Из Hermes:
REM   terminal(command='cmd.exe //c "C:\\path\\to\\build.bat"',
REM            background=True, notify_on_complete=True, timeout=600)
REM ============================================================

set MSYSTEM=

REM === Пути (настроить под свою среду) ===
set IDF_PATH=D:\esp\idf55
set IDF_TOOLS_PATH=C:\Users\valer\.espressif
set PROJECT_DIR=D:\ESP32\projects\PROJECT_NAME

set TOOLS_BASE=%IDF_TOOLS_PATH%\tools
set PYTHON_ENV=%IDF_TOOLS_PATH%\python_env\idf5.5_py3.14_env\Scripts
set CMAKE_BIN=%TOOLS_BASE%\cmake\3.30.2\bin
set NINJA_BIN=%TOOLS_BASE%\ninja\1.12.1
set TOOLCHAIN=%TOOLS_BASE%\xtensa-esp-elf\esp-14.2.0_20251107\xtensa-esp-elf\bin

set PATH=%PYTHON_ENV%;%CMAKE_BIN%;%NINJA_BIN%;%TOOLCHAIN%;%IDF_PATH%\tools;%PATH%

echo === ESP-IDF Build ===
echo IDF_PATH=%IDF_PATH%
echo Project: %PROJECT_DIR%
echo.

cd /d %PROJECT_DIR%

echo === Step 1: Checking dependencies ===
if exist main\idf_component.yml (
    type main\idf_component.yml
) else (
    echo No idf_component.yml — using legacy dependencies
)
echo.

echo === Step 2: Building ===
python %IDF_PATH%\tools\idf.py build
if %errorlevel% neq 0 (
    echo.
    echo ❌ BUILD FAILED
    echo Check: build\ log\idf_py_stderr_output_*.txt
    exit /b 1
)

echo.
echo ✅ BUILD SUCCESS
echo Binary: %PROJECT_DIR%\build\PROJECT_NAME.bin