# This is a sample Python script.
import platform
import time
import operator
from email.utils import formatdate

from project import Project
import os
from unrar import rarfile
# Press Umschalt+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Strg+F8 to toggle the breakpoint.

def isDirectoryEntryRelevant(entry):
    if entry[-4:].casefold() == ".rar":
        if len(entry) >= 10:
            return True

def workWithFilelist(systemPath):
    entries = os.listdir(systemPath)
    global files
    files = entries.copy()
    for entry in entries:
        if isDirectoryEntryRelevant(entry):
            # projTimestamp = getTimestampFromFilename(entry)
            projTimestamp = getTimestampFromFilesystem(systemPath + "\\" + entry)
            projName = getProjectNameFromFilename(entry)
            projInfo = getProjectAdditionalInfoFromFilename(entry)
            projSystemPath = systemPath + "\\" + entry
            currentProject = Project(projTimestamp, projName, projInfo, projSystemPath, entry)
            projects.append(currentProject)

    print("{:<30}: {}".format("numberOfFiles", len(entries)))
    print("{:<30}: {}".format("numberOfProjects", len(projects)))

def showFiles():
    for e in files:
        print(e)

def showProjects():
    for p in projects:
        print()
        p.say_state()
        print()

def getTimestampFromFilename(fileName):
    # split string with " ", 1 time => list with 2 itmes
    data = fileName.split(" ", 1)
    # timestamp format: 10 characters
    ## 123456789T
    ## 2014.08.08
    if len(data) > 1:
        return data[1][0:10]
    return "0000.00.00"

def modified_date(path_to_file):
    """
    Try to get the date that a file was created, falling back to when it was
    last modified if that isn't possible.
    See http://stackoverflow.com/a/39501288/1709587 for explanation.
    """
    if platform.system() == 'Windows':
        return os.path.getmtime(path_to_file)
    else:
        stat = os.stat(path_to_file)
        try:
            return stat.st_birthtime
        except AttributeError:
            # We're probably on Linux. No easy way to get creation dates here,
            # so we'll settle for when its content was last modified.
            return stat.st_mtime

def creation_date(path_to_file):
    """
    Try to get the date that a file was created, falling back to when it was
    last modified if that isn't possible.
    See http://stackoverflow.com/a/39501288/1709587 for explanation.
    """
    if platform.system() == 'Windows':
        return os.path.getctime(path_to_file)
    else:
        stat = os.stat(path_to_file)
        try:
            return stat.st_birthtime
        except AttributeError:
            # We're probably on Linux. No easy way to get creation dates here,
            # so we'll settle for when its content was last modified.
            return stat.st_mtime

def getTimestampFromFilesystem(fileName):
    return modified_date(fileName)
    #return creation_date(fileName)

def getProjectNameFromFilename(fileName):
    # split string with " ", 1 time => list with 2 itmes
    data = fileName.split(" ", 1)
    return data[0]

def getProjectAdditionalInfoFromFilename(fileName):
    # split string with " ", 1 time => list with 2 itmes
    data = fileName.split(" ", 1)
    if len(data) > 1:
        return data[1][10:]
    return ""

# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    # @echo off
    # rem get files (ordered)
    # rem extract date and commit details

    # rem (optional) cronical History
    # rem Option A: change system time
    # rem Option B: git parameter

    # rem integrate next commit
    # rem remove all project files from git repo
    # rem extract all project file to repo-folder
    # rem apply gitignore
    # rem approve all (file) changes
    # rem commit

    print_hi('PyCharm')

    projects = list()
    files = list()

    systemPath = "D:\\_delete\\SuperMarioWars"
#    systemPath = "D:\\_temp"
#    systemPath = "Z:\\e_projekte\\Unity\\SuperMarioWars"
#    systemPath = "Z:\\e_projekte\\Unity\\SuperMarioWars\\_MapCreation"
#    systemPath = "Z:\\e_projekte\\Unity\\SuperMarioWars\\_MapCreationResume"
#    systemPath = "Z:\\e_projekte\\Unity\\SuperMarioWars\\SuperMarioWars 2014.08.06 PhotonUnityNetwork - Authorative Movement - Movement with Networked Rigidbody2D"
#    systemPath = "Z:\\e_projekte\\Unity\\SuperMarioWars\\SuperMarioWars 2014.08.19 PhotonUnityNetwork - Authorative Movement - Movement without Unity Physics - New InputScript"

    workWithFilelist(systemPath)

    # showFiles()
    # showProjects()
    # print(files[1])  # SuperMarioWars 2014.06.05 UnityNetwork.rar

    systemPathRepo = "D:\\_temp_dev"

    rootFolders = list()
    for p in projects:
        if rarfile.is_rarfile(p.systemFilePath):
            p.israrfile = True
            rar = rarfile.RarFile(p.systemFilePath)
            rootFolderInRARArchive = rar.namelist()[0].split("\\")[0]
            p.rarRootFolder = rootFolderInRARArchive
            rootFolders.append(rootFolderInRARArchive)
        else:
            print(p.systemFilePath + " is not a RAR-File!")
            p.israrfile = False

    numOfRarFiles = 0
    for p in projects:
        if p.israrfile:
            numOfRarFiles = numOfRarFiles + 1

    if True:
        print("{:<30}: {}".format("numOfRarFiles", numOfRarFiles))
        print("rootFolders")
        print(set(rootFolders))  # hide duplicates from list

        print("{:<130} {:^9} ".format("file", "root folder"))
        for p in projects:
            print("{:<130} {:^9} ".format(p.fileName, p.rarRootFolder))


    #testProjectList = list()

    print("projects")
    for p in projects:
        timestamp = p.timestamp
        local_time = time.ctime(timestamp)
        rfc2822 = formatdate(timestamp, True)
        print("{:<18} - {} - {} - {}".format(timestamp, rfc2822, local_time, p.fileName))

    #projects.sort(key=operator.attrgetter('timestamp'))    # inline sorting
    projectsSorted = sorted(projects, key=operator.attrgetter('timestamp'))  # sort copy

    print("projects")
    for p in projectsSorted:
        timestamp = p.timestamp
        local_time = time.ctime(timestamp)
        print("{:<18} - {} - {} - {}".format(timestamp, rfc2822, local_time, p.fileName))

    print("compare projects lists")
    for i in range(len(projectsSorted)):
        p = projects[i].fileName
        ps = projectsSorted[i].fileName
        compareresult = "not tested"
        if p == ps:
            compareresult = "==="
        else:
            compareresult = "!!!"
        print("{:<130} {:<3} {:<130}".format(p, compareresult, ps))



    #print(rarfile.getinfo(testList[0]))

    fileName = files[1]
    projectFilePath = systemPath + "\\" + fileName
    rarf = rarfile.RarFile(projectFilePath)
    rootFolderInRARArchive = rarf.namelist()[0].split("\\")[0]
    print("")
    print("{:<30}: {}".format("rarFile", fileName))
    print("{:<30}: {}".format("rootFolderInRARArchive", rootFolderInRARArchive))

    if "rootFolderInRARArchive" == "rootFolderInRARArchive":  # == repoName
        # extract
        print("Extract {} ...".format(projectFilePath))
        # rarf.extractall(systemPathRepo)


#    destinationPath = systemPathRepo + "\\" + rarf.namelist()[0]
    #print(destinationPath)
    #print(rarf.infolist()[0])
    #print(rarf.printdir())

    #rarf.extractall()

    # print(rarf.namelist())
    # print(rarf.getinfo("SuperMarioWars\\Assets").date_time)
    # print(projects[1].timestamp)



# See PyCharm help at https://www.jetbrains.com/help/pycharm/
