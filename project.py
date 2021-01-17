import deprecation
from json import JSONEncoder
class Project:
    # SuperMarioWars 2014.06.05 UnityNetwork
    # SuperMarioWars 2015.04.05_2_Unity5_createPrefab_moreGenericWayV3_Works_Next_FullCharacterWithAnims

    def __init__(self, timestamp="0000.00.00", projName="projname", shortDescription="shortDscr", systemFilePath="", fileName=""):
        self.timestamp = timestamp
        self.name = projName
        self.shortDescription = shortDescription
        self.systemFilePath = systemFilePath
        self.fileName = fileName

        self.israrfile = False
        self.rootElements = set()
        self.extractPath = ""
        self.extractPathRepoBase = ""
        self.rfc2822 = ""

    def setRootElements(self, newSet):
        self.rootElements = newSet

    def getRootElements(self):
        return self.rootElements

    def longDescription(self):
        return self.systemFilePath + "\n" + self.name + "\n" + str(self.timestamp) + "\n" + self.shortDescription

    def say_state(self):
        print("{:<30}: {}".format("timestamp", self.timestamp))
        print("{:<30}: {}".format("systemFilePath", self.systemFilePath))
        print("{:<30}: {}".format("shortDescription", self.shortDescription))
        print("{:<30}: {}".format("longDescription", self.longDescription))

    def setTimestamp(self, newTimestamp):
        self.timestamp = newTimestamp

    def __lt__(self, other):
        return self.timestamp < other.timestamp


# subclass JSONEncoder
class ProjectEncoder(JSONEncoder):
    def default(self, o):
                
        if isinstance(o, set):
            serial = list(o)
            return serial

        return o.__dict__
