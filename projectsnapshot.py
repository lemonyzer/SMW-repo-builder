import deprecation
from json import JSONEncoder


class ExtendedRarInfo():
    _filename = ""
    _date_time = None
    _file_size = None
    _is_root_element = False
    _will_be_extracted = True

    def __init__(self, fn, dt, s, ire, wbe):
        self._filename=fn
        self._date_time=dt
        self._file_size=s
        self._is_root_element=ire
        self._will_be_extracted=wbe

    def __str__(self):
        return f"{self._filename} {self._is_root_element}"

class ProjectSnapshot:
    # SuperMarioWars 2014.06.05 UnityNetwork
    # SuperMarioWars 2015.04.05_2_Unity5_createPrefab_moreGenericWayV3_Works_Next_FullCharacterWithAnims

    _filename = ""
    _filename_timestamp = "0000.00.00"
    _filename_project_name = ""
    _filename_additional_info = ""

    _filesystem_file_path = 0
    _filesystem_timestamp_modified = 0
    _filesystem_timestamp_modified_rfc2822 = 0
    _filesystem_timestamp_created = 0
    _filesystem_timestamp_created_rfc2822 = 0

    _rar_is_rar_file = False
    _rar_root_elements = list()
    _rar_extended_infolist = None
    _rar_to_extract_namelist = list()
    _rar_not_to_extract_namelist = list()

    _rar_content_newest_file_element = None
    _rar_content_newest_file_element_timestamp = None
    _rar_content_newest_directory_element = None
    _rar_content_newest_directory_element_timestamp = None

    _extraction_destination = ""
    _extraction_destination_respective_repo_root_path = ""

    def __init__(self):
        pass


    @property
    def filesystem_timestamp_modified(self):
        return self._filesystem_timestamp_modified

    @filesystem_timestamp_modified.setter
    def filesystem_timestamp_modified(self, new_timestamp):
        # think about analysing filename and extractin addional information here???
        self._filesystem_timestamp_modified = new_timestamp


    @property
    def filesystem_timestamp_created(self):
        return self._filesystem_timestamp_created

    @filesystem_timestamp_created.setter
    def filesystem_timestamp_created(self, new_timestamp):
        # think about analysing filename and extractin addional information here???
        self._filesystem_timestamp_created = new_timestamp

 
    @property
    def filesystem_file_path(self):
        return self._filesystem_file_path

    @filesystem_file_path.setter
    def filesystem_file_path(self, value):
        # think about analysing filename and extractin addional information here???
        self._filesystem_file_path = value

 
    @property
    def filename(self):
        return self._filename

    @filename.setter
    def filename(self, value):
        self._filename = value
 
    @property
    def filename_timestamp(self):
        return self._filename_timestamp

    @filename_timestamp.setter
    def filename_timestamp(self, value):
        self._filename_timestamp = value


    @property
    def filename_project_name(self):
        return self._filename_project_name

    @filename_project_name.setter
    def filename_project_name(self, value):
        self._filename_project_name = value


    @property
    def filename_additional_info(self):
        return self._filename_additional_info

    @filename_additional_info.setter
    def filename_additional_info(self, value):
        self._filename_additional_info = value


    @property
    def rar_is_rar_file(self):
        return self._rar_is_rar_file

    @rar_is_rar_file.setter
    def rar_is_rar_file(self, value):
        self._rar_is_rar_file = value


    @property
    def rar_root_elements(self):
        return self._rar_root_elements

    @rar_root_elements.setter
    def rar_root_elements(self, new_set):
        self._rar_root_elements = set(new_set)

    @property
    def rar_extended_infolist(self):
        return self._rar_extended_infolist

    @rar_extended_infolist.setter
    def rar_extended_infolist(self, newlist):
        self._rar_extended_infolist = newlist
    
    @property
    def rar_to_extract_namelist(self):
        return self._rar_to_extract_namelist

    @rar_to_extract_namelist.setter
    def rar_to_extract_namelist(self, newlist):
        self._rar_to_extract_namelist = newlist

    @property
    def rar_not_to_extract_namelist(self):
        return self._rar_not_to_extract_namelist

    @rar_not_to_extract_namelist.setter
    def rar_not_to_extract_namelist(self, newlist):
        self._rar_not_to_extract_namelist = newlist
    

    @property
    def extraction_destination(self):
        return self._extraction_destination

    @extraction_destination.setter
    def extraction_destination(self, value):
        self._extraction_destination = value


    @property
    def extraction_destination_respective_repo_root_path(self):
        return self._extraction_destination_respective_repo_root_path

    @extraction_destination_respective_repo_root_path.setter
    def extraction_destination_respective_repo_root_path(self, value):
        self._extraction_destination_respective_repo_root_path = value



    def long_description(self):
        return self._filesystem_file_path + "\n" + self._filename_project_name + "\n" + str(
            self._filesystem_timestamp_modified) + "\n" + self._filename_additional_info

    def say_state_one_line(self):
        # print("{self._filename_project_name} {self._filesystem_timestamp_modified} {self._filename_additional_info} {self._filename}".format())
        print("{:<15} {:<10} {:<80} -- {}".format(self._filename_project_name, self._filesystem_timestamp_modified, self._filename_additional_info, self._filename))

    def say_state(self):
        print("{:<30}: {}".format("project name", self._filename_project_name))
        print("{:<30}: {}".format("timestamp (fs_mf)", self._filesystem_timestamp_modified))
        print("{:<30}: {}".format("additional inf", self._filename_additional_info))

    def __lt__(self, other):
        return self.filesystem_timestamp_modified < other.filesystem_timestamp_modified


# subclass JSONEncoder
class ProjectSnapshotEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, set):
            serial = list(o)
            return serial

        return o.__dict__
