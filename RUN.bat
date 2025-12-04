@echo off
REM Quick launcher for Antigravity Optimizer

echo ========================================
echo Antigravity Optimizer - Quick Launcher
echo ========================================
echo.

REM Check if venv exists
if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found!
    echo Please run: python -m venv .venv
    echo Then run: .venv\Scripts\pip install -r requirements_agent.txt
    pause
    exit /b 1
)

echo Select what to run:
echo.
echo 1. Greedy Scheduler (fast baseline)
echo 2. Ollama Agent Demo (AI-powered)
echo 3. Test Ollama Connection
echo 4. Validate Schedule
echo 5. Exit
echo.

set /p choice="Enter choice (1-5): "

if "%choice%"=="1" goto greedy
if "%choice%"=="2" goto demo
if "%choice%"=="3" goto test
if "%choice%"=="4" goto validate
if "%choice%"=="5" goto end

echo Invalid choice!
pause
exit /b 1

:greedy
echo.
echo Running Greedy Scheduler...
echo.
.venv\Scripts\python.exe src\engine\greedy_scheduler.py
echo.
echo Done! Check outputs\ folder for results.
pause
goto end

:demo
echo.
echo Running Ollama Agent Demo...
echo (This will take 10-30 seconds)
echo.
.venv\Scripts\python.exe demo_ollama_agent.py
echo.
pause
goto end

:test
echo.
echo Testing Ollama Connection...
echo.
.venv\Scripts\python.exe test_ollama.py
echo.
pause
goto end

:validate
echo.
echo Validating Schedule...
echo.
.venv\Scripts\python.exe src\engine\validator.py --schedule outputs\schedule.json --inputs inputs\
echo.
pause
goto end

:end
echo.
echo Goodbye!
