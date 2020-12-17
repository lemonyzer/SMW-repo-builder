# This is a sample Python script.
import datetime
import platform
import time
import operator
from email.utils import formatdate
from html import escape

from project import Project
import os
from pathlib import Path
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
    return False


def loadDirectoryList(systemPath):
    # iterates (recursive) trough all files and folders in systemPath and built projectsList
    # difference between path.absolut() path.resolve()  https://discuss.python.org/t/pathlib-absolute-vs-resolve/2573
    #                                                   https://stackoverflow.com/questions/42513056/how-to-get-absolute-path-of-a-pathlib-path-object
    # print("{:<30} {}".format(systemPath, "... loading ..."))
    pathEntries = Path(systemPath)
    print("{:<30} {}".format(str(pathEntries.resolve()), "... loading ..."))

    projectList = list()

    for entry in pathEntries.iterdir():
        if entry.is_dir():
            print("{:<30}: {} {}".format(str(pathEntries.resolve()), "directory", entry.name))
            loadDirectoryList(str(entry.resolve()))

            ''' recursive function
            ### this part is not needed
            subPathEntries = Path(str(entry.resolve()))
            print("test ...")
            print(subPathEntries)
            for subPath in subPathEntries.iterdir():
                #print("{:<30}: {} {}".format(str(pathEntries.resolve()), "directory", entry.name))
                print("subPath: (should not occure) - " + str(subPath))
            '''

        if entry.is_file():
            print("{:<30}: {} {}".format(str(pathEntries.resolve()), "file", entry.name))
            project = readProjectDetailsFromSystemPath(str(entry.resolve()))
            projectList.append(project)

    return projectList


def readProjectDetailsFromSystemPath(fileSystemPath):
    filePath = Path(fileSystemPath)
    # print("read project details from " + str(filePath))
    # projTimestamp = getTimestampFromFilename(entry)
    projTimestamp = getTimestampFromFilesystem(str(filePath.resolve()))
    projName = getProjectNameFromFilename(filePath.name)
    projInfo = getProjectAdditionalInfoFromFilename(filePath.name)
    projSystemPath = str(filePath.resolve())
    currentProject = Project(projTimestamp, projName, projInfo, projSystemPath, filePath.name)

    readRarSpecificDetailsFromSystemPath(currentProject)
    return currentProject


def readRarSpecificDetailsFromSystemPath(project):

    if rarfile.is_rarfile(project.systemFilePath):
        project.israrfile = True
        rar = rarfile.RarFile(project.systemFilePath)
        rootelements = rootElements(rar.namelist())
        project.setRootElements(rootelements)
        rootFolderInRARArchive = rar.namelist()[0].split("\\")[0]       # TODO wrong! could exist more than on root Element -> use rootelements instead!
        project.rarRootFolder = rootFolderInRARArchive
        #rootFolders.append(rootFolderInRARArchive)
    else:
        project.israrfile = False

    return


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

    # List all subdirectories using os.listdir
    basepath = systemPath
    for entry in os.listdir(basepath):
        if os.path.isdir(os.path.join(basepath, entry)):
            print("Checking subdirectory {}...".format(os.path.join(basepath, entry)))

            subdirectory = os.path.join(basepath, entry)
            subentries = os.listdir(subdirectory)
            for subentry in subentries:
                if isDirectoryEntryRelevant(subentry):
                    # projTimestamp = getTimestampFromFilename(entry)

                    projTimestamp = getTimestampFromFilesystem(os.path.join(subdirectory, subentry))
                    projName = getProjectNameFromFilename(entry)
                    projInfo = getProjectAdditionalInfoFromFilename(subentry)
                    projSystemPath = os.path.join(subdirectory, subentry)
                    currentProject = Project(projTimestamp, projName, projInfo, projSystemPath, subentry)
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
    #123456789012345
    #SuperMarioWars 2014
    #SuperMarioWars_2014
    if len(fileName) > 15:
        splitChar = ""
        if fileName[14] == " ":
            splitChar = fileName[14]
        elif fileName[14] == "_":
            splitChar = fileName[14]

        data = fileName.split(splitChar, 1)
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


def printProjects(list):
    for p in list:
        timestamp = p.timestamp
        local_time = time.ctime(timestamp)
        rfc2822 = formatdate(timestamp, True)
        print("{:<18} - {} - {} - {}".format(timestamp, rfc2822, local_time, p.fileName))


