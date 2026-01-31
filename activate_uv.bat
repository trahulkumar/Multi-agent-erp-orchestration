@echo off
if exist ".venv_uv\Scripts\activate.bat" (
    call .venv_uv\Scripts\activate.bat
    echo Virtual environment activated with uv (.venv_uv).
) else if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo Virtual environment activated with uv (.venv).
) else (
    echo Error: Virtual environment not found at .venv_uv\Scripts\activate.bat or .venv\Scripts\activate.bat
    echo Please ensure you have created the environment using 'uv venv'.
    exit /b 1
)
