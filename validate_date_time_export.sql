-- DB Browser for SQLite
SELECT 
filename_timestamp, 
datetime(filesystem_timestamp_modified, 'unixepoch') as second_from_1970,
datetime(filesystem_timestamp_modified, 'unixepoch', 'localtime') as utc_to_localtime_second_from_1970,
rar_content_newest_directory_element_timestamp,
rar_content_newest_file_element_timestamp
FROM DB_ProjectSnapshot
ORDER BY filesystem_timestamp_modified asc