def gitInitRepo():
    gitCommand("git init")
    sysCommand("copy .gitignore")
    gitCommand("git add - a")
    gitCommand("git commit")


def gitCommand(cmd):
    print(cmd)


def sysCommand(cmd):
    print(cmd)


def removeAllProjectFilesFromRepo(repoSystemPath):
    # keep
    #.git/
    #.gitignore
    sysCommand("rm {} -r -e:.git .gitignore".format(repoSystemPath))


def compare_intersect(x, y):
    return frozenset(x).intersection(y)


def isRarRootFolderRepoFolder(project):
    # if RootElement is on of the string in valid array, it is the repo Folder and we need to cd "change direction" on path deeper
    valid = ["SuperMarioWars", "SuperMarioWars_UnityNetwork", "SuperMarioWars 2015.04.08_1_Changes", "SuperMarioWars_clean"]

    # https://stackoverflow.com/questions/1388818/how-can-i-compare-two-lists-in-python-and-return-matches
    intersectResult = compare_intersect(project.getRootElements(), valid)

    print(intersectResult)
    if len(intersectResult) >= 1:
        return True
    else:
        return False


def systemPathExists(systemPath):
    sysCommand(systemPath + "exists? {}".format(os.path.isdir(systemPath)))
    #return os.path.isdir(os.path.join(basepath, entry))
    return os.path.isdir(systemPath)


def gitRepoExists(systemPath):
    # Option A:
    gitCommand("git status")
    # TODO: check if repo exists
    a = False
    b = False
    if "git status == ....":
        a = True
    else:
        a = False

    # Option B:
    b = systemPathExists(systemPath + "\\.git")

    return a


def extractProject(proj, extractTargetSystemPath):
    #rarf = rarfile.RarFile(projectFilePath)
    #rarf.extractall(systemPathRepo)
    sysCommand("rarf.extractall({})".format(extractTargetSystemPath))


def workflow(projectList, extractTargetSystemPath, repoSystemPath):

    # https://lemonyzed.atlassian.net/wiki/spaces/SE/pages/105545805/git

    if not systemPathExists(extractTargetSystemPath):
        sysCommand("create dir " + extractTargetSystemPath)

    if not gitRepoExists(repoSystemPath):
        gitInitRepo(repoSystemPath)

    if systemPathExists(extractTargetSystemPath) and gitRepoExists(repoSystemPath):
        print("Starting with workflow of {} projects...".format(len(projectList)))
        i = 0
        for p in projectList:
            i=i+1
            print()
            print(" {:<3}/{:<3} ... {:<50} ... extracting".format(i, len(projectList), p.fileName))

            ## clean up
            removeAllProjectFilesFromRepo(repoSystemPath)  # delete previous project files

            extractProject(p, extractTargetSystemPath)  # /projects/<rar-filename>/
            ## extractTargetSystemPath
            ##  |
            ##  |-<rar filename of Project 0>
            ##  |    |
            ##  |    |-<rarRootFolder>
            ##  |
            ##  |-<rar filename of Project 1>
            ##  |     |
            ##  |     |-<rarRootFolder>
            ##

            ## A) if only one folder and NO files exists in root of extracted project
            ## if rarRootFolder exists
            ##
            ## B) if root folder name == ...
            ## if rarRootFolder
            ##      == valid = ["SuperMarioWars", "SuperMarioWars_UnityNetwork", "SuperMarioWars 2015.04.08_1_Changes", "SuperMarioWars_clean"]
            ##
            ## C) [DYNAMIC] search for Assets folder
            ## if folder "Assets" exists in current dir
            #########
            #### 0 cd rarRootFolder
            #### 1 search for folder ".\Assets"
            #### 2 if "Assets" found stop cd, use cd as base dir
            #### 3 if "Assets" not found, search recursive
            #### 4 for dir in dirlist cd dir and step 1
            #########
##
            ## simple
            # cd rarRootFolder
            # if dirList.len() === 1:
            #   if dirList[0] === "Assets" || dirList[0] === "Maps" || dirList[0] === "MapRawCreationWithoutValidTilesetToLokalTranslation" || dirList[0] === "27.09. Umzug Patrick Miriam"
            #      -> use cd, move all files to repo
            #   else:
            #      cd subdir
            #      -> use subdir, move all files to repo
            #
            # else:     # mehr als ein Unter Ordner in RAR-Archiv
            #   print("cd hat mehr als ein Ordner")
            #   use cd, move all files to repo
            #
