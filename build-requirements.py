
# py -m pip install requests
import requests # download
import os # execute
import subprocess # execute (wait for done)
url = 'http://www.rarlab.com/rar/UnRARDLL.exe'

myfile = requests.get(url)
unrardll_filename = "UnRARDLL.exe"
# current workingdir .... cwd 
# open('c:/users/LikeGeeks/downloads/PythonImage.png', 'wb').write(myfile.content)
open(unrardll_filename, 'wb').write(myfile.content)

# https://realpython.com/run-python-scripts/#:~:text=To%20run%20Python%20scripts%20with,python3%20hello.py%20Hello%20World!
# https://stackoverflow.com/questions/1811691/running-an-outside-program-executable-in-python


# start file (parallel)
# os.startfile(unrardll_filename)

# start file (sequential)
#subprocess.Popen(unrardll_filename) # doesnt wait
#subprocess.call(["start", unrardll_filename])  # old < python 3.5
subprocess.run([unrardll_filename])

# TODO Tutorial: https://stackoverflow.com/questions/55574212/how-to-set-path-to-unrar-library-in-python 
# TODO get extracted folder OR set extracted folder
# TODO cd to extracted folder 
# TODO NOT(copy UnRAR.dll or x64\UnRAR.dll to ???)
# TODO YES: 
# TODO  32bit OS: set UNRAR_LIB_PATH = C:\Program Files (x86)\UnrarDLL\UnRAR.dll
# TODO  64bit OS: set UNRAR_LIB_PATH = C:\Program Files (x86)\UnrarDLL\x64\UnRAR64.dll
#      