class App:

    _main_wait_for_input = False

    _project_list_load_via_os = list()
    _project_list_load_via_pathlib = list()

    _file_list = list()

    _project_list_sorted = list()

    _project_list_loaded = list()

    _global_rar_root_elements = list()

    system_path_rar_files = "R:\\SMW-Test"
    system_path_repo = "R:\\repoTest"
    system_path_extraction = "R:\\extractTest"

    @property
    def projects_sorted(self):
        return self._project_list_sorted

    @projects_sorted.setter
    def projects_sorted(self, value):
        self._project_list_sorted = value

    @projects_sorted.deleter
    def projects_sorted(self):
        del self._project_list_sorted

    @property
    def projects(self):
        return self._project_list_load_via_os

    @projects.setter
    def projects(self, value):
        self._project_list_load_via_os = value

    @projects.deleter
    def projects(self):
        del self._project_list_load_via_os

    @property
    def files(self):
        return self._file_list

    @files.setter
    def files(self, value):
        self._file_list = value

    @files.deleter
    def files(self):
        del self._file_list


    def __init__(self):
        self.feature_use_filter_before_extraction = True
        self.feature_use_gitignore = True
        self.feature_use_readable_json_export = True

    def set_rar_directory_system_path(self, systempath):
        self.system_path_rar_files = systempath
        

    def set_repo_directory_system_path(self, systempath):
        self.system_path_repo = systempath


    def set_rar_extraction_directory_system_path(self, systempath):
        self.system_path_extraction = systempath
