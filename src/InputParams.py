import xml.etree.ElementTree as ET
from XmlSerializable import XmlSerializable

### Constants ###

class FileLevelNodeItem(XmlSerializable):
    def __init__(self, tag: str = '', nameXPath: str = ''):
        super().__init__()
        self.tag: str = tag
        self.nameXPath: str = nameXPath
        #TODO: Allow to serialize custom functions as getNodeNameFunctions


class InputParams(XmlSerializable):
    def __init__(self):
        self.fileLevelNodes: list[FileLevelNodeItem] = []
        self.inputFilePath: str = ''
        self.outputDirectoryPath: str = ''
        self.outputShortEmptyElements: bool = True
        self.indentDelimiter = '  '

    def getFileLevelNodeTags(self):
        return [item.tag for item in self.fileLevelNodes]

    def getFileLevelNodeByTag(self, tag: str):
        return [x for x in self.fileLevelNodes if x.tag == tag][0]

