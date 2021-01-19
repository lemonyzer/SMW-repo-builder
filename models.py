from sqlalchemy import Column, Integer, String
from appsettings import AppSettings
# from AppSettings import Base

class DB_ProjectSnapshot(AppSettings.Base):
    __tablename__ = "DB_ProjectSnapshot"
    id = Column(Integer, primary_key=True)

    filename = Column(String(254) )
    filename_project_name = Column(String(254) )
    filename_timestamp = Column(String(254) )
    filename_additional_info = Column(String(254) )

    filesystem_file_path = Column(String(254), unique=True)
    filesystem_timestamp_modified = Column(String(254), )
    filesystem_timestamp_modified_rfc2822 = Column(String(254), )

    # rar_is_rar_file = Column(String(254) )
    # rar_root_folder = Column(String(254) )
    # rar_root_elements = Column(String(254) )        1 zu n: -> eigene tabelle, root_elements aber auch in DB_RAR_Content analisierbar
    
    extraction_destination = Column(String(254) )
    extraction_destination_respective_repo_root_path = Column(String(254) )

    def __repr__(self):
        return f"DB_ProjectSnapshot('{self.id}', '{self.filename}', '{self.filename_timestamp}')"


# class DB_Filesystem(Model):
#     id = Column(Integer, primary_key=True)
#     file_timestamp = Column(String(254))
#     file_name = Column(String(254))
#     file_extension = Column(String(254))
#     file_full_path = Column(String(254))


class DB_RAR_Content(AppSettings.Base):
    __tablename__ = "DB_RAR_Content"
    id_rar_project = Column(Integer, primary_key=True)
    rar_filename = Column(String(254), primary_key=True)
    rar_date_time = Column(String(254))
    rar_size_uncompressed = Column(String(254))
    cflag_is_root_element = Column(String(254))
    cflag_will_be_extracted = Column(String(254))

    def __repr__(self):
        return f"DB_RAR_Content('{self.id_rar_project}', '{self.rar_filename}', '{self.rar_date_time}', '{self.rar_size_uncompressed}')"
