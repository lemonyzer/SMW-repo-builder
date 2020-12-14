class Project:
    # SuperMarioWars 2014.06.05 UnityNetwork
    # SuperMarioWars 2015.04.05_2_Unity5_createPrefab_moreGenericWayV3_Works_Next_FullCharacterWithAnims

    def __init__(self, timestamp="1234.12.12", projName="projname", shortDescription="shortDscr", systemFilePath="", fileName=""):
        self.timestamp = timestamp
        self.name = projName
        self.shortDescription = shortDescription
        self.systemFilePath = systemFilePath
        self.fileName = fileName
        self.longDescription = systemFilePath + "\n" + projName + "\n" + str(timestamp) + "\n" + shortDescription
        self.israrfile = False
        self.rarRootFolder = ""

    def say_state(self):
        print("{:<30}: {}".format("timestamp", self.timestamp))
        print("{:<30}: {}".format("systemFilePath", self.systemFilePath))
        print("{:<30}: {}".format("shortDescription", self.shortDescription))
        print("{:<30}: {}".format("longDescription", self.longDescription))

    def setTimestamp(self, newTimestamp):
        self.timestamp = newTimestamp

    def __lt__(self, other):
        return self.timestamp < other.timestamp