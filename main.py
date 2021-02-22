# This is a sample Python script.
import datetime
import platform
import time
import operator
from email.utils import formatdate
from html import escape

from projectsnapshot import ProjectSnapshot
from projectsnapshot import ExtendedRarInfo
from projectsnapshot import ProjectSnapshotEncoder

import os
from pathlib import Path, PurePath
from unrar import rarfile
from unrar import unrarlib
import shutil
from git import Repo, NoSuchPathError, InvalidGitRepositoryError, Actor

import json
import jsonpickle

from pathvalidate import sanitize_filename  # sanitize_filename()  #  py -m pip install pathvalidate

import deprecation
from appsettings import AppSettings

from models import DB_ProjectSnapshot, DB_RAR_Content

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
## return: project_list (list<ProjectSnapshot>)
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

        if entry.is_file():
            print("{:<30}: {} {}".format(str(path_entries), "file", entry.name))
            project = read_project_details_from_system_path(str(entry))
            if (project.rar_is_rar_file):
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
## return: ProjectSnapshot Object
##
def read_project_details_from_system_path(file_system_path):
    file_path = Path(file_system_path)
    # print("read project details from " + str(file_path))

    # Analyze file name
    filename_properties = smw_schema_get_info_from_filename(file_path.name)
    proj_name = filename_properties["project_name"]                    # get_project_name_from_filename(file_path.name)
    proj_timestamp_from_filename = filename_properties["timestamp"] # get_timestamp_from_filename(str(file_path))
    proj_info = filename_properties["additional_info"]              # get_project_additional_info_from_filename(file_path.name)

    # Analyze file system
    # Timestamp exceptions:
    # * CrystalQuest_2015.02.01_check
    # * uNet Sandbox_ramstein_7z_8_somthing_between_7and8.rar
    if file_path.name == "CrystalQuest_2015.02.01_check.rar":
        print(f"replacing timestamp: {file_path.name}")
        # date : 2015-02-01T01:01:01+00:00
        # unix : 1422752461
        proj_timestamp_from_filesystem = 1422752461
    elif file_path.name == "uNet Sandbox_ramstein_7z_8_somthing_between_7and8.rar":
        print(f"replacing timestamp: {file_path.name}")
        # date : 2016-03-03T12:00:00+00:00
        # unix : 1457006400
        proj_timestamp_from_filesystem = 1457006400
    else:
        proj_timestamp_from_filesystem = get_timestamp_from_filesystem(str(file_path))
    
    proj_timestamp_from_filesystem_rfc2822 = formatdate(proj_timestamp_from_filesystem, True)

    # store data in project
    currentProject = ProjectSnapshot()
    # Filesystem
    currentProject.filesystem_file_path = str(file_path)
    currentProject.filesystem_timestamp_modified = proj_timestamp_from_filesystem
    currentProject.filesystem_timestamp_modified_rfc2822 = proj_timestamp_from_filesystem_rfc2822
    # Filename
    currentProject.filename = file_path.name
    currentProject.filename_project_name = proj_name
    currentProject.filename_timestamp = proj_timestamp_from_filename
    currentProject.filename_additional_info = proj_info
    # RAR-properties
    read_rar_specific_details_from_system_path(currentProject)
    return currentProject


def read_rar_specific_details_from_system_path(project):

    if rarfile.is_rarfile(project.filesystem_file_path):
        project.rar_is_rar_file = True
        rar = rarfile.RarFile(project.filesystem_file_path)
        results = get_root_elements_and_newest_elements_from_rar_infolist(rar.infolist())

        project._rar_content_newest_directory_element = results["newest_rar_directory"].filename
        project._rar_content_newest_directory_element_timestamp = results["newest_rar_directory"].date_time
        project._rar_content_newest_file_element = results["newest_rar_file"].filename
        project._rar_content_newest_file_element_timestamp = results["newest_rar_file"].date_time
        
        '''
        project._rar_content_newest_directory_element = result["newest_directory_filename"]
        project._rar_content_newest_directory_element_timestamp = result["newest_directory_timestamp"]
        project._rar_content_newest_file_element = result["newest_file_filename"]
        project._rar_content_newest_file_element_timestamp = result["newest_file_timestamp"]
        '''
        project.rar_root_elements = results["root_elements"]

        results_2 = filter_unescessary_files_from_rar(project, rar)

        if results_2:
            project.rar_extended_infolist = results_2["ex_infolist"]
            project.rar_to_extract_namelist = results_2["filteredmembers"]
            project.rar_not_to_extract_namelist = results_2["excludedmembers"]
        else:
            project.rar_extended_infolist = list()
            project.rar_to_extract_namelist = rar.namelist()
            project.rar_not_to_extract_namelist = list()

        
        results_3 = get_newest_elements_from_filtered_rar_infolist(results_2["filtered_infolist"])
        
        project._rar_content_newest_directory_element = results_3["newest_rar_directory"].filename
        project._rar_content_newest_directory_element_timestamp = results_3["newest_rar_directory"].date_time
        project._rar_content_newest_file_element = results_3["newest_rar_file"].filename
        project._rar_content_newest_file_element_timestamp = results_3["newest_rar_file"].date_time
        

        app._global_rar_root_elements.extend(results["root_elements"])
    else:
        project.rar_is_rar_file = False
    print("{:<30}: {}".format(project.filesystem_file_path, "file" + (" RAR" if project.rar_is_rar_file else " NOT RAR marked")))   # conditional expression
    
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


