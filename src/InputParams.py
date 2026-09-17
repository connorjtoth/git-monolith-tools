import xml.etree.ElementTree as ET


### Constants ###
INPUT_PARAMS_XML_TAG = 'inputParams'

INPUT_FILE_PATH_XML_TAG = 'inputFilePath'
OUTPUT_DIR_PATH_XML_TAG = 'outputDirectoryPath'

FILE_LEVEL_NODE_ITEM_XML_TAG = 'fileLevelNodeItem'
FILE_LEVEL_NODE_ITEM_TAG_ATTR = 'tag'
FILE_LEVEL_NODE_ITEM_NAMEXPATH_ATTR = 'nameXPath'
FILE_LEVEL_NODE_LIST_XML_TAG = 'fileLevelNodes'


class FileLevelNodeItem:
    def __init__(self, tag, nameXPath):
        self.tag = tag
        self.nameXPath = nameXPath
        #self.getNodeNameFunction = nodeNameFn
        #TODO: Allow to serialize custom functions as getNodeNameFunctions

    def asXmlElement(self):
        attribs = {
            FILE_LEVEL_NODE_ITEM_TAG_ATTR: self.tag,
            FILE_LEVEL_NODE_ITEM_NAMEXPATH_ATTR: self.nameXPath
        }
        element = ET.Element(FILE_LEVEL_NODE_ITEM_XML_TAG, attribs)
        #element.text = self.getNodeNameFunction
        return element


class InputParams:
    def __init__(self, fileLevelNodes={}, inputFilePath='', outputDirectoryPath=''):
        self.fileLevelNodes = fileLevelNodes
        self.inputFilePath = inputFilePath
        self.outputDirectoryPath = outputDirectoryPath

    def asXmlElement(self):
        inputParamsRootElement = ET.Element(INPUT_PARAMS_XML_TAG)

        fileLevelNodesElement = ET.Element(FILE_LEVEL_NODE_LIST_XML_TAG)
        fileLevelNodesElement.extend(item.asXmlElement() for item in self.fileLevelNodes.values())
        inputParamsRootElement.append(fileLevelNodesElement)

        inputParamsRootElement.append(ET.Element(INPUT_FILE_PATH_XML_TAG, text=self.inputFilePath))
        inputParamsRootElement.append(ET.Element(OUTPUT_DIR_PATH_XML_TAG, text=self.outputDirectoryPath))
        return inputParamsRootElement


    def fromXmlElement(self, xmlElement):
        pass
        #TODO