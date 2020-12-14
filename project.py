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
        print("timestamp=\t\t\t{}".format(self.timestamp))
        print("systemFilePath=\t\t{}".format(self.systemFilePath))
        print("shortDescription=\t{}".format(self.shortDescription))
        print("longDescription=\t{}".format(self.longDescription))

    def setTimestamp(self, newTimestamp):
        self.timestamp = newTimestamp

    def __lt__(self, other):
        return self.timestamp < other.timestamp