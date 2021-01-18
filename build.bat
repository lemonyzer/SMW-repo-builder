@echo off

REM need pyvenv
py -m pip install pyvenv

REM prepare virtual python Environment
py -m venv venv

REM activate virtual environment
. /venv/Scripts/activate
start "" venv/Scripts/activate

REM (venv) install dev-tool pylint
python -m pip install -U pylint

REM (venv) install build-requirements
python -m pip install requests unrar gitpython jsonpickle pathvalidate deprecation
start "" /WAIT build-requirements.py
REM for sequencial bat files ...
REM start /wait cmd /c "file.bat"

set UNRAR_LIB_PATH="C:\Program Files (x86)\UnrarDLL\x64\UnRAR64.dll"
echo.
echo set environment variable (system variable)
echo UNRAR_LIB_PATH
echo 32bit: "C:\Program Files (x86)\UnrarDLL\UnRAR.dll"
echo 64bit: "C:\Program Files (x86)\UnrarDLL\x64\UnRAR64.dll"
REM start "" /WAIT sysdm.cpl
REM start runas /user:localhost\administrator cmd
REM start runas /user:localhost\administrator rundll32 sysdm.cpl,EditEnvironmentVariables
start "" /WAIT rundll32 sysdm.cpl,EditEnvironmentVariables
echo.
echo with admin privileges:
echo rundll32 sysdm.cpl,EditEnvironmentVariables
echo continue when UNRAR_LIB_PATH setted
pause

REM https://stackoverflow.com/questions/13257571/call-command-vs-start-with-wait-option
start "" /WAIT "cmd /k main.py"