def smw_schema_get_info_from_filename(filename):

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
        "timestamp" : "",
        "additional_info" : ""
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
            filename_properties["additional_info"] = ""
        else:
            data = filename.split(splitChar, 1) # split only one time!
                                                # ideal case:
                                                # data[0] = project_name
                                                # data[1] = ####.##.## additional info...


            # project name extracted (first part of splitted string)
            filename_properties["project_name"] = data[0]

            if len(data) > 1:
                # second part (should start with timestamp), proceeding...
                # timestamp format: 10 characters
                # 123456789T
                # 2014.08.08
                # [start : end : step]
                # * index starts from 0
                # * end index is not included
                filename_properties["timestamp"] = data[1][0:10]        # first 10 characters are the timestamp
                filename_properties["additional_info"] = data[1][10:]    # substring from 11. positon till end is additional info string
            else:
                # no second existing (splitting resulted in array of size 1)
                # timestamp will not be extracted, instead "0000.00.00" will be used
                filename_properties["timestamp"] = "0000.00.00"
                filename_properties["additional_info"] = ""

    else:
        # filename is not long enough, doesn't matches standard smw naming schema!
        # project name will not be extracted, instead full filename will be used
        # timestamp will not be extracted, instead "0000.00.00" will be used
        filename_properties["project_name"] = filename
        filename_properties["timestamp"] = "0000.00.00"
        filename_properties["additional_info"] = ""

    return filename_properties


def get_project_name_from_filename(filename):
    return smw_schema_get_info_from_filename(filename)["project_name"]


def get_project_additional_info_from_filename(filename):
    return smw_schema_get_info_from_filename(filename)["additional_info"]


def get_timestamp_from_filename(filename):
    return smw_schema_get_info_from_filename(filename)["timestamp"]


def get_timestamp_from_rar_root_elements(project):
    rar = rarfile.RarFile(project.filesystem_file_path)
    
    root_elements = project.rar_root_elements
    string_list = []
    for e in root_elements:
        
        date_str = rar_datetime_to_datestr(rar.getinfo(e).date_time)       

        string_list.append(f"{date_str}; {rar.getinfo(e).filename}")

    return string_list


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



def print_projects(list):
    print("{:<18} - {:<31} - {:<24} - {:<120} - {}".format("timestamp", "rfc2822", "local_time", "fileName", "numOf root_elements"))
    for p in list:
        timestamp = p.filesystem_timestamp_modified
        local_time = time.ctime(timestamp)
        rfc2822 = p.filesystem_timestamp_modified_rfc2822
        print("{:<18} - {} - {} - {:<120} - {}".format(timestamp, rfc2822, local_time, p.filename, len(p.rar_root_elements)))


def git_init_repo(repo_system_path):
    repo = Repo.init(repo_system_path)

    git_command("git init")
    sys_command("copy .gitignore")   #  TODO .gitignore
    src = os.getcwd() + "\\Unity.gitignore"
    dst = repo_system_path + "\\.gitignore"
    shutil.copy(src, dst)

    # git_command("git add - a")
    # git_command("git commit")

    return repo


def git_command(cmd):
    print(cmd)


def sys_command(cmd):
    print(cmd)


def remove_all_project_files_from_repo(repo_system_path):
    # keep
    #.git
    #.gitignore
    sys_command("rm {} -r -e:.git .gitignore".format(repo_system_path))

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


def is_rar_root_folder_repo_folder(project):
    # if RootElement is on of the string in valid array, it is the repo Folder and we need to cd "change direction" on path deeper
    valid = ["SuperMarioWars", "SuperMarioWars_UnityNetwork", "SuperMarioWars 2015.04.08_1_Changes", "SuperMarioWars_clean"]

    # https://stackoverflow.com/questions/1388818/how-can-i-compare-two-lists-in-python-and-return-matches
    intersectResult = compare_intersect(project.rar_root_elements, valid)

    print(intersectResult)
    if len(intersectResult) >= 1:
        return True
    else:
        return False


def systemPathExists(systemPath):
    sys_command(systemPath + "exists? {}".format(os.path.isdir(systemPath)))
    #return os.path.isdir(os.path.join(basepath, entry))
    return os.path.isdir(systemPath)


def git_repo_exists(repo_system_path):
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

def is_rar_root_element(rar_filename):
    if rar_filename == rar_filename.split("\\", 1)[0]:
        return True
    else:
        return False

def extract_project(proj, extract_destination_system_path, use_filtered_namelist=True):
    # extract rar-file to targetDir\rar-file-name\
    project_extract_path = extract_destination_system_path + "\\" + proj.filename
    project_extract_path = project_extract_path[:-4]
    project_extract_path = project_extract_path.rstrip()  # FIX for rarfalies with space before extension "xyz .rar"
    proj.extraction_destination = project_extract_path
    rarf = rarfile.RarFile(proj.filesystem_file_path)
    
    if (use_filtered_namelist):
        # !!!
        # TODO filter_unescessary_files_from_rar already executed, results NOT stored in project.....
        # TODO store restults 
        #
        # filtered_members = filter_unescessary_files_from_rar(proj, rarf)["filteredmembers"]
        # DONE
        filtered_members = proj.rar_to_extract_namelist
        print("filtered_members {} / {} are going to get extracted...".format(len(filtered_members), len(rarf.namelist())))
        rarf.extractall(project_extract_path, members=filtered_members)
    else:
        rarf.extractall(project_extract_path)

    sys_command("extract (use_filter={}) {} ------> .... rarf.extractall .... {})".format(str(use_filtered_namelist), proj.filesystem_file_path, extract_destination_system_path))


