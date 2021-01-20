-- check which files WILL NOT be extracted:

SELECT * FROM DB_RAR_Content WHERE 
cflag_will_be_extracted == "0" AND
rar_filename not like "SuperMarioWars\Library%" AND
rar_filename not like "SuperMarioWars_clean\Library%" AND
rar_filename not like "SuperMarioWars_UnityNetwork\Library%" AND
rar_filename not like "SuperMarioWars_UnityNetwork_Server_headless\Library%" AND
rar_filename not like "SuperMarioWars_UnityNetwork\Temp\%" --AND





-- check which files WILL BE extracted:

SELECT * FROM DB_RAR_Content WHERE 
--cflag_will_be_extracted == "1" AND
rar_filename like "%Library%" AND
rar_filename not like "%\Library\metadata%" AND
rar_filename not like "%\Library\ScriptAssemblies%" AND
rar_filename not like "%\Library\ShaderCache%" AND
rar_filename not like "%\Library\shadercompiler%" AND
-- 22 einzelne filter
rar_filename not like "%\Library\AnnotationManager" AND
rar_filename not like "%\Library\assetDatabase3" AND
rar_filename not like "%\Library\AssetImportState" AND
rar_filename not like "%\Library\AssetVersioning" AND
rar_filename not like "%\Library\AssetServerCacheV3" AND
rar_filename not like "%\Library\BuildPlayer.prefs" AND
rar_filename not like "%\Library\BuildSettings.asset" AND
rar_filename not like "%\Library\CurrentLayout.dwlt" AND
rar_filename not like "%\Library\EditorUserBuildSettings.asset" AND
rar_filename not like "%\Library\EditorUserSettings.asset" AND
rar_filename not like "%\Library\expandedItems" AND
rar_filename not like "%\Library\FailedAssetImports.txt" AND
rar_filename not like "%\Library\guidmapper" AND
rar_filename not like "%\Library\InspectorExpandedItems.asset" AND
rar_filename not like "%\Library\MonoManager.asset" AND
rar_filename not like "%\Library\ProjectSettings.asset" AND
rar_filename not like "%\Library\AssetVersioning.db" AND
rar_filename not like "%\Library\ScriptMapper" AND
rar_filename not like "%\Library\LibraryFormatVersion.txt" AND
rar_filename not like "%\Library\CurrentMaximizeLayout.dwlt" AND
rar_filename not like "%\Library\CrashedAssetImports.txt" AND
rar_filename not like "%\Library\LastSceneManagerSetup.txt"
ORDER BY rar_filename desc




-- alle Ordner mit namen Library (falls im Projekt selbst auch Ordner Library genannt wurden)
SELECT * FROM DB_RAR_Content WHERE 
rar_filename like "%\Library"
ORDER BY rar_date_time desc