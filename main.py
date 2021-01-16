# This is a sample Python script.
import datetime
import platform
import time
import operator
from email.utils import formatdate
from html import escape

from project import Project
from project import ProjectEncoder

import os
from pathlib import Path, PurePath
from unrar import rarfile
import shutil
from git import Repo, NoSuchPathError, InvalidGitRepositoryError

import json
import jsonpickle

from pathvalidate import sanitize_filename  # sanitize_filename()  #  py -m pip install pathvalidate

from app import App

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


def load_directory_list(system_path_rar_files):
    # iterates (recursive) through all files and folders in system_path_rar_files and built projectsList
    # difference between path.absolut() path.resolve()  https://discuss.python.org/t/pathlib-absolute-vs-resolve/2573
    #                                                   https://stackoverflow.com/questions/42513056/how-to-get-absolute-path-of-a-pathlib-path-object
    # print("{:<30} {}".format(system_path_rar_files, "... loading ..."))
    path_entries = Path(system_path_rar_files)
    print("{:<30} {}".format(str(path_entries), "... loading ..."))

    project_list = list()

    for entry in path_entries.iterdir():
        if entry.is_dir():
            print("{:<30}: {} {}".format(str(path_entries), "directory", entry.name))
            project_list.extend(load_directory_list(str(entry)))   # FIX: rekursive Funktion muss Zwischenergebnisse Speichern!!!

            ''' recursive function
            ### this part is not needed
            subPathEntries = Path(str(entry.resolve()))
            print("test ...")
            print(subPathEntries)
            for subPath in subPathEntries.iterdir():
                #print("{:<30}: {} {}".format(str(path_entries.resolve()), "directory", entry.name))
                print("subPath: (should not occure) - " + str(subPath))
            '''

        if entry.is_file():
            print("{:<30}: {} {}".format(str(path_entries), "file", entry.name))
            project = read_project_details_from_system_path(str(entry))
            project_list.append(project)

    return project_list


def read_project_details_from_system_path(fileSystemPath):
    filePath = Path(fileSystemPath)
    # print("read project details from " + str(filePath))
    # projTimestamp = getTimestampFromFilename(entry)
    projTimestamp = getTimestampFromFilesystem(str(filePath))
    projName = getProjectNameFromFilename(filePath.name)
    projInfo = getProjectAdditionalInfoFromFilename(filePath.name)
    projSystemPath = str(filePath)
    currentProject = Project(projTimestamp, projName, projInfo, projSystemPath, filePath.name)

    read_rar_specific_details_from_system_path(currentProject)
    return currentProject


def read_rar_specific_details_from_system_path(project):

    if rarfile.is_rarfile(project.systemFilePath):
        project.israrfile = True
        rar = rarfile.RarFile(project.systemFilePath)
        rootelements = root_elements(rar.namelist())
        project.setRootElements(rootelements)
        
        # FIX empty rar, rar without containing folder
        # TODO renaming rootFolderInRARArchive -> first root element
        if len(rar.namelist()) > 0: 
            first_element_names = rar.namelist()[0].split("\\")
            if len(first_element_names) > 0:
                rootFolderInRARArchive = first_element_names[0]         # TODO wrong! could exist more than one root Element -> use rootelements instead!
                                                                        # TODO wrong, could be less than one root elment (empty rar File)!
            else:
                rootFolderInRARArchive = None
        else:
            rootFolderInRARArchive = None

        project.rarRootFolder = rootFolderInRARArchive
        #rootFolders.append(rootFolderInRARArchive)
    else:
        project.israrfile = False
    print("{:<30}: {}".format(project.systemFilePath, "file" + (" RAR" if project.israrfile else " NOT RAR marked")))   # conditional expression
    
    return

# workWithFilelist()
# limitation: reads files max. 2 level deeper than system_path
# depricated! use load_directory_list - works recursively
def workWithFilelist(system_path_rar_files, project_list, file_list):

    entries = os.listdir(system_path_rar_files)
    # file_list.extend(entries)

    # all Files&Folders in root
    for entry in entries:
        #if os.path.isfile(os.path.join(system_path_rar_files, entry)):                                 # dublicates! don't remove twice!
        #    file_list.append(entry)
        print("Checking entry (Level 0) {}...".format(os.path.join(system_path_rar_files, entry)))
        if isDirectoryEntryRelevant(entry):
            # projTimestamp = getTimestampFromFilename(entry)
            projTimestamp = getTimestampFromFilesystem(system_path_rar_files + "\\" + entry)
            projName = getProjectNameFromFilename(entry)
            projInfo = getProjectAdditionalInfoFromFilename(entry)
            projSystemPath = system_path_rar_files + "\\" + entry
            currentProject = Project(projTimestamp, projName, projInfo, projSystemPath, entry)
            project_list.append(currentProject)
        else:
            print("... skipped ...")

    # all Files&Folders in subdirectories of root (direct subdirectories of root, 1 level deeper)
    # List all subdirectories using os.listdir
    basepath = system_path_rar_files
    for entry in os.listdir(basepath):
        if os.path.isfile(os.path.join(basepath, entry)):
            file_list.append(entry)
        # in this loop only files&folder in Level 1
        print("Checking entry (Level 1) {}...".format(os.path.join(basepath, entry)))
        if os.path.isdir(os.path.join(basepath, entry)):
            print("Checking subdirectory (Level 1) {}...".format(os.path.join(basepath, entry)))

            subdirectory = os.path.join(basepath, entry)
            subentries = os.listdir(subdirectory)
            # all Files&Folders in subdirectories of subdirectory (2 level deeper)
            for subentry in subentries:
                print("Checking subdirectory (Level 2) {}...".format(os.path.join(basepath, subentry)))
                if os.path.isfile(os.path.join(subdirectory, subentry)):
                    file_list.append(subentry)

                if isDirectoryEntryRelevant(subentry):
                    # projTimestamp = getTimestampFromFilename(entry)

                    projTimestamp = getTimestampFromFilesystem(os.path.join(subdirectory, subentry))
                    projName = getProjectNameFromFilename(entry)
                    projInfo = getProjectAdditionalInfoFromFilename(subentry)
                    projSystemPath = os.path.join(subdirectory, subentry)
                    currentProject = Project(projTimestamp, projName, projInfo, projSystemPath, subentry)
                    project_list.append(currentProject)
                else:
                    print("... skipped ...")
        else:
            print("... skipped ...")

    print("{:<30}: {}".format("number of files & folders (file_list)", len(file_list)))
    print("{:<30}: {}".format("number of projects (project_list)", len(project_list)))


def showFiles(file_list):
    print("showFiles()...")
    for e in file_list:
        print(f'- {e}')


def showProjects(project_list):
    for p in project_list:
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

        # BUG can't splitt with empty separator!
        # FIX
        if splitChar == "":
            data = fileName
        else:
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
    print("{:<18} - {:<31} - {:<24} - {:<120} - {}".format("timestamp", "rfc2822", "local_time", "fileName", "numOf rootElements"))
    for p in list:
        timestamp = p.timestamp
        local_time = time.ctime(timestamp)
        rfc2822 = formatdate(timestamp, True)
        p.rfc2822 = rfc2822
        print("{:<18} - {} - {} - {:<120} - {}".format(timestamp, rfc2822, local_time, p.fileName, len(p.rootElements)))


def gitInitRepo(repoSystemPath):
    repo = Repo.init(repoSystemPath)

    gitCommand("git init")
    sysCommand("copy .gitignore")   #  TODO .gitignore
    src = os.getcwd() + "\\Unity.gitignore"
    dst = repoSystemPath + "\\.gitignore"
    shutil.copy(src, dst)

    gitCommand("git add - a")
    gitCommand("git commit")

    return repo


def gitCommand(cmd):
    print(cmd)


def sysCommand(cmd):
    print(cmd)


def removeAllProjectFilesFromRepo(repoSystemPath):
    # keep
    #.git
    #.gitignore
    sysCommand("rm {} -r -e:.git .gitignore".format(repoSystemPath))

    exclusions = [".git", ".gitignore"]
    print(f'exclusions: {exclusions}')
    removeRecursive(repoSystemPath, exclusions)


def removeRecursive(repoSystemPath, exclusions):

    repo = Path(repoSystemPath)
    for entry in repo.iterdir():

        if entry.name in exclusions:
            # exclusion found, don't delete entry
            print(f'exclusions found {entry.name}')
            continue
        else:
            if entry.is_dir():
                # is_Directory
                removeRecursive(str(entry), exclusions)
                # print(f'{entry.name}.rmdir()')
                entry.rmdir()                                       # remove (empty) directory
            else:
                # is_File
                # print(f'{entry.name}.unlink(missing_ok=True)')
                entry.unlink(missing_ok=True)                       # remove file


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


def gitRepoExists(repoSystemPath):
    # Option B return repo ... return null if not exists
    # repo = any
    repoExists = False

    try:
        # Option B
        # repo = Repo(repoSystemPath)
        Repo(repoSystemPath)
        repoExists = True
    except NoSuchPathError as exc:
        print(exc)
    except InvalidGitRepositoryError as exc:
        print(exc)

    return repoExists


def extractProject(proj, extractTargetSystemPath):
    # extract rar-file to targetDir\rar-file-name\
    projectExtractPath = extractTargetSystemPath + "\\" + proj.fileName
    projectExtractPath = projectExtractPath[:-4]
    projectExtractPath = projectExtractPath.rstrip()  # FIX for rarfalies with space before extension "xyz .rar"
    proj.extractPath = projectExtractPath
    rarf = rarfile.RarFile(proj.systemFilePath)
    filteredMembers = filterUnescessaryFilesFromRar(proj, rarf)
    print("filteredMembers {} / {}".format(len(filteredMembers), len(rarf.namelist())))
    rarf.extractall(projectExtractPath, members=filteredMembers)
    sysCommand("extract {} ------> .... rarf.extractall .... {})".format(proj.systemFilePath, extractTargetSystemPath))


def maxLevel(checkLevel, arrayLength):
    if checkLevel == 0:
        return 0
    else:
        # can't filter checkLevel 1 (1 Level subdir) if array has only one element
        if arrayLength > 1:
            return 1
        else:
            return 0


def filterUnescessaryFilesFromRar(proj, rarFile):
    exclusions = ["Library", "Temp", "Obj", "Build", "Builds", "Logs", "User Settings", ".vs", ".gradle"]
    debug = False
    #for m in rarFile.namelist():
    #    print(f'{m}')

    checkLevel = 0

    if len(proj.getRootElements()) == 1:
        # single root element
        if "Assets" in proj.getRootElements():
            print("Assets is rootElement, no filtering explusions!!!")
            return rarFile.namelist()
        else:
            # other rootElement (propably <UnityProjectName>)
            checkLevel = 1
            pass
    elif len(proj.getRootElements()) > 1:
        # multiple root elements
        if "Assets" in proj.getRootElements():
            # Assets in rootElements found, filtering only in level 0
            checkLevel = 0
        else:
            # Assets NOT in rootElements found, filtering in level 1
            checkLevel = 1

    filteredmembers = list()
    excludedmembers = list()
    for member in rarFile.namelist():
        array = member.split("\\")

        basepathOfMember = member.split("\\")[maxLevel(checkLevel, len(array))]  # TODO fix/verify: Option 1 basedir extract with current filter, Option B second baseDir extract without filter. totalcommander to compare both base dir and delete similar files. check diff
        # print(basepathOfMember)
        if basepathOfMember in exclusions:
            if debug:
                print(f'excluded member: {member}')
            excludedmembers.append(member)
        else:
            filteredmembers.append(member)

    # for i in excludedmembers:
    #     print(f'excluded: {i}')

    return filteredmembers


def findProjectRepoLevel(projectExtractedPath):
    # TODO find repoLevel in extracted project structure
    projectExtractedPath = Path(projectExtractedPath)
    print("findProjectRepoLevel in " + str(projectExtractedPath))
    #print("findProjectRepoLevel in " + str(projectExtractedPath.resolve()))
    # print(f'{projectExtractedPath.name} - child elements: {len(projectExtractedPath.iterdir())}')
    #directoryList = os.listdir(projectExtractedPath.resolve())
    directoryList = os.listdir(projectExtractedPath)

    # if RootElement is on of the string in valid array, we are in the repo Folder
    baseIsFirstLevel = ["Assets"]

    # if RootElement is on of the string in baseIsSecondLevel array, it is the repo Folder and we need to cd "change direction" on path deeper
    baseIsSecondLevel = ["SuperMarioWars", "SuperMarioWars_UnityNetwork", "SuperMarioWars 2015.04.08_1_Changes", "SuperMarioWars_clean", "Changes SuperMarioWars 2015.04.07_5 to 2015.04.10_3"]

    # https://stackoverflow.com/questions/1388818/how-can-i-compare-two-lists-in-python-and-return-matches
    intersectResult = compare_intersect(directoryList, baseIsFirstLevel)

    print(intersectResult)
    if len(intersectResult) >= 1:
        return projectExtractedPath
    else:

        intersectResult = compare_intersect(directoryList, baseIsSecondLevel)
        print(intersectResult)
        if len(intersectResult) >= 1:
            for entry in projectExtractedPath.iterdir():
                # print(str(entry.name))
                if entry.name in intersectResult:
                    return entry

                #                                            # TODO double checking .... i'm to tired.
                #                                            # TODO list compares with list (intersection) schnittmenge
                #                                            # TODO if atleast one element intersects... go to folder that matches first # THIS IS NOT SOLID!
                # if entry in baseIsSecondLevel:
                #    return entry
            print("no matching found! " + str(intersectResult))
        else:
            return projectExtractedPath

    return projectExtractedPath
    # for entry in projectExtractedPath.iterdir():
    #
    #     if(entry.is_dir())
    #         findProjectRepoLevel(entry)
    #
    #     if
    #     pass


def wait_for_input(message):
    x = ""
    while x not in ["yes", "YES", "N", "n", "No"]:
        x = input(message)
        if x in ["N", "n", "No"]:
            exit()
        elif x in ["yes", "YES"]:
            break


def workflow(projectList, extractTargetSystemPath, repoSystemPath):
    # TODO implement extract and git workflow
    # https://lemonyzed.atlassian.net/wiki/spaces/SE/pages/105545805/git

    extractTargetRoot = Path(extractTargetSystemPath)
    # check if folder exists, if not try to create it
    if not extractTargetRoot.exists():
        try:
            extractTargetRoot.mkdir(parents=True)
        except FileExistsError as exc:
            print(exc)
            exit()

    # check if folder is folder, if not exit
    if not extractTargetRoot.is_dir():
        print("ERROR: {:<50} ... is not a folder and exists".format(str(extractTargetRoot.resolve())))
        exit()
    else:
        #print("{:<50} ... is folder and exists".format(str(extractTargetRoot.resolve())))
        print("{:<50} ... is folder and exists".format(str(extractTargetRoot)))

    repo = any
    repoExisted = False

    try:
        repo = Repo(repoSystemPath)
        repoExisted = True
    except NoSuchPathError as exc:
        print(exc)
    except InvalidGitRepositoryError as exc:
        print(exc)

    repoPath = Path(repoSystemPath)
    if not repoPath.exists():
        repoExisted = False
        repoPath.mkdir(parents=True)

    if not repoExisted:                         # TODO gitRepoExists
        print("repo didn't exists, create folder and init repo ...")
        repo = gitInitRepo(repoSystemPath)             # TODO gitInitRepo

    if not Path(repoSystemPath + "\\.gitignore").exists():
        message = "no .gitingore file found, continue? [yes/No]:"
        wait_for_input(message)

    if extractTargetRoot.exists() and extractTargetRoot.is_dir():
        print()
        print("Starting with workflow of {} projects...".format(len(projectList)))
        i = 0
        for p in projectList:

            i=i+1
            print()
            print(" {:<3}/{:<3} ... {:<50} ... extracting".format(i, len(projectList), p.fileName))
            ## wait_for_input("continue? [yes/No]:")
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

            # TODO join extractTargetRoot.resolve() with p.fileName to reach extractedPath
            # print(extractTargetSystemPath)
            # if extractTargetRoot.exists():
            #       print(extractTargetRoot.resolve())
            #       print(str(extractTargetRoot))

            # extractedProjectSystemPath = str(extractTargetRoot)+"\\"+p.fileName
            # extractedProjectSystemPath = extractedProjectSystemPath[:-4]   # remove .rar
            # print(extractedProjectSystemPath)

            projectExtractedPath = Path(p.extractPath)
            print(f'{str(projectExtractedPath)} exists? {projectExtractedPath.exists()}')

            if projectExtractedPath.exists():
                # analyseExtractedPath(projectExtractedPath)
                # find root of repo
                # sub-level for repo
                projectExtractedPathRepoLevel = findProjectRepoLevel(projectExtractedPath)
                p.extractPathRepoBase = projectExtractedPathRepoLevel
                print("--- {:<50} : is repo base dir".format(str(projectExtractedPathRepoLevel)))


                # if isRarRootFolderRepoFolder(p):
                #     sysCommand("cd to extracted project folder sub directory")
                #     sysCommand("move all files in cd .\\* to repo folder")
                # else:
                #     sysCommand("move all files in cd .\\* to repo folder")

                # TODO move files to repo

                # Problem: moves complete directory!
                # shutil.move(str(p.extractPathRepoBase.resolve()), repoSystemPath)
                # Fix:
                for entry in p.extractPathRepoBase.iterdir():
                    # print("move " + str(entry))
                    shutil.move(str(entry), repoSystemPath)


                gitCommand("git add .")
                repo.git.add(A=True)        # same as git add .
                gitcmds.append("repo.git.add(A=True)")

                #fileSystemTimestamp = datetime.datetime.fromtimestamp(p.timestamp).isoformat()
                fileSystemTimestamp = p.rfc2822

                commitTitle = "{}".format(p.fileName)  # TODO escape character, convert LF and RETURN to html code?
                commitBody = escape(p.longDescription())    # TODO escape character, convert LF and RETURN to html code?
                # argument: --date = "Sat Nov 14 14:00 2015 +0100"
                gitCommand("git commit -m '{}' -m '{}' --date='{}' ".format(commitTitle, commitBody, fileSystemTimestamp))
                print("fileSystemTimestamp = " + fileSystemTimestamp)
                print('--allow-empty', '-m', f'"{commitTitle}"', '-m', f'"{commitTitle}"', '--date', fileSystemTimestamp)
                parts = ['--allow-empty', '-m', f'"{commitTitle}"', '-m', f'"{commitTitle}"', '--date', fileSystemTimestamp]
                gitcmds.append("repo.git.commit " + " ".join(parts))
                repo.git.commit('--allow-empty', '-m', f'"{commitTitle}"', '-m', f'"{commitTitle}"', '--date', fileSystemTimestamp)  # FIX --allow-empty (if rar files don't contain changes!)
                time.sleep(0.2)
        removeAllProjectFilesFromRepo(repoSystemPath)  # delete last project extracted files

def root_elements(rarfile_content_filenamelist):
    # analyze the rarfile.filenames() list to find all root elements (files and folders)
    rootelements = set()
    for item in rarfile_content_filenamelist:
        rootelements.add(item.split("\\")[0])
    return rootelements


def load_database(filename):
    filename = sanitize_filename(filename + ".pickel.json")
    if not os.path.exists(filename):
        pass
    else:
        with open(filename) as json_file:
            data_encoded = json.load(json_file)
            data = jsonpickle.decode(data_encoded)
            return data

    return None
    

def save_database(data, filename):
    #print("Printing to check how it will look like")
    #print(ProjectEncoder().encode(data))

    #print("Encode Project Objects into JSON formatted Data using custom JSONEncoder")
    #dataJSONData = json.dumps(data, indent=4, cls=ProjectEncoder)
    #print(dataJSONData)

    print("saving {} with {} elements".format(filename,len(data)))

    fullfilename = sanitize_filename(filename + ".json")
    with open(fullfilename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, cls=ProjectEncoder, indent=4)

    fullfilename_pickle = sanitize_filename(filename + ".pickel.json")
    with open(fullfilename_pickle, 'w') as json_file:
        encoded_data = jsonpickle.encode(data)
        json.dump(encoded_data, json_file)


def user_input_path(input_message, check_valid_path):
    repeat = True
    while repeat:
        os.system("cls")
        print ("{}, [0] to cancel".format(input_message))
        input_text = input(">>")
        if input_text == "0":
            break
        if (check_valid_path):
            path = Path(input_text)
            if path.is_dir():
                return path
        else:
            return input_text


def cli_menu():
    # dependencies: 
    # level 0: 1,2,3 possible
    # level 1: 4
    # level 2: 5,6,7
    #
    line_text = "\
        Welcome to SMW-repo-builder\n\
        [1] - set input Folder (rar-Files) \n\
        [2] - set output Folder (extraction) \n\
        [3] - set output Folder (repo) \n\
        [4] - read input Folder \n\
        [5] - output project list \n\
        [6] - compare project list sorting \n\
        [ ] - search through rar-Files \n\
        [ ] - search for file inside rar-Files \n\
        [ ] - search for text inside rar-Files \n\
        [ ] - output timespan of all rar-Files\n\
        [ ] - output rootElements of all rar-Files\n\
        [ ] - export database [pass]\n\
        [ ] - import database [pass]\n\
            \n\
        [ ] - batch: extract all (--- ### ---) rar-Files\n\
        [ ] - batch: built repo from extracted (--- ### ---)\n\
        [100] - batch: run auto workflow (--- ### ---)\n\
        [0] - Exit \n\
        \n\
        Options: \n\
        input-Folder: \n\
        output-Folder (extract): \n\
        output-Folder (repo): \n\
        \n\
        Stats:\n\
            Import Database\n\
                Projects imported: xyz\n\
            readed Folder \n\
                Files found: ###\n\
                rar-Files found: ###\n\
                Projects found: ###\n\
            \n\
        "
    print(line_text)


def command_line_interface():
    input_message = ">>"
    while (True):
        x = ""
        os.system('cls')
        cli_menu()
        x = input(input_message)
        if x == "0":
            exit()
        elif x == "1":
            pass
            # source_folder = user_input_path("rar files directory", True)
        elif x == "2":
            pass
            # extraction_folder = user_input_path("extraction directory", True)
        elif x == "3":
            pass
            # repository_folder = user_input_path("repository directory", True)
        elif x == "4":
            pass
        elif x == "5":
            pass
        elif x == "6":
            pass
        else:
            pass


##
## analyze_rar_files
##  * loops over project_list
##  * checks if item is a rar-File, marks israrfile True/False
##  * loops over all rar Files
##  *   optional: prints rar file content (some filters activated)
##  *   analyses and saves all root_elements() for each rar file in project.rootElements set/list
##  *   prints root_elements
##  *   analyses rootDirectory @depricated !!!! BUG
##  *     prints available rar.getinfo() of rootDirectory
##
def analyze_rar_files(project_list, rootFolders, print_rar_content=False, printRarRootDirectoryDetails=False):
    for p in project_list:
        if rarfile.is_rarfile(p.systemFilePath):
            # is RAR File...
            p.israrfile = True
            rar = rarfile.RarFile(p.systemFilePath)
            
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
            print("{:<30}: {}".format("p.fileName", p.fileName))
            if print_rar_content:
                # list RAR content
                print("{:<30}: contains {} elements; {}".format("rar.namelist()", len(rar.namelist()), "filtered: 'Assets', 'Library'"))
                for file in rar.namelist():
                    if not "Assets" in file:
                        if not "Library" in file:
                            print("{:<30}: {}".format("", file))
            else:
                print("{:<30}: contains {} elements; {}".format("rar.namelist()", len(rar.namelist()), "filtered: *"))

            #print(rar.printdir())
            rootelements = root_elements(rar.namelist())
            p.setRootElements(rootelements)
            print("{:<30}: {}".format("rootelements", len(p.getRootElements())))
            for el in p.getRootElements():
                print("{:<30}: {}".format("", el))

            # BUG: more or less than one root element possible! @deprecated! 
            # FIX empty rar, rar without containing folder
            # TODO renaming rootFolderInRARArchive -> first root element
            if len(rar.namelist()) > 0: 
                first_element_names = rar.namelist()[0].split("\\")
                if len(first_element_names) > 0:
                    rootFolderInRARArchive = first_element_names[0]         # could exist more than one root Element -> use rootelements instead!
                                                                            # could be less than one root elment (empty rar File)!
                else:
                    rootFolderInRARArchive = None
            else:
                rootFolderInRARArchive = None

            # BUG: FIXED
            if len(rar.namelist()) > 0:
                print("{:<30}: {}".format("rar.namelist()[0]", rar.namelist()[0]))
            else:
                print("{:<30}: {}".format("rar.namelist()[0]", None))

            print("{:<30}: {}".format("rootFolderInRARArchive", rootFolderInRARArchive))
            #test = rarfile.RarInfo()
            if printRarRootDirectoryDetails:
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
            # p is not a RAR File!
            #print(p.systemFilePath + " is not a RAR-File!")
            p.israrfile = False



def project_list_stats(projects, show_non_rar_files=False):
    print("project_list_stats...")
    print("project_list_stats, show non rar files = " + "True" if show_non_rar_files else "False")
    rarFiles = 0
    for p in projects:
        if p.israrfile:
            rarFiles += 1 
        else:
            if show_non_rar_files:
                print(p.systemFilePath)
    print(f'num of projects: {len(projects)}')
    print(f'num of rar-files: {rarFiles}')


# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    app = App()
    app.system_path_rar_files
    app.system_path_repo
    app.system_path_extraction

    # command_line_interface()

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


    ##
    ## read directory
    ##

    ###
    ### read directory: Method B (pathlib, recursive)
    ###
    print("load_directory_list...")
    app._project_list_load_via_pathlib = load_directory_list(app.system_path_rar_files)
    # printProjects(app._project_list_load_via_pathlib)
    print()
    project_list_stats(app._project_list_load_via_pathlib, True)
    wait_for_input("app._project_list_load_via_pathlib, continue?")

    ###
    ### read directory: Method A (os, recursive, limitation deepness = 2!!!) - use Method B: load_directory_list() instead!
    ###
    ### app.projects contains matching rar-Files 
    ### app.files contains ALL files (not only rar-files)
    ###
    print("workWithFilelist...")
    workWithFilelist(app.system_path_rar_files, app.projects, app.files)
    # printProjects(app.system_path_rar_files)
    print()
    #project_list_stats(app.projects, False)                     # CAUTION! workWithFilelist doesn't analyze rar-Files, project.israrfile is False
    showFiles(app.files)
    wait_for_input("app._project_list_load_via_os, continue?")

    ####
    #### read directory: Method A 
    #### Analyze RAR Files (still for Method A)
    #### after running this, p in app.projects have p.israrfile is set
    #### after running this, ... TODO need to check what else analyze_rar_files is doing! (timestamp, ...) 
    ####                         TODO compare DOING with reading directory: Method B 
    ####
    print("analyze_rar_files...")
    rootFolders = list()
    analyze_rar_files(app.projects, rootFolders, print_rar_content=False)
    project_list_stats(app.projects, True)  # app.projects with israrfile set
    wait_for_input("analyze_rar_files(), continue?")


    ##
    ## sort Projects
    ##
    sort_show_projects = False                # use to compare lists before and after sorting

    if sort_show_projects:
        print("projects (unsorted)")
        printProjects(app.projects)

    ###
    ### sort Projects: Method A (inline sorting)
    ###
    # app.projects.sort(key=operator.attrgetter('timestamp'))    # inline sorting

    ###
    ### sort Projects: Method B (sort copy)
    ###
    app.projects_sorted = sorted(app.projects, key=operator.attrgetter('timestamp'))  # sort copy

    if sort_show_projects:
        print("projects Sorted")
        printProjects(app.projects_sorted)


    ##
    ## @deprecated use compare timestamps to visually check order and check timestamps source!
    ## Visual sort check - compare project properties
    ## * timestamp:
    ##              extracted from filename 
    ##              extracted from filesystem (last modified date)
    ## * order (sorted by filesystem)
    ##
    skip_visual_sort_check = True
    if not skip_visual_sort_check:
        print("visual compare project_list with project_list_sorted")
        for i in range(len(app.projects_sorted)):
            p = app.projects[i].fileName
            ps = app.projects_sorted[i].fileName
            compareresult = "not tested"
            if p == ps:
                compareresult = " ="
            else:
                compareresult = "!!!"
            print("{:<130} {:<3} {:<130}".format(p, compareresult, ps))

        wait_for_input("check sorted list [yes,no]:")


    ##
    ## save
    ##
    ## Format:
    ## * json (human readable)
    ## * json.pickle (more complexe object types are possible to serialize)
    ##
    ## Objects:
    ## * app.project_list           --> File: "app.project_list.json"
    ##                              --> File: "app.project_list.json.pickle"
    ## * app.project_list_sorted    --> File: "app.project_list_sorted.json"
    ##                              --> File: "app.project_list_sorted.json.pickle"
    ##

    print("saving database...")
    save_database(app.projects, "app.projects")
    save_database(app.projects_sorted, "app.projects_sorted")
    save_database(app._project_list_load_via_pathlib, "app._project_list_load_via_pathlib")


    ##
    ## load 
    ##
    ## source File:
    ## * "app.project_list_sorted.json.pickle" 
    ##
    ## load @
    ## app._project_list_loaded
    ##

    print("loading database...")
    app._project_list_loaded = load_database("app.projects_sorted")
    print("loaded {} elements".format(len(app._project_list_loaded)))
    print("loaded Projects:")
    printProjects(app._project_list_loaded)
    wait_for_input("check loaded projects list [yes,no]:")


    ##
    ## show RAR content: root elements
    ##

    showRARArchiveRootFolder = True
    print()
    print("show RAR content: root elements")
    
    if showRARArchiveRootFolder:
        num_of_rar_files = 0
        for p in app.projects:
            if p.israrfile:
                num_of_rar_files = num_of_rar_files + 1
        print("{:<30}: {}".format("num_of_rar_files", num_of_rar_files))
        print()

        print("RAR rootFolders (all projects summarized)")
        for item in set(rootFolders):
            print("\t{}".format(item))  # hide duplicates from list
        print()

        print("RAR rootFolders by project")
        print("{:<130} {:<55} {}".format("file", "root folder", "amount of root Elements"))
        for p in app.projects_sorted:
            if len(p.rootElements) == 1:
                #print("{:<130} {:<55} {}".format(p.fileName, p.rarRootFolder, len(p.rootElements)))            # deprecated: p.rarRootFolder
                print("{:<130} {:<55} {}".format(p.fileName, ", ".join(p.getRootElements()), len(p.rootElements)))
            elif len(p.rootElements) > 1:
                print("{:<130} {:<55} {}".format(p.fileName, "------------------------------------------------", len(p.rootElements)))
                i = 0
                for e in p.getRootElements():
                    i += 1
                    print("{:<127} [{}] {:<55}".format("|>", i, e))
            else:
                print("{:<130} {:<55} {}".format(p.fileName, ", ".join(p.getRootElements()), len(p.rootElements)))


    ##
    ## compare timestamps
    ## * timestamp:
    ##              extracted from filename 
    ##              extracted from filesystem (last modified date)
    ## * order (sorted by filesystem)
    ##
    print()
    print(" ! IMPORTANT !")
    print(" ! please check timestamps, especially for !!! marked entries      !")
    print(" ! if fileName has a wrong nameing scheme, or maybe no date set,   !")
    print(" ! consider checking rar file content to get the modification date !")
    print(" ! IMPORTANT !")
    print("\\|/ \\|/ \\|/ \\|/ \\|/ \\|/ \\|/ \\|/ \\|/ \\|/ \\|/ \\|/ \\|/ \\|/")
    print()

    print("{:<25} {:<5} {:<20} {}".format("\\|/ FileSystem \\|/", " ", "FileName", "p.fileName"))
    for p in app.projects_sorted:
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
            compareresult = " = "
        else:
            compareresult = "!!!"
        print("{:<25} {:<5} {:<20} {}".format(fileSystemTimestamp, compareresult, fileNameTimestamp, p.fileName))

    print()
    print("/|\\ /|\\ /|\\ /|\\ /|\\ /|\\ /|\\ /|\\ /|\\ /|\\ /|\\ /|\\ /|\\ /|\\")
    print(" ! IMPORTANT !")
    print(" ! please check timestamps, especially for !!! marked entries      !")
    print(" ! if fileName has a wrong nameing scheme, or maybe no date set,   !")
    print(" ! consider checking rar file content to get the modification date !")
    print(" ! IMPORTANT !")
    print()
    wait_for_input("check timestamps [yes,no]:")

    ##
    ##  Workflow
    #       RAR Extraction
    #       File Moving
    #       git adding
    #       git commiting
    ##

    wait_for_input("start workflow? [yes,no]:")
    gitcmds = list()
    workflow(app.projects_sorted, app.system_path_extraction, app.system_path_repo)     #  FIX project order

    for i in gitcmds:
        print(i)

    for p in app.projects_sorted:
        print(str(p.extractPathRepoBase))
# See PyCharm help at https://www.jetbrains.com/help/pycharm/