##

            ## if rarRootFolder
            #analyseExtractedFolder(p, extractTargetSystemPath)

            # normal:
            # cd rarRootFolder
            # rarRootFolder\* -> repo\*
            # move all files inside rootFolder to repoFolder

            sysCommand("cd to extracted project folder")

            if isRarRootFolderRepoFolder(p):
                sysCommand("cd to extracted project folder sub directory")
                sysCommand("move all files in cd .\\* to repo folder")
            else:
                sysCommand("move all files in cd .\\* to repo folder")

            gitCommand("git add .")
            fileSystemTimestamp = datetime.datetime.fromtimestamp(p.timestamp).isoformat()
            commitTitle = "{}".format(p.fileName)  # TODO escape character, convert LF and RETURN to html code?
            commitBody = escape(p.longDescription())    # TODO escape character, convert LF and RETURN to html code?
            # argument: --date = "Sat Nov 14 14:00 2015 +0100"
            gitCommand("git commit -m '{}' -m '{}' --date='{}' ".format(commitTitle, commitBody, fileSystemTimestamp))


def rootElements(list):
    # analyze the rarfile.filenames() list to find all root elements
    rootelements = set()
    for item in list:
        rootelements.add(item.split("\\")[0])
    return rootelements


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

    #systemPath = "D:\\_delete\\SuperMarioWars"
    systemPath = "D:\\_delete\\test"
