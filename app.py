class App:

    projects_load_via_os = list()
    projects_load_via_pathlib = list()
    files = list()

    system_path_rar_files = "R:\\SMW-Test"
    system_path_repo = "R:\\repoTest"
    system_path_extraction = "R:\\extractTest"

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
