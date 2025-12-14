@echo off
REM AlgoQuant Backend - Hugging Face Deployment Script (Windows)
REM Run this script to quickly deploy your backend to Hugging Face Spaces

echo ========================================
echo 🚀 AlgoQuant Backend Deployment
echo ========================================
echo.

REM Check if huggingface-cli is installed
huggingface-cli --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Hugging Face CLI not found. Installing...
    pip install huggingface_hub
)

REM Login check
echo Checking Hugging Face authentication...
huggingface-cli whoami >nul 2>&1
if %errorlevel% neq 0 (
    echo Please login to Hugging Face:
    huggingface-cli login
)

echo ✅ Authenticated with Hugging Face
echo.

REM Get space name
set /p SPACE_NAME="Enter Space name (default: algoquant-backend): "
if "%SPACE_NAME%"=="" set SPACE_NAME=algoquant-backend

echo.
echo 📦 Creating Space: %SPACE_NAME%...
huggingface-cli repo create %SPACE_NAME% --type space --space_sdk docker

echo.
echo 📋 Next steps:
echo.
echo 1. Go to https://huggingface.co/spaces/YOUR_USERNAME/%SPACE_NAME%
echo 2. Click "Files" tab
echo 3. Upload these files from your backend directory:
echo    - main.py
echo    - database.py
echo    - models.py
echo    - strategy.py
echo    - strategy_handlers.py
echo    - simulated_exchange.py
echo    - simulated_trading.py
echo    - requirements.txt
echo    - Dockerfile
echo    - backend\README_HF.md (rename to README.md)
echo.
echo 4. Go to Settings tab and add secrets:
echo    - DATABASE_URL
echo    - SECRET_KEY
echo.
echo 5. Wait for build to complete (check Logs tab)
echo.
echo 6. Your API will be at: https://YOUR_USERNAME-%SPACE_NAME%.hf.space
echo.
echo ✨ Or use the Hugging Face web UI for easier upload!
echo.
pause