def max_level(checkLevel, arrayLength):
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

    namelist_seperated = {
        "filteredmembers": None,
        "excludedmembers": None,
        "filtered_infolist": None,
        "ex_infolist": None
    }

    ex_infolist = list()

    checkLevel = 0

    if len(proj.rar_root_elements) == 1:
        # single root element
        if "Assets" in proj.rar_root_elements:
            print("Assets is rootElement, not filtering exclusions!!!")
            namelist_seperated["filteredmembers"] = rar_file.namelist()
            namelist_seperated["filtered_infolist"] = rar_file.infolist()

            for member in rar_file.infolist():
                member_is_root_element = is_rar_root_element(member.filename)
                # TODO: optimizable? 
                #if member.filename in proj.rar_root_elements:
                #    member_is_root_element = True
                ex_rar_info = ExtendedRarInfo(member.filename, member.date_time, member.file_size, member_is_root_element, True)
                ex_infolist.append(ex_rar_info)
            namelist_seperated["ex_infolist"] = ex_infolist
            
            return namelist_seperated
        else:
            # other rootElement (propably <UnityProjectName>)
            checkLevel = 1
            pass
    elif len(proj.rar_root_elements) > 1:
        # multiple root elements
        if "Assets" in proj.rar_root_elements:
            # Assets in root_elements found, filtering only in level 0
            checkLevel = 0
        else:
            # Assets NOT in root_elements found, filtering in level 1
            checkLevel = 1

    filteredmembers = list()
    excludedmembers = list()
    filtered_infolist = list()


    for member in rar_file.infolist():
        array = member.filename.split("\\")

        basepathOfMember = member.filename.split("\\")[max_level(checkLevel, len(array))]  # TODO fix/verify: Option 1 basedir extract with current filter, Option B second baseDir extract without filter. totalcommander to compare both base dir and delete similar files. check diff
        # print(basepathOfMember)
        if basepathOfMember in exclusions:
            if debug:
                print(f'excluded member: {member.filename}')
            excludedmembers.append(member.filename)
            will_be_extracted = False
        else:
            filtered_infolist.append(member)
            filteredmembers.append(member.filename)
            will_be_extracted = True
        
        member_is_root_element = is_rar_root_element(member.filename)
        #if member.filename in proj.rar_root_elements:
        #    member_is_root_element = True
        ex_rar_info = ExtendedRarInfo(member.filename, member.date_time, member.file_size, member_is_root_element, will_be_extracted)

        ex_infolist.append(ex_rar_info)

    # for i in excludedmembers:
    #     print(f'excluded: {i}')

    namelist_seperated["filteredmembers"] = filteredmembers
    namelist_seperated["excludedmembers"] = excludedmembers
    namelist_seperated["filtered_infolist"] = filtered_infolist
    namelist_seperated["ex_infolist"] = ex_infolist

    return namelist_seperated

def find_project_repo_level_crystal_quest(project_extraced_path):
    # impartant!
    # since we are recursive searching...
    # 
    # we are searching for the first occurence of the folder "Assets" - if there are more than one Assets folder .... only the first found is used as reference point
    # all project should contain it. in crystal quest rar-project-snapshots this is the case.
    result = recursive_search_assets_folder(project_extraced_path)

    if result is None:
        # Asset folder not found, use extracted root folder...
        print("{:<30} {}".format(str(project_extraced_path), "... ASSET-Folder NOT FOUND, use root as repo Level ..."))
        return Path(project_extraced_path)
    else:
        # Asset folder found
        return Path(result)


def recursive_search_assets_folder(system_path):
    # iterates (recursive) through all folders in system_path and searchs folder with name "Assets"
    # returns parent folder if found
    # returns root folder if not found
    # difference between path.absolut() path.resolve()  https://discuss.python.org/t/pathlib-absolute-vs-resolve/2573
    #                                                   https://stackoverflow.com/questions/42513056/how-to-get-absolute-path-of-a-pathlib-path-object
    # print("{:<30} {}".format(system_path_rar_files, "... loading ..."))
    parent_path = Path(system_path)
    print("{:<30} {}".format(str(parent_path), "... loading ..."))

    

    for entry in parent_path.iterdir():
        if entry.is_dir():
            print("{:<30}: {} {}".format(str(parent_path), "directory", entry.name))
            if entry.name == "Assets":
                # Asset folder found -> return partent_path
                print("{:<30}: {} {}".format(str(parent_path), "directory", entry.name))
                return system_path
            else:
                # not the Asset folder -> step into and search one level deeper
                result = recursive_search_assets_folder(str(entry))
                if result is None:
                    pass
                else:
                    # Asset Folder in subdirectory found
                    return result

    return None


