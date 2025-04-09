@echo off

set PYTHONPATH= ..\Client

cd /d ..\Client

call venv\Scripts\activate

python -m src.application

pause