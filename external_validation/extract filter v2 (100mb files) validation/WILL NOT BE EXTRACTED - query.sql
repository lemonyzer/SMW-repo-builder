SELECT * FROM DB_RAR_Content WHERE 
cflag_will_be_extracted == "0" AND
rar_filename not like "SuperMarioWars\Library%" AND
rar_filename not like "SuperMarioWars_clean\Library%" AND
rar_filename not like "SuperMarioWars_UnityNetwork\Library%" AND
rar_filename not like "SuperMarioWars_UnityNetwork_Server_headless\Library%" AND
rar_filename not like "SuperMarioWars_UnityNetwork\Temp\%" --AND