def find_project_repo_level(project_extracted_path):
    # TODO find repoLevel in extracted project structure
    project_extracted_path = Path(project_extracted_path)
    print("find_project_repo_level in " + str(project_extracted_path))
    #print("find_project_repo_level in " + str(project_extracted_path.resolve()))
    # print(f'{project_extracted_path.name} - child elements: {len(project_extracted_path.iterdir())}')
    #directoryList = os.listdir(project_extracted_path.resolve())
    directoryList = os.listdir(project_extracted_path)

    # if RootElement is on of the string in valid array, we are in the repo Folder
    baseIsFirstLevel = ["Assets"]

    # if RootElement is on of the string in baseIsSecondLevel array, it is the repo Folder and we need to cd "change direction" on path deeper
    baseIsSecondLevel = ["SuperMarioWars", "SuperMarioWars_UnityNetwork", "SuperMarioWars 2015.04.08_1_Changes", "SuperMarioWars_clean", "Changes SuperMarioWars 2015.04.07_5 to 2015.04.10_3"]
    #baseIsSecondLevel = ["SMWCharacterImport"]

    # https://stackoverflow.com/questions/1388818/how-can-i-compare-two-lists-in-python-and-return-matches
    intersectResult = compare_intersect(directoryList, baseIsFirstLevel)

    print(intersectResult)
    if len(intersectResult) >= 1:
        return project_extracted_path
    else:

        intersectResult = compare_intersect(directoryList, baseIsSecondLevel)
        print(intersectResult)
        if len(intersectResult) >= 1:
            for entry in project_extracted_path.iterdir():
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
            return project_extracted_path

    return project_extracted_path
    # for entry in project_extracted_path.iterdir():
    #
    #     if(entry.is_dir())
    #         find_project_repo_level(entry)
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

    extract_target_root = Path(extract_destination_system_path)
    # check if folder exists, if not try to create it
    if not extract_target_root.exists():
        try:
            extract_target_root.mkdir(parents=True)
        except FileExistsError as exc:
            print(exc)
            exit()

    # check if folder is folder, if not exit
    if not extract_target_root.is_dir():
        print("ERROR: {:<50} ... is not a folder and exists".format(str(extract_target_root.resolve())))
        exit()
    else:
        #print("{:<50} ... is folder and exists".format(str(extract_target_root.resolve())))
        print("{:<50} ... is folder and exists".format(str(extract_target_root)))

    repo = any
    repo_existed = False

    try:
        repo = Repo(repo_system_path)
        repo_existed = True
    except NoSuchPathError as exc:
        print(exc)
    except InvalidGitRepositoryError as exc:
        print(exc)

    repoPath = Path(repo_system_path)
    if not repoPath.exists():
        repo_existed = False
        repoPath.mkdir(parents=True)

    if not repo_existed:                         # TODO git_repo_exists()
        print("repo didn't exists, create folder and init repo ...")
        repo = git_init_repo(repo_system_path)             # TODO git_init_repo

    if not Path(repo_system_path + "\\.gitignore").exists():
        message = "no .gitingore file found, continue? [yes/No]:"
        wait_for_input(message)

    if extract_target_root.exists() and extract_target_root.is_dir():
        print()
        print("Starting with workflow of {} projects...".format(len(projectList)))
        i = 0
        for p in projectList:

            i=i+1
            print()
            print(" {:<3}/{:<3} ... {:<50} ... extracting".format(i, len(projectList), p.filename))
            ## wait_for_input("continue? [yes/No]:")
            ## clean up
            ## clean up exclusion (incomplete project_snapshots)
            incomplete_project_snapshot = False
            incomplete_project_snapshot_filenames = ["SuperMarioWars 2014.09.27_13 CHANGES 11to13 Umzug Patrick Miriam.rar",
                                                    "SuperMarioWars 2015.04.08_1_Changes.rar",
                                                    "SuperMarioWars 2015.04.10_3 to 2015.04.07_5 Changes_ONLY.rar", 
                                                    # "Maps_v15.rar", 
                                                    "SuperMarioWars 2015.04.22_26-27 Between.rar"]
            if p.filename in incomplete_project_snapshot_filenames:
                incomplete_project_snapshot = True
            else:
                remove_all_project_files_from_repo(repo_system_path)  # delete previous project files

            extract_project(p, extract_destination_system_path)  # /projects/<rar-filename>/
            ## extract_destination_system_path
            ##  |
            ##  |-<rar filename of ProjectSnapshot 0>
            ##  |    |
            ##  |    |-<rarRootFolder>
            ##  |
            ##  |-<rar filename of ProjectSnapshot 1>
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

            sys_command("cd to extracted project folder")

            # TODO join extract_target_root.resolve() with p.filename to reach extractedPath
            # print(extract_destination_system_path)
            # if extract_target_root.exists():
            #       print(extract_target_root.resolve())
            #       print(str(extract_target_root))

            # extractedProjectSystemPath = str(extract_target_root)+"\\"+p.filename
            # extractedProjectSystemPath = extractedProjectSystemPath[:-4]   # remove .rar
            # print(extractedProjectSystemPath)

            project_extracted_path = Path(p.extraction_destination)
            print(f'{str(project_extracted_path)} exists? {project_extracted_path.exists()}')

            if project_extracted_path.exists():
                # analyseExtractedPath(project_extracted_path)
                # find root of repo
                # sub-level for repo
                
                if incomplete_project_snapshot:
                    project_extracted_path_repo_level = project_extracted_path
                else:
                    # crystal quest:
                    project_extracted_path_repo_level = find_project_repo_level_crystal_quest(project_extracted_path)

                    # other projects:
                    #project_extracted_path_repo_level = find_project_repo_level(project_extracted_path)

                p.extraction_destination_respective_repo_root_path = project_extracted_path_repo_level
                print("--- {:<50} : is repo base dir".format(str(project_extracted_path_repo_level)))


                # if is_rar_root_folder_repo_folder(p):
                #     sys_command("cd to extracted project folder sub directory")
                #     sys_command("move all files in cd .\\* to repo folder")
                # else:
                #     sys_command("move all files in cd .\\* to repo folder")

                # TODO move files to repo

                # Problem: moves complete directory!
                # shutil.move(str(p.extraction_destination_respective_repo_root_path.resolve()), repo_system_path)
                # Fix:
                for entry in p.extraction_destination_respective_repo_root_path.iterdir():
                    # print("move " + str(entry))
                    shutil.move(str(entry), repo_system_path)


                git_command("git add .")
                repo.git.add(A=True)        # same as git add .
                gitcmds.append("repo.git.add(A=True)")


                ##
                if repo.is_dirty(untracked_files=True):
                    print('is_dirty: Changes detected.')
                else:
                    print('NOT is_dirty')
                    
                    if i == 0:
                        # first rar file is empty or all files are ignored... or previousely created repo already contains current rar file
                        print(f"{p.filename} - first rar file is empty or all files are ignored... or previousely created repo already contains current rar file")
                    elif i > 1:
                        previouse_project = projectList[i-2]
                        pe_log=f"{previouse_project.filename} === {p.filename}"
                        print(pe_log)
                        projects_equal.append(pe_log)
                        projects_equal.append(previouse_project.filesystem_file_path)
                        projects_equal.append(p.filesystem_file_path)
                        projects_equal.append("")
                ##

                #filesystem_timestamp = datetime.datetime.fromtimestamp(p.filesystem_timestamp_modified).isoformat()
                filesystem_timestamp = p.filesystem_timestamp_modified_rfc2822

                commit_title = "{}".format(p.filename)  # TODO escape character, convert LF and RETURN to html code?
                commit_body = escape(p.long_description())    # TODO escape character, convert LF and RETURN to html code?
                # argument: --date = "Sat Nov 14 14:00 2015 +0100"
                #m_git_cmd = "--allow-empty -m '{}' -m '{}' --date='{}' ".format(commit_title, commit_body, filesystem_timestamp)
                m_git_cmd_parts = ['--allow-empty', '-m', f'"{commit_title}"', '--date', f'"{filesystem_timestamp}"']
                m_git_cmd = " ".join(m_git_cmd_parts)
                git_command(m_git_cmd)
                #print("filesystem_timestamp = " + filesystem_timestamp)
                #print('--allow-empty', '-m', f'"{commit_title}"', '-m', f'"{commit_title}"', '--date', f'"{filesystem_timestamp}"')
                #parts = ['--allow-empty', '-m', f'"{commit_title}"', '-m', f'"{commit_body}"', '--date', f'"{filesystem_timestamp}"']
                #gitcmds.append("repo.git.commit " + " ".join(parts))
                gitcmds.append("repo.git.commit (git commit) " + m_git_cmd)
                #repo.git.commit('--allow-empty', '-m', f'"{commit_title}"', '-m', f'"{commit_body}"', '--date', f'"{filesystem_timestamp}"')  # FIX --allow-empty (if rar files don't contain changes!)

                # set environment variables
                os.environ["GIT_AUTHOR_DATE"] = f'"{filesystem_timestamp}"'
                os.environ["GIT_COMMITTER_DATE"] = f'"{filesystem_timestamp}"'
                # git native
                repo.git.commit(m_git_cmd_parts)

                # gitpython command: (doesn't work with environment-variable commit date rfc 2822 format!...)
                #repo.index.commit(commit_title)

                #actor = Actor("Bob", "Bob@McTesterson.dev" )
                #repo.index.commit(commit_title, author=actor, committer=actor, commit_date=filesystem_timestamp)
                #commit_date_as_text = datetime.datetime.fromtimestamp(p.filesystem_timestamp_modified).strftime('%Y-%m-%d %H:%M:%S %z')
                #repo.index.commit(commit_title, author=actor, committer=actor, commit_date=commit_date_as_text)
                #repo.index.commit(commit_title, author=actor, committer=actor, commit_date=datetime.date(2020, 7, 21).strftime('%Y-%m-%d %H:%M:%S'))
                
                
        # remove_all_project_files_from_repo(repo_system_path)  # delete last project extracted files


