class Option:


    def __init__(self, rar_directory, extraction_directory, repo_directory):
        self.rar_directory_system_path = rar_directory
        self.rar_extraction_directory_system_path = extraction_directory
        self.repo_directory_system_path = repo_directory
        self.feature_use_filter_before_extraction = True
        self.feature_use_gitignore = True
        self.feature_use_readable_json_export = True
        

    def set_rar_directory_system_path(self, systempath):
        self.rar_directory_system_path = systempath
        

    def set_repo_directory_system_path(self, systempath):
        self.repo_directory_system_path = systempath


    def set_rar_extraction_directory_system_path(self, systempath):
        self.rar_extraction_directory_system_path = systempath
