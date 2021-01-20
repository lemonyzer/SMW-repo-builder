// PowerQuery
let
    Quelle = Csv.Document(File.Contents("R:\validate_date_time_export.csv"),[Delimiter=",", Columns=5, Encoding=1252, QuoteStyle=QuoteStyle.None]),
    #"Höher gestufte Header" = Table.PromoteHeaders(Quelle, [PromoteAllScalars=true]),
    #"Geänderter Typ" = Table.TransformColumnTypes(#"Höher gestufte Header",{{"filename_timestamp", type text}, {"second_from_1970", type text}, {"utc_to_localtime_second_from_1970", type text}, {"rar_content_newest_directory_element_timestamp", type text}, {"rar_content_newest_file_element_timestamp", type text}}),
    #"Ersetzter Wert" = Table.ReplaceValue(#"Geänderter Typ","-",".",Replacer.ReplaceText,{"second_from_1970"}),
    #"Ersetzter Wert1" = Table.ReplaceValue(#"Ersetzter Wert","-",".",Replacer.ReplaceText,{"utc_to_localtime_second_from_1970"}),
    #"Extrahierte erste Zeichen" = Table.TransformColumns(#"Ersetzter Wert1", {{"second_from_1970", each Text.Start(_, 10), type text}}),
    #"Extrahierte erste Zeichen1" = Table.TransformColumns(#"Extrahierte erste Zeichen", {{"utc_to_localtime_second_from_1970", each Text.Start(_, 10), type text}}),
    #"Hinzugefügte benutzerdefinierte Spalte" = Table.AddColumn(#"Extrahierte erste Zeichen1", "Benutzerdefiniert", each if [filename_timestamp] = [second_from_1970] then "=" else "!!!"),
    #"Neu angeordnete Spalten" = Table.ReorderColumns(#"Hinzugefügte benutzerdefinierte Spalte",{"filename_timestamp", "Benutzerdefiniert", "second_from_1970", "utc_to_localtime_second_from_1970", "rar_content_newest_directory_element_timestamp", "rar_content_newest_file_element_timestamp"}),
    #"Hinzugefügte benutzerdefinierte Spalte1" = Table.AddColumn(#"Neu angeordnete Spalten", "Benutzerdefiniert.1", each Number.FromText(Text.End([filename_timestamp],2))-Number.FromText(Text.End([second_from_1970],2))),
    #"Ersetzte Fehler" = Table.ReplaceErrorValues(#"Hinzugefügte benutzerdefinierte Spalte1", {{"Benutzerdefiniert.1", 100}}),
    #"Neu angeordnete Spalten1" = Table.ReorderColumns(#"Ersetzte Fehler",{"filename_timestamp", "Benutzerdefiniert.1", "Benutzerdefiniert", "second_from_1970", "utc_to_localtime_second_from_1970", "rar_content_newest_directory_element_timestamp", "rar_content_newest_file_element_timestamp"}),
    #"Gefilterte Zeilen" = Table.SelectRows(#"Neu angeordnete Spalten1", each ([Benutzerdefiniert.1] <> 0)),
    #"Hinzugefügte benutzerdefinierte Spalte2" = Table.AddColumn(#"Gefilterte Zeilen", "Benutzerdefiniert.2", each Number.FromText(Text.End([rar_content_newest_file_element_timestamp],2))-Number.FromText(Text.End([second_from_1970],2))),
    #"Neu angeordnete Spalten2" = Table.ReorderColumns(#"Hinzugefügte benutzerdefinierte Spalte2",{"filename_timestamp", "Benutzerdefiniert.1", "Benutzerdefiniert", "second_from_1970", "utc_to_localtime_second_from_1970", "Benutzerdefiniert.2", "rar_content_newest_directory_element_timestamp", "rar_content_newest_file_element_timestamp"}),
    #"Gefilterte Zeilen1" = Table.SelectRows(#"Neu angeordnete Spalten2", each ([Benutzerdefiniert.2] = 1))
in
    #"Gefilterte Zeilen1"