def get_root_elements_and_newest_elements_from_rar_infolist(rar_info_list):
    # analyze the rarfile.infolist() list to find all root elements (files and folders)
    
    # Init
    root_elements = set()

    newest_rar_file = rarfile.RarInfo(unrarlib.RARHeaderDataEx())
    newest_rar_directory = rarfile.RarInfo(unrarlib.RARHeaderDataEx())

    for item in rar_info_list:

        # newest rar file/directory
        #
        splitted = item.filename.split("\\")
        filename_part = len(splitted)-1
        if "." in splitted[filename_part]:
            # File (not 100% )
            if newest_rar_file.date_time < item.date_time:
                newest_rar_file = item
        else:
            #Folder
            if newest_rar_directory.date_time < item.date_time:
                newest_rar_directory = item

        # root elements
        #
        # TODO TRY
        root_elements.add(item.filename.split("\\", 1)[0])
        #root_elements.add(item.split("\\")[0])
    
    print ("{:<120} (newest file)".format(newest_rar_file.filename))
    print ("{:<120} (newest directory)".format(newest_rar_directory.filename))

    results = {
        "root_elements": root_elements,
        "newest_rar_file": newest_rar_file,
        "newest_rar_directory": newest_rar_directory
        # "newest_rar_file_filename": newest_rar_file_filename,
        # "newest_rar_file_timestamp": newest_rar_file_timestamp,
        # "newest_rar_directory_filename": newest_rar_directory_filename,
        # "newest_rar_directory_timestamp": newest_rar_directory_timestamp
    }

    return results


