@echo off
REM Donizo Truth Engine - Quick Start Script (Windows)

echo ======================================================================
echo   DONIZO TRUTH ENGINE - Quick Start
echo ======================================================================
echo.
echo This script will:
echo   1. Build the Docker image
echo   2. Start the interactive menu
echo.
echo No dependencies needed on your machine - everything runs in Docker!
echo.
echo ======================================================================
echo.

REM Create data directory if it doesn't exist
if not exist data mkdir data

echo Building Docker image (this may take a few minutes)...
docker build -t donizo-engine:latest .

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Build successful!
    echo.
    echo Starting interactive menu...
    echo ======================================================================
    echo.

    REM Run the container interactively
    docker run -it --rm -v "%cd%\data:/data" --name donizo-truth-engine donizo-engine:latest
) else (
    echo.
    echo Build failed! Please check the error messages above.
    exit /b 1
)
