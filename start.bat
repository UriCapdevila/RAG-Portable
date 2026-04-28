@echo off
setlocal

if not exist ".venv\Scripts\python.exe" (
    py -3 -m venv .venv
)

if exist "frontend\package.json" (
    npm.cmd --prefix frontend install
    npm.cmd --prefix frontend run build
)

py -3 -m pip --python .venv\Scripts\python.exe install -r requirements.txt
call .venv\Scripts\activate.bat
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