def get_newest_elements_from_filtered_rar_infolist(rar_info_list):

    newest_rar_file = rarfile.RarInfo(unrarlib.RARHeaderDataEx())
    newest_rar_file.date_time = datetime.datetime(2011, 11, 11, 11, 11, 11, 11111).timetuple()
    newest_rar_directory = rarfile.RarInfo(unrarlib.RARHeaderDataEx())
    newest_rar_directory.date_time = datetime.datetime(2011, 11, 11, 11, 11, 11, 11111).timetuple()


    for item in rar_info_list:

        splitted = item.filename.split("\\")
        filename_part = len(splitted)-1
        if "." in splitted[filename_part]:
            # File (not 100% )
            if newest_rar_file.date_time < item.date_time:
                newest_rar_file = item
        else:
            #Folder
            if newest_rar_directory.date_time < item.date_time:
                newest_rar_directory = item

    
    print ("{:<120} (FILTERED: newest file)".format(newest_rar_file.filename))
    print ("{:<120} (FILTERED: newest directory)".format(newest_rar_directory.filename))

    results = {
        "newest_rar_file": newest_rar_file,
        "newest_rar_directory": newest_rar_directory
    }

    return results

def get_newest_timestamp_from_rar_content(project):
    # TODO:
    # finds latest modified file
    # returns date + time (+ filename?)
    rar = rarfile.RarFile(project.filesystem_file_path)
    
    # Init
    newest_rar_element = None
    if len(rar.infolist()) > 0:
        newest_rar_element = rar.infolist()[0]

    # Loop & Compare
    for e in rar.infolist():
        if newest_rar_element.date_time < e.date_time:
            newest_rar_element = e
    
    return newest_rar_element


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
    #print(ProjectSnapshotEncoder().encode(data))

    #print("Encode ProjectSnapshot Objects into JSON formatted Data using custom JSONEncoder")
    #dataJSONData = json.dumps(data, indent=4, cls=ProjectSnapshotEncoder)
    #print(dataJSONData)

    print("saving {} with {} elements".format(filename,len(data)))

    fullfilename = sanitize_filename(filename + ".json")
    with open(fullfilename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, cls=ProjectSnapshotEncoder, indent=4)

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
##  *   analyses and saves all get_root_elements_from_rar_namelist() for each rar file in project.rar_root_elements set/list
##  *   saves all root_elements in global_rar_root_elements (sumarization of all rar files)
##  *   prints root_elements
##  *   analyses rootDirectory @depricated !!!! BUG
##  *     prints available rar.getinfo() of rootDirectory
##
def analyze_rar_files(project_list, global_rar_root_elements, print_rar_content=False, print_rarinfo_properties_of_first_element_in_rar=False):
    for p in project_list:
        if rarfile.is_rarfile(p.filesystem_file_path):
            # is RAR File...
            p.rar_is_rar_file = True
            rar = rarfile.RarFile(p.filesystem_file_path)
            
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
            print("{:<30}: {}".format("p.filename", p.filename))
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
            root_elements = get_root_elements_and_newest_elements_from_rar_infolist(rar.infolist())
            p.rar_root_elements = root_elements
            print("{:<30}: {}".format("root_elements", len(p.rar_root_elements)))
            for el in p.rar_root_elements:
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
            #print(p.filesystem_file_path + " is not a RAR-File!")
            p.rar_is_rar_file = False

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
        p.say_state_one_line()
        if p.rar_is_rar_file:
            rar_files += 1 
        else:
            if show_non_rar_files:
                print(p.filesystem_file_path)
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
    # print_projects(app._project_list_load_via_pathlib)
    print()
    project_list_stats(app.projects, True)
    wait_for_input("app.projects, continue?")
    

def main_sort(projects):
    ##
    ## sort Projects
    ##
    sort_show_projects = False                # use to compare lists before and after sorting

    if sort_show_projects:
        print("projects (unsorted)")
        print_projects(projects)

    ###
    ### sort Projects: Method A (inline sorting)
    ###
    # app.projects.sort(key=operator.attrgetter('timestamp'))    # inline sorting

    ###
    ### sort Projects: Method B (sort copy)
    ###
    projects_sorted = sorted(projects, key=operator.attrgetter('filesystem_timestamp_modified'))  # sort copy
    
    if sort_show_projects:
        print("projects Sorted")
        print_projects(projects_sorted)
    
    return projects_sorted


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
            p = app.projects[i].filename                                    # project
            ps = app.projects_sorted[i].filename                            # project_sorted
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
    print_projects(app._project_list_loaded)
    wait_for_input("check loaded projects list [yes,no]:")


def main_visual_check_rar_root_elements(projects):
    ##
    ## show RAR content: root elements
    ##
    # projects = app._project_list_loaded
    print()
    print("show RAR content: root elements")
    
    num_of_rar_files = 0
    for p in projects:
        if p.rar_is_rar_file:
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
        if len(p.rar_root_elements) == 1:
            print("{:<130} {:<55} {}".format(p.filename, ", ".join(p.rar_root_elements), len(p.rar_root_elements)))
        elif len(p.rar_root_elements) > 1:
            print("{:<130} {:<55} {}".format(p.filename, "------------------------------------------------", len(p.rar_root_elements)))
            i = 0
            for e in p.rar_root_elements:
                i += 1
                print("{:<127} [{}] {:<55}".format("|>", i, e))
        else:
            print("{:<130} {:<55} {}".format(p.filename, ", ".join(p.rar_root_elements), len(p.rar_root_elements)))

    wait_for_input("check root elements [yes,no]:")


