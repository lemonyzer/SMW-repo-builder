@echo off

py -m pip install requests
start /wait build-requirements.py
REM for sequencial bat files ...
REM start /wait cmd /c "file.bat"

REM https://stackoverflow.com/questions/13257571/call-command-vs-start-with-wait-option
start /wait main.py