#    systemPath = "D:\\_temp"
#    systemPath = "Z:\\e_projekte\\Unity\\SuperMarioWars"
#    systemPath = "Z:\\e_projekte\\Unity\\SuperMarioWars\\_MapCreation"
#    systemPath = "Z:\\e_projekte\\Unity\\SuperMarioWars\\_MapCreationResume"
#    systemPath = "Z:\\e_projekte\\Unity\\SuperMarioWars\\SuperMarioWars 2014.08.06 PhotonUnityNetwork - Authorative Movement - Movement with Networked Rigidbody2D"
#    systemPath = "Z:\\e_projekte\\Unity\\SuperMarioWars\\SuperMarioWars 2014.08.19 PhotonUnityNetwork - Authorative Movement - Movement without Unity Physics - New InputScript"

    prokectsnew = loadDirectoryList(systemPath)
    printProjects(prokectsnew)
    exit()
    workWithFilelist(systemPath)

    # showFiles()
    # showProjects()
    # print(files[1])  # SuperMarioWars 2014.06.05 UnityNetwork.rar

    systemPathRepo = "D:\\_temp_dev"
    extractTargetSystemPath = "D:\\_delete\\extract"

    printRarDetails = False

    rootFolders = list()
    for p in projects:
        if rarfile.is_rarfile(p.systemFilePath):
            p.israrfile = True
            rar = rarfile.RarFile(p.systemFilePath)
            #print(rar.namelist())
            print("{:<30}: {}".format("p.fileName", p.fileName))
            if printRarDetails:
                print("{:<30}: {}".format("rar.namelist()", ""))
                for file in rar.namelist():
                    if not "Assets" in file:
                        if not "Library" in file:
                            print("{:<30}: {}".format("", file))

            #print(rar.printdir())
            rootelements = rootElements(rar.namelist())
            p.setRootElements(rootelements)
            print("{:<30}: {}".format("rootelements", len(p.getRootElements())))
            for el in p.getRootElements():
                print("{:<30}: {}".format("", el))

            rootFolderInRARArchive = rar.namelist()[0].split("\\")[0]

            print("{:<30}: {}".format("rar.namelist()[0]", rar.namelist()[0]))
            print("{:<30}: {}".format("rootFolderInRARArchive", rootFolderInRARArchive))
            #test = rarfile.RarInfo()
            if printRarDetails:
                print("{:<30}: {}".format("getinfo()", rootFolderInRARArchive))
                print("{:<30} {:<30}: {}".format("", "date_time", rar.getinfo(rootFolderInRARArchive).date_time))
                print("{:<30} {:<30}: {}".format("", "filename", rar.getinfo(rootFolderInRARArchive).filename))
                #print("{:<30} {:<30}: {}".format("", "compress_type", rar.getinfo(rootFolderInRARArchive).compress_type))
                print("{:<30} {:<30}: {}".format("", "comment", rar.getinfo(rootFolderInRARArchive).comment))
                print("{:<30} {:<30}: {}".format("", "create_system", rar.getinfo(rootFolderInRARArchive).create_system))
                print("{:<30} {:<30}: {}".format("", "extract_version", rar.getinfo(rootFolderInRARArchive).extract_version))
                print("{:<30} {:<30}: {}".format("", "flag_bits", rar.getinfo(rootFolderInRARArchive).flag_bits))
                print("{:<30} {:<30}: {}".format("", "CRC", rar.getinfo(rootFolderInRARArchive).CRC))
                print("{:<30} {:<30}: {}".format("", "rar.getinfo(rootFolderInRARArchive)", rar.getinfo(rootFolderInRARArchive)))
            #print(rar.infolist())
            print()
            p.rarRootFolder = rootFolderInRARArchive
            rootFolders.append(rootFolderInRARArchive)
        else:
            print(p.systemFilePath + " is not a RAR-File!")
            p.israrfile = False

    numOfRarFiles = 0
    for p in projects:
        if p.israrfile:
            numOfRarFiles = numOfRarFiles + 1

    #testProjectList = list()

    showProjects = False

    if showProjects:
        print("projects")
        printProjects(projects)

    #projects.sort(key=operator.attrgetter('timestamp'))    # inline sorting
    projectsSorted = sorted(projects, key=operator.attrgetter('timestamp'))  # sort copy

    if showProjects:
        print("projects Sorted")
        printProjects(projectsSorted)

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



    showRARArchiveRootFolder = True
    if showRARArchiveRootFolder:
        print("{:<30}: {}".format("numOfRarFiles", numOfRarFiles))
        print("RAR rootFolders")
        for item in set(rootFolders):
            print("\t{}".format(item))  # hide duplicates from list

        print("{:<130} {:<55} {}".format("file", "root folder", "amount of root Elements"))
        for p in projectsSorted:
            if len(p.rootElements) == 1:
                print("{:<130} {:<55} {}".format(p.fileName, p.rarRootFolder, len(p.rootElements)))
            elif len(p.rootElements) > 1:
                print("{:<130} {:<55} {}".format(p.fileName, "------------------------------------------------", len(p.rootElements)))
                for e in p.getRootElements():
                    print("{:<130} {:<55}".format("|---------------------------------------------------------------->", e))
            else:
                print("{:<130} {:<55} {}".format(p.fileName, ", ".join(p.getRootElements()), len(p.rootElements)))

    ## compare timestamps
    print()
    print("{:<12} {:<3} {:<12} {}".format("fileName", " ", "fileSystem", "p.fileName"))
    for p in projectsSorted:
        fileNameTimestamp = getTimestampFromFilename(p.fileName)
        # 2015.04.18

        # p.timestamp -> convert
        # CONVERT tutorial: https://timestamp.online/article/how-to-convert-timestamp-to-datetime-in-python
        ##fileSystemTimestamp = datetime.datetime.fromtimestamp(p.timestamp).isoformat()
        ## ISO Format
        ## 2020-12-04T10:54:42+01:00
        #dtts = datetime(p.timestamp)
        #https://www.programiz.com/python-programming/datetime (Example 5: Get date from a timestamp)
        timestamp = datetime.date.fromtimestamp(p.timestamp)
        fileSystemTimestamp = timestamp.strftime("%Y.%m.%d")

        compareresult = "NA"
        if fileNameTimestamp == fileSystemTimestamp:
            compareresult = "==="
        else:
            compareresult = "!!!"
        print("{:<12} {} {:<12} {}".format(fileNameTimestamp, compareresult, fileSystemTimestamp, p.fileName))

    ##
    ##  Workflow
    #       RAR Extraction
    #       File Moving
    #       git adding
    #       git commiting
    ##

    workflow(projects, extractTargetSystemPath, systemPathRepo)

    print("WorkFlow Part ....")
    fileName = files[1]
    print("{:<30}: {}".format("fileName", fileName))
    projectFilePath = systemPath + "\\" + fileName
    print("{:<30}: {}".format("projectFilePath", projectFilePath))
    if(rarfile.is_rarfile(projectFilePath)):
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