def main_visual_check_compare_sort_and_timestamps(projects):
    ##
    ## compare timestamps
    ## * timestamp:
    ##              extracted from filesystem (last modified date)
    ##              extracted from filename 
    ##              extracted from rar root elements
    ##              TODO: display last modified file from rar content
    ## * order (sorted by filesystem)
    ##
    # projects = app._project_list_loaded
    print()
    print(" ! IMPORTANT !")
    print(" ! please check timestamps, especially for !!! marked entries      !")
    print(" ! if fileName has a wrong nameing scheme, or maybe no date set,   !")
    print(" ! consider checking rar file content to get the modification date !")
    print(" ! IMPORTANT !")
    print("\\|/ \\|/ \\|/ \\|/ \\|/ \\|/ \\|/ \\|/ \\|/ \\|/ \\|/ \\|/ \\|/ \\|/")
    print()

    print("{:<25} {:<5} {:<20} {:<82} {}".format("\\|/ FileSystem \\|/", " ", "FileName", "Date from RARInfo of RAR root elements", "p.filename"))
    for p in projects:
        fileNameTimestamp = get_timestamp_from_filename(p.filename)
        # 2015.04.18

        # p.filesystem_timestamp_modified -> convert
        # CONVERT tutorial: https://timestamp.online/article/how-to-convert-timestamp-to-datetime-in-python
        ##filesystem_timestamp = datetime.datetime.fromtimestamp(p.filesystem_timestamp_modified).isoformat()
        ## ISO Format
        ## 2020-12-04T10:54:42+01:00
        #dtts = datetime(p.filesystem_timestamp_modified)
        #https://www.programiz.com/python-programming/datetime (Example 5: Get date from a timestamp)
        timestamp = datetime.date.fromtimestamp(p.filesystem_timestamp_modified)
        filesystem_timestamp = timestamp.strftime("%Y.%m.%d")

        compareresult = "NA"
        if fileNameTimestamp == filesystem_timestamp:
            compareresult = " = "
        else:
            compareresult = "!!!"
        print("{:<25} {:<5} {:<20}\\  {:<80} {}".format(filesystem_timestamp, compareresult, fileNameTimestamp, "", p.filename))

        # RAR content: newest file
        # TODO push analysation to beginning -> load_directory_list
        rar_content_newest_element = get_newest_timestamp_from_rar_content(p)
        
        if not rar_content_newest_element == None:

            date_str = rar_datetime_to_datestr(rar_content_newest_element.date_time)

            rar_content_newest_element_timestamp = date_str
            compareresult_rar_content = "NA"
            if rar_content_newest_element_timestamp == filesystem_timestamp:
                compareresult_rar_content = " = "
            else:
                compareresult_rar_content = "!!!"
            print("{:<25} {:<5} {:<10} RAR({}) - newest file".format("", compareresult_rar_content, rar_content_newest_element_timestamp, rar_content_newest_element.filename))

        # RAR content: root elements
        for timestamp_with_element_name in get_timestamp_from_rar_root_elements(p):
            print("{:<25} {:<5} {:<10} |-{:<80} {}".format( "", "", "", timestamp_with_element_name, "" ))

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


def database_reinit():
    database_drop_all()
    database_first_init()

def database_drop_all():
    app.Base.metadata.drop_all(app.engine)

def database_first_init():
    app.Base.metadata.create_all(app.engine)

def database_single_static_import():
    p1 = DB_ProjectSnapshot(
    filename = "SuperMarioWars 2015.04.14_2 Unity5_NetworkedPlayer_DataTweaks_part2_build0.711.rar",
    filename_project_name = "SuperMarioWars", 
    filename_timestamp = "2015.04.14",
    filename_additional_info = "_2 Unity5_NetworkedPlayer_DataTweaks_part2_build0.711.rar",
    filesystem_file_path = "R:\\SuperMarioWars\\SuperMarioWars 2015.04.14_2 Unity5_NetworkedPlayer_DataTweaks_part2_build0.711.rar",
    filesystem_timestamp_modified = "1429003281.2974927",
    filesystem_timestamp_modified_rfc2822 = "Tue, 14 Apr 2015 11:21:21 +0200",

    extraction_destination = "R:\\extractTest\\SuperMarioWars 2015.04.14_2 Unity5_NetworkedPlayer_DataTweaks_part2_build0.711",
    extraction_destination_respective_repo_root_path = "R:\\extractTest\\SuperMarioWars 2015.04.14_2 Unity5_NetworkedPlayer_DataTweaks_part2_build0.711\\SuperMarioWars_UnityNetwork")

    app.session.add(p1)
    app.session.commit()

def database_show_all():
    for row in app.session.query(DB_ProjectSnapshot,DB_ProjectSnapshot.filename).all():
        print(row.DB_ProjectSnapshot, row.filename)

