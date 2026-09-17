import xml.etree.ElementTree as ET


### Constants ###
INPUT_PARAMS_XML_TAG = 'inputParams'

INPUT_FILE_PATH_XML_TAG = 'inputFilePath'
OUTPUT_DIR_PATH_XML_TAG = 'outputDirectoryPath'
VALUE_TEXT_ATTR = 'text'

FILE_LEVEL_NODE_ITEM_XML_TAG = 'fileLevelNodeItem'
FILE_LEVEL_NODE_ITEM_TAG_ATTR = 'tag'
FILE_LEVEL_NODE_ITEM_NAMEXPATH_ATTR = 'nameXPath'
FILE_LEVEL_NODE_LIST_XML_TAG = 'fileLevelNodes'


class FileLevelNodeItem:

    def __init__(self, tag: str, nameXPath: str):
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
    
    @classmethod
    def fromXmlElement(cls, xmlElement: ET.Element):
        tag = xmlElement.get(FILE_LEVEL_NODE_ITEM_TAG_ATTR)
        nameXPath = xmlElement.get(FILE_LEVEL_NODE_ITEM_NAMEXPATH_ATTR)
        return FileLevelNodeItem(tag, nameXPath)
    

class InputParams:
    def __init__(self, fileLevelNodes: dict = {}, inputFilePath: str = '', outputDirectoryPath: str = ''):
        self.fileLevelNodes = fileLevelNodes
        self.inputFilePath = inputFilePath
        self.outputDirectoryPath = outputDirectoryPath

    @classmethod
    def fromXmlElement(cls, xmlElement: ET.Element):
        fileLevelNodes = {n.tag: FileLevelNodeItem.fromXmlElement(n) for n in xmlElement.findall(FILE_LEVEL_NODE_LIST_XML_TAG)}
        inputFilePath = xmlElement.find(INPUT_FILE_PATH_XML_TAG).get(VALUE_TEXT_ATTR)
        outputDirectoryPath = xmlElement.find(OUTPUT_DIR_PATH_XML_TAG).get(VALUE_TEXT_ATTR)
        return InputParams(fileLevelNodes, inputFilePath, outputDirectoryPath) 

    def asXmlElement(self):
        inputParamsRootElement = ET.Element(INPUT_PARAMS_XML_TAG)

        fileLevelNodesElement = ET.Element(FILE_LEVEL_NODE_LIST_XML_TAG)
        fileLevelNodesElement.extend(item.asXmlElement() for item in self.fileLevelNodes.values())
        inputParamsRootElement.append(fileLevelNodesElement)

        inputParamsRootElement.append(ET.Element(INPUT_FILE_PATH_XML_TAG, {VALUE_TEXT_ATTR: self.inputFilePath}))
        inputParamsRootElement.append(ET.Element(OUTPUT_DIR_PATH_XML_TAG, {VALUE_TEXT_ATTR: self.outputDirectoryPath}))
        return inputParamsRootElement