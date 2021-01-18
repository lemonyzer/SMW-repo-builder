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

import deprecation
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


##
## load_directory_list
## 
## param: system_path_rar_files
## return: project_list (list<Project>)
##
## loads and loops/iterates through directory elements
##  if element is directory
##    ... -> recursive call (load_directory_list) with current directory as system_path_rar_files 
##  if element is file
##    call read_project_details_from_system_path()
##    append initialized project to project_list
## 
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
            if (project.israrfile):
                project_list.append(project)
            else:
                print(f"dropping: {entry}")

    return project_list


##
## read_project_details_from_system_path
##
## parameter: 
##   * file_system_path: any File Path (not only rar-Files) 
##
## return: Project Object
##
def read_project_details_from_system_path(file_system_path):
    file_path = Path(file_system_path)
    # print("read project details from " + str(file_path))
    # proj_timestamp = get_timestamp_from_filename(entry)
    proj_timestamp = get_timestamp_from_filesystem(str(file_path))
    proj_name = get_project_name_from_filename(file_path.name)
    proj_info = get_project_additional_info_from_filename(file_path.name)
    proj_system_path = str(file_path)
    currentProject = Project(proj_timestamp, proj_name, proj_info, proj_system_path, file_path.name)

    read_rar_specific_details_from_system_path(currentProject)
    return currentProject


def read_rar_specific_details_from_system_path(project):

    if rarfile.is_rarfile(project.systemFilePath):
        project.israrfile = True
        rar = rarfile.RarFile(project.systemFilePath)
        root_elements = get_root_elements_from_rar_namelist(rar.namelist())
        project.root_elements = root_elements
        
        # TODO: append / extend ...
        app._global_rar_root_elements.extend(root_elements)
    else:
        project.israrfile = False
    print("{:<30}: {}".format(project.systemFilePath, "file" + (" RAR" if project.israrfile else " NOT RAR marked")))   # conditional expression
    
    return


def showFiles(file_list):
    print("showFiles()...")
    for e in file_list:
        print(f'- {e}')


def showProjects(project_list):
    for p in project_list:
        print()
        p.say_state()
        print()


def smw_schema_get_info_from_filename(filename, selected_property):

    # check naming schema for all projects
    # smw standard naming schema (some exceptions existing)
    #                    \|/
    #       123456789012345   (15. element is seperator)
    #       SuperMariaWars 2021.01.16 Description.rar
    #       SuperMariaWars_2021.01.17 Description.rar
    #       Maps_v15.rar
    #
    # split string with " ", 1 time => list with 2 itmes

    filename_properties = {
        "project_name" : "",
        "timestamp" : ""
    }

    if len(filename) > 15:
        splitChar = ""
        if filename[14] == " ":
            splitChar = filename[14]
        elif filename[14] == "_":
            splitChar = filename[14]

        # BUG can't splitt with empty separator!
        # FIX
        if splitChar == "":
            # different naming schema
            # project name will not be extracted, instead full filename will be used
            # timestamp will not be extracted, instead "0000.00.00" will be used
            filename_properties["project_name"] = filename
            filename_properties["timestamp"] = "0000.00.00"
        else:
            data = filename.split(splitChar, 1)

            # project name extracted (first part of splitted string)
            filename_properties["project_name"] = data[0]

            if len(data) > 1:
                # second part (should start with timestamp), proceeding...
                # timestamp format: 10 characters
                # 123456789T
                # 2014.08.08
                filename_properties["timestamp"] = data[1][0:10]
            else:
                # no second existing (splitting resulted in array of size 1)
                # timestamp will not be extracted, instead "0000.00.00" will be used
                filename_properties["timestamp"] = "0000.00.00"
    else:
        # filename is not long enough, doesn't matches standard smw naming schema!
        # project name will not be extracted, instead full filename will be used
        # timestamp will not be extracted, instead "0000.00.00" will be used
        filename_properties["project_name"] = filename
        filename_properties["timestamp"] = "0000.00.00"

    return filename_properties[selected_property]


def get_timestamp_from_filename(filename):
    return smw_schema_get_info_from_filename(filename, "timestamp")

def get_timestamp_from_rar_root_elements(project):
    rar = rarfile.RarFile(project.systemFilePath)
    
    root_elements = project.root_elements
    string_list = []
    for e in root_elements:
        # https://www.saltycrane.com/blog/2008/11/python-datetime-time-conversions/
        # Example:
        # datetime object to string
        # dt_obj = datetime(2008, 11, 10, 17, 53, 59)
        # date_str = dt_obj.strftime("%Y-%m-%d %H:%M:%S")
        #
        # Example:
        # time tuple to datetime object
        # time_tuple = (2008, 11, 12, 13, 51, 18, 2, 317, 0)
        # dt_obj = datetime(*time_tuple[0:6])
        # print repr(dt_obj) 

        # time tipe --> datetime object --> string       
        time_tuple = rar.getinfo(e).date_time
        dt_obj = datetime.datetime(*time_tuple[0:3])    # FIX: data in time_tuple[4:6] doesn't represent the correct time. need to investigate
        date_str = dt_obj.strftime("%Y.%m.%d")
        string_list.append(f"{date_str}; {rar.getinfo(e).filename}")

    return string_list

def get_newest_timestamp_from_rar_elements(project):
    # TODO:
    # finds latest modified file
    # returns date + time (+ filename?)
    pass


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


def get_timestamp_from_filesystem(file_name):
    return modified_date(file_name)


def get_project_name_from_filename(filename):
    return smw_schema_get_info_from_filename(filename, "project_name")



def get_project_additional_info_from_filename(file_name):
    # split string with " ", 1 time => list with 2 itmes
    data = file_name.split(" ", 1)
    if len(data) > 1:
        return data[1][10:]
    return ""


def printProjects(list):
    print("{:<18} - {:<31} - {:<24} - {:<120} - {}".format("timestamp", "rfc2822", "local_time", "fileName", "numOf root_elements"))
    for p in list:
        timestamp = p.timestamp
        local_time = time.ctime(timestamp)
        rfc2822 = formatdate(timestamp, True)
        p.rfc2822 = rfc2822
        print("{:<18} - {} - {} - {:<120} - {}".format(timestamp, rfc2822, local_time, p.fileName, len(p.root_elements)))


def gitInitRepo(repo_system_path):
    repo = Repo.init(repo_system_path)

    gitCommand("git init")
    sysCommand("copy .gitignore")   #  TODO .gitignore
    src = os.getcwd() + "\\Unity.gitignore"
    dst = repo_system_path + "\\.gitignore"
    shutil.copy(src, dst)

    # gitCommand("git add - a")
    # gitCommand("git commit")

    return repo


def gitCommand(cmd):
    print(cmd)


def sysCommand(cmd):
    print(cmd)


def remove_all_project_files_from_repo(repo_system_path):
    # keep
    #.git
    #.gitignore
    sysCommand("rm {} -r -e:.git .gitignore".format(repo_system_path))

    exclusions = [".git", ".gitignore"]
    print(f'exclusions: {exclusions}')
    remove_recursive(repo_system_path, exclusions)


def remove_recursive(element_system_path, exclusions):
    repo = Path(element_system_path)
    for entry in repo.iterdir():

        if entry.name in exclusions:
            # exclusion found, don't delete entry
            print(f'exclusions found {entry.name}')
            continue
        else:
            if entry.is_dir():
                # is_Directory
                remove_recursive(str(entry), exclusions)
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
    intersectResult = compare_intersect(project.root_elements, valid)

    print(intersectResult)
    if len(intersectResult) >= 1:
        return True
    else:
        return False


def systemPathExists(systemPath):
    sysCommand(systemPath + "exists? {}".format(os.path.isdir(systemPath)))
    #return os.path.isdir(os.path.join(basepath, entry))
    return os.path.isdir(systemPath)


def gitRepoExists(repo_system_path):
    # Option B return repo ... return null if not exists
    # repo = any
    repoExists = False

    try:
        # Option B
        # repo = Repo(repo_system_path)
        Repo(repo_system_path)
        repoExists = True
    except NoSuchPathError as exc:
        print(exc)
    except InvalidGitRepositoryError as exc:
        print(exc)

    return repoExists


def extract_project(proj, extract_destination_system_path, use_custom_filter=False):
    # extract rar-file to targetDir\rar-file-name\
    project_extract_path = extract_destination_system_path + "\\" + proj.fileName
    project_extract_path = project_extract_path[:-4]
    project_extract_path = project_extract_path.rstrip()  # FIX for rarfalies with space before extension "xyz .rar"
    proj.extractPath = project_extract_path
    rarf = rarfile.RarFile(proj.systemFilePath)
    
    if (use_custom_filter):
        filtered_members = filter_unescessary_files_from_rar(proj, rarf)
        print("filtered_members {} / {}".format(len(filtered_members), len(rarf.namelist())))
        rarf.extractall(project_extract_path, members=filtered_members)
    else:
        rarf.extractall(project_extract_path)

    sysCommand("extract (use_filter={}) {} ------> .... rarf.extractall .... {})".format(str(use_custom_filter), proj.systemFilePath, extract_destination_system_path))


def maxLevel(checkLevel, arrayLength):
    if checkLevel == 0:
        return 0
    else:
        # can't filter checkLevel 1 (1 Level subdir) if array has only one element
        if arrayLength > 1:
            return 1
        else:
            return 0


def filter_unescessary_files_from_rar(proj, rar_file):
    exclusions = ["Library", "Temp", "Obj", "Build", "Builds", "Logs", "User Settings", ".vs", ".gradle"]
    debug = False
    #for m in rar_file.namelist():
    #    print(f'{m}')

    checkLevel = 0

    if len(proj.root_elements) == 1:
        # single root element
        if "Assets" in proj.root_elements:
            print("Assets is rootElement, no filtering explusions!!!")
            return rar_file.namelist()
        else:
            # other rootElement (propably <UnityProjectName>)
            checkLevel = 1
            pass
    elif len(proj.root_elements) > 1:
        # multiple root elements
        if "Assets" in proj.root_elements:
            # Assets in root_elements found, filtering only in level 0
            checkLevel = 0
        else:
            # Assets NOT in root_elements found, filtering in level 1
            checkLevel = 1

    filteredmembers = list()
    excludedmembers = list()
    for member in rar_file.namelist():
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
    if app._main_wait_for_input:
        x = ""
        while x not in ["yes", "YES", "N", "n", "No"]:
            x = input(message)
            if x in ["N", "n", "No"]:
                exit()
            elif x in ["yes", "YES"]:
                break
    else:
        print("AUTO MODE")


def workflow(projectList, extract_destination_system_path, repo_system_path):
    ##
    ## workflow
    ##
    ## Init:
    ##  * check if extract destination system path exists
    ##  * check if repo exists
    ##  *   if not create it
    ##  *   if yes, 
    ##  *           Warn User: repo exists
    ##  *           Ask User: a) want to overwrite (delete repo and create new one)?
    ##  *                     b) want to use it (commits will be applied in existing repo)?
    ##  * 
    ##
    ## Loop project_list:
    ##  1* remove all files and folders in repo system path (except: .git, .gitignore)
    ##  2* extract project
    ##  3* cd to extracted project
    ##  4*   cd to repo root level of extracted project
    ##  5* move all files and folders to repo system path
    ##  6* run git commands
    ##  7*   git add .
    ##  8*   git commit --allow-empty -m <comment> -m <comment2> -m <comment3> --date rfc2822
    ##
    ## Finialize:
    ##  * remove all project files and folders in repo system path (except: .git, .gitignore)
    ##

    ## git workflow
    ## https://lemonyzed.atlassian.net/wiki/spaces/SE/pages/105545805/git

    extractTargetRoot = Path(extract_destination_system_path)
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
        repo = Repo(repo_system_path)
        repoExisted = True
    except NoSuchPathError as exc:
        print(exc)
    except InvalidGitRepositoryError as exc:
        print(exc)

    repoPath = Path(repo_system_path)
    if not repoPath.exists():
        repoExisted = False
        repoPath.mkdir(parents=True)

    if not repoExisted:                         # TODO gitRepoExists
        print("repo didn't exists, create folder and init repo ...")
        repo = gitInitRepo(repo_system_path)             # TODO gitInitRepo

    if not Path(repo_system_path + "\\.gitignore").exists():
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
            remove_all_project_files_from_repo(repo_system_path)  # delete previous project files

            extract_project(p, extract_destination_system_path)  # /projects/<rar-filename>/
            ## extract_destination_system_path
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
            #analyseExtractedFolder(p, extract_destination_system_path)

            # normal:
            # cd rarRootFolder
            # rarRootFolder\* -> repo\*
            # move all files inside rootFolder to repoFolder

            sysCommand("cd to extracted project folder")

            # TODO join extractTargetRoot.resolve() with p.fileName to reach extractedPath
            # print(extract_destination_system_path)
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
                # shutil.move(str(p.extractPathRepoBase.resolve()), repo_system_path)
                # Fix:
                for entry in p.extractPathRepoBase.iterdir():
                    # print("move " + str(entry))
                    shutil.move(str(entry), repo_system_path)


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
                #time.sleep(0.2)
        remove_all_project_files_from_repo(repo_system_path)  # delete last project extracted files


def get_root_elements_from_rar_namelist(rarfile_content_filenamelist):
    # analyze the rarfile.filenames() list to find all root elements (files and folders)
    root_elements = set()
    for item in rarfile_content_filenamelist:
        root_elements.add(item.split("\\")[0])
    return root_elements


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
        [ ] - output root_elements of all rar-Files\n\
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
##  *   analyses and saves all get_root_elements_from_rar_namelist() for each rar file in project.root_elements set/list
##  *   saves all root_elements in global_rar_root_elements (sumarization of all rar files)
##  *   prints root_elements
##  *   analyses rootDirectory @depricated !!!! BUG
##  *     prints available rar.getinfo() of rootDirectory
##
def analyze_rar_files(project_list, global_rar_root_elements, print_rar_content=False, print_rarinfo_properties_of_first_element_in_rar=False):
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
            root_elements = get_root_elements_from_rar_namelist(rar.namelist())
            p.root_elements = root_elements
            print("{:<30}: {}".format("root_elements", len(p.root_elements)))
            for el in p.root_elements:
                print("{:<30}: {}".format("", el))

            # first_element_in_rar
            if len(rar.namelist()) > 0:
                first_element_in_rar = rar.namelist()[0]
                print("{:<30}: {}".format("rar.namelist()[0]", first_element_in_rar))
                if print_rarinfo_properties_of_first_element_in_rar:
                    print_rar_getinfo_properies(rar, first_element_in_rar)
            else:
                print("{:<30}: {}".format("rar.namelist()[0]", None))

            print()
            
            global_rar_root_elements.extend(root_elements)
        else:
            # p is not a RAR File!
            #print(p.systemFilePath + " is not a RAR-File!")
            p.israrfile = False

def print_rar_getinfo_properies(rar, rar_info_element):
    print("{:<30}: {}".format("getinfo()", rar_info_element))
    print("{:<30} {:<30}: {}".format("", "date_time", rar.getinfo(rar_info_element).date_time))
    print("{:<30} {:<30}: {}".format("", "filename", rar.getinfo(rar_info_element).filename))
    #print("{:<30} {:<30}: {}".format("", "compress_type", rar.getinfo(rar_info_element).compress_type))
    print("{:<30} {:<30}: {}".format("", "comment", rar.getinfo(rar_info_element).comment))
    print("{:<30} {:<30}: {}".format("", "create_system", rar.getinfo(rar_info_element).create_system))
    print("{:<30} {:<30}: {}".format("", "extract_version", rar.getinfo(rar_info_element).extract_version))
    print("{:<30} {:<30}: {}".format("", "flag_bits", rar.getinfo(rar_info_element).flag_bits))
    print("{:<30} {:<30}: {}".format("", "CRC", rar.getinfo(rar_info_element).CRC))
    print("{:<30} {:<30}: {}".format("", "rar.getinfo(rar_info_element)", rar.getinfo(rar_info_element)))


def project_list_stats(projects, show_non_rar_files=False):
    print("project_list_stats...")
    print("project_list_stats, show non rar files = " + "True" if show_non_rar_files else "False")
    rar_files = 0
    for p in projects:
        if p.israrfile:
            rar_files += 1 
        else:
            if show_non_rar_files:
                print(p.systemFilePath)
    print(f'num of projects: {len(projects)}')
    print(f'num of rar-files: {rar_files}')


def main_read_directory():
    ##
    ## read directory
    ##

    ###
    ### read directory: Method B (pathlib, recursive)
    ###
    print("load_directory_list...")
    app.projects = load_directory_list(app.system_path_rar_files)
    # printProjects(app._project_list_load_via_pathlib)
    print()
    project_list_stats(app.projects, True)
    wait_for_input("app.projects, continue?")
    

def main_sort():
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


def main_visual_sort_check():
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
            p = app.projects[i].fileName                                    # project
            ps = app.projects_sorted[i].fileName                            # project_sorted
            compareresult = "not tested"
            if p == ps:
                compareresult = " ="
            else:
                compareresult = "!!!"
            print("{:<130} {:<3} {:<130}".format(p, compareresult, ps))

        wait_for_input("check sorted list [yes,no]:")


def main_save():
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


def main_load():
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


def main_visual_check_rar_root_elements():
    ##
    ## show RAR content: root elements
    ##
    projects = app._project_list_loaded
    showRARArchiveRootFolder = True
    print()
    print("show RAR content: root elements")
    
    if showRARArchiveRootFolder:
        num_of_rar_files = 0
        for p in projects:
            if p.israrfile:
                num_of_rar_files = num_of_rar_files + 1
        print("{:<30}: {}".format("num_of_rar_files", num_of_rar_files))
        print()

        print("RAR global_rar_root_elements (all projects summarized)")
        for item in set(app._global_rar_root_elements):
            print("\t{}".format(item))  # hide duplicates from list
        print()

        print("RAR root elements folders/files by project")
        print("{:<130} {:<55} {}".format("file", "root folder", "amount of root Elements"))
        for p in projects:
            if len(p.root_elements) == 1:
                print("{:<130} {:<55} {}".format(p.fileName, ", ".join(p.root_elements), len(p.root_elements)))
            elif len(p.root_elements) > 1:
                print("{:<130} {:<55} {}".format(p.fileName, "------------------------------------------------", len(p.root_elements)))
                i = 0
                for e in p.root_elements:
                    i += 1
                    print("{:<127} [{}] {:<55}".format("|>", i, e))
            else:
                print("{:<130} {:<55} {}".format(p.fileName, ", ".join(p.root_elements), len(p.root_elements)))

    wait_for_input("check root elements [yes,no]:")


def main_visual_check_compare_sort_and_timestamps():
    ##
    ## compare timestamps
    ## * timestamp:
    ##              extracted from filesystem (last modified date)
    ##              extracted from filename 
    ##              extracted from rar root elements
    ##              TODO: display last modified file from rar content
    ## * order (sorted by filesystem)
    ##
    projects = app._project_list_loaded
    print()
    print(" ! IMPORTANT !")
    print(" ! please check timestamps, especially for !!! marked entries      !")
    print(" ! if fileName has a wrong nameing scheme, or maybe no date set,   !")
    print(" ! consider checking rar file content to get the modification date !")
    print(" ! IMPORTANT !")
    print("\\|/ \\|/ \\|/ \\|/ \\|/ \\|/ \\|/ \\|/ \\|/ \\|/ \\|/ \\|/ \\|/ \\|/")
    print()

    print("{:<25} {:<5} {:<20} {:<82} {}".format("\\|/ FileSystem \\|/", " ", "FileName", "Date from RARInfo of RAR root elements", "p.fileName"))
    for p in projects:
        fileNameTimestamp = get_timestamp_from_filename(p.fileName)
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
        print("{:<25} {:<5} {:<20}\\  {:<80} {}".format(fileSystemTimestamp, compareresult, fileNameTimestamp, "", p.fileName))

        for timestamp_with_element_name in get_timestamp_from_rar_root_elements(p):
            print("{:<25} {:<5} {:<20} |-{:<80} {}".format( "", "", "", timestamp_with_element_name, "" ))

        #print("{:<25} {:<5} {:<20} / {:<80} {}".format("", "", "", "", "" ))
        print()


    print()
    print("/|\\ /|\\ /|\\ /|\\ /|\\ /|\\ /|\\ /|\\ /|\\ /|\\ /|\\ /|\\ /|\\ /|\\")
    print(" ! IMPORTANT !")
    print(" ! please check timestamps, especially for !!! marked entries      !")
    print(" ! if fileName has a wrong nameing scheme, or maybe no date set,   !")
    print(" ! consider checking rar file content to get the modification date !")
    print(" ! IMPORTANT !")
    print()
    wait_for_input("check timestamps [yes,no]:")

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
    main_read_directory()
    

    ##
    ## sort Projects
    ##
    main_sort()


    # deprecated 
    # main_visual_sort_check()


    ##
    ## save
    ##
    main_save()
    

    ##
    ## load
    ##
    main_load()


    ##
    ## show RAR content: root elements
    ##
    main_visual_check_rar_root_elements()

    ##
    ## compare timestamps
    ##
    main_visual_check_compare_sort_and_timestamps()


    ##
    ##  Workflow
    ##       RAR Extraction
    ##       File Moving
    ##       git adding
    ##       git commiting
    ##
    projects = app._project_list_loaded

    wait_for_input("start workflow? [yes,no]:")

    while input("FORCED STOP BEFORE WORKFLOW STARTS (continue with 'y')") != "y":
        pass

    gitcmds = list()
    workflow(projects, app.system_path_extraction, app.system_path_repo)     

    for i in gitcmds:
        print(i)

    for p in projects:
        print(str(p.extractPathRepoBase))