def database_import(project_list):

    for p in project_list:

        item = DB_ProjectSnapshot(
            filename = p.filename,
            filename_project_name = p.filename_project_name, 
            filename_timestamp = p.filename_timestamp,
            filename_additional_info = p.filename_additional_info,

            filesystem_file_path = p.filesystem_file_path,
            filesystem_timestamp_modified = p.filesystem_timestamp_modified,
            filesystem_timestamp_modified_rfc2822 = p.filesystem_timestamp_modified_rfc2822,

            rar_content_newest_file_element = p._rar_content_newest_file_element,
            rar_content_newest_file_element_timestamp = rar_datetime_to_datestr(p._rar_content_newest_file_element_timestamp),
            rar_content_newest_directory_element = p._rar_content_newest_directory_element,
            rar_content_newest_directory_element_timestamp = rar_datetime_to_datestr(p._rar_content_newest_directory_element_timestamp),

            extraction_destination = p.extraction_destination,
            extraction_destination_respective_repo_root_path = p.extraction_destination_respective_repo_root_path)

        app.session.add(item)
        app.session.flush()
        # At this point, the object f has been pushed to the DB, 
        # and has been automatically assigned a unique primary key id
        app.session.refresh(item)
        # refresh updates given object in the session with its state in the DB
        # (and can also only refresh certain attributes - search for documentation)

        # item.id
        # is the automatically assigned primary key ID given in the database.
        #database_import_rar_content(p, item.id)
        database_import_rar_content_extended(p, item.id)

    app.session.commit()

def rar_datetime_to_datestr(rar_date_time):
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

    # dostime = unrarlib.dostime_to_timetuple(rar_date_time) # !!! NOT WORKING NEITHER !!!
    time_tuple = rar_date_time
    # print(time_tuple)
    dt_obj = datetime.datetime(*time_tuple[0:3])    # FIX: data in time_tuple[4:6] doesn't represent the correct time. need to investigate
    date_str = dt_obj.strftime("%Y.%m.%d")
    return date_str

def database_import_rar_content(p, p_id):
    '''
    source: rar.infolist()

    '''
    rar = rarfile.RarFile(p.filesystem_file_path)
    
    for rared_element in rar.infolist():

        date_str = rar_datetime_to_datestr(rared_element.date_time)

        db_item = DB_RAR_Content (
            id_rar_project = p_id,
            rar_filename = rared_element.filename,
            rar_date_time = date_str,
            rar_size_uncompressed = rared_element.file_size
        )

        app.session.add(db_item)


def database_import_rar_content_extended(p, p_id):
    '''
    source: project.rar_extended_infolist()

    '''
   
    for ex_rared_element in p.rar_extended_infolist:

        date_str = rar_datetime_to_datestr(ex_rared_element._date_time)

        db_item = DB_RAR_Content (
            id_rar_project = p_id,
            rar_filename = ex_rared_element._filename,
            rar_date_time = date_str,
            rar_size_uncompressed = ex_rared_element._file_size,
            cflag_is_root_element = ex_rared_element._is_root_element,
            cflag_will_be_extracted = ex_rared_element._will_be_extracted
        )

        app.session.add(db_item)


def test_is_rar_root_element(projects):
    print("test_is_rar_root_element")
    for p in projects:
        rar = rarfile.RarFile(p.filesystem_file_path)

        print(f"{p.filename}")
        for e in rar.namelist():
            if is_rar_root_element(e):
                # print(f"\t{e}is root element")
                print("\t{:<55} [root element]".format(e))
        print()
            

def export_loglist_to_file(log_list, log_filename):

    system_path_repo_building = app.system_path_repo + "\\" + app.system_path_repo_building
    folder_exists = False
    if not os.path.exists(system_path_repo_building):
        try:
            os.makedirs(system_path_repo_building)
            folder_exists = True
        except OSError as e:
            # if e.errno != errno.EEXIST:
            #     raise
            print(e)
    else:
        folder_exists = True

    if folder_exists:
        file_path = system_path_repo_building + "\\" + log_filename
        with open(file_path, "w") as text_file:
            #text_file.writelines(log_list)
            for cmd in log_list:
                text_file.write(f"{cmd}\n")
    
    # git add .
    # git commit .... building details (history & log)



# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    app = AppSettings()
    
    database_reinit()

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
    app.projects_sorted = main_sort(app.projects)

    ##
    ## Database creation and import
    ##
    database_import(app.projects_sorted)

    while input("FORCED STOP AFTER DB INIT (continue with 'y')") != "y":
        print("database created...")
        pass

    ##
    ## save 
    ##
    # main_save()   # (deactivated, files get to big since filtered extraction namelist is cached in projectsnapshot object)
    
    ##
    ## load
    ##
    # main_load()   # (deactivated, files get to big since filtered extraction namelist is cached in projectsnapshot object)

    ##
    ## show RAR content: root elements
    ##
    main_visual_check_rar_root_elements(app.projects_sorted)

    ##
    ## compare timestamps
    ##
    # main_visual_check_compare_sort_and_timestamps(app.projects_sorted) # deactivated for producton runs, TODO need optimization

    ##
    ##  Workflow
    ##       RAR Extraction
    ##       File Moving
    ##       git adding
    ##       git commiting
    ##
    wait_for_input("start workflow? [yes,no]:")

    while input("FORCED STOP BEFORE WORKFLOW STARTS (continue with 'y')") != "y":
        pass

    gitcmds = list()
    projects_equal = list()
    workflow(app.projects_sorted, app.system_path_extraction, app.system_path_repo)     

    print("gitcmds")
    for i in gitcmds:
        print(i)

    print("projects equal")
    for pe in projects_equal:
        print(pe)

    print("extraction_destination_respective_repo_root_path")
    for p in app.projects_sorted:
        print("\t path = " + str(p.extraction_destination_respective_repo_root_path))


    export_loglist_to_file(gitcmds,app.logfile_gitcmds)
    export_loglist_to_file(projects_equal,app.logfile_projects_with_identical_repo)
    


