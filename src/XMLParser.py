import xml.etree.ElementTree as ET
from os import mkdir
import time

from InputParams import InputParams, FileLevelNodeItem

### CONSTANTS ###

INPUT_PARAMS_XML_TAG = 'inputParams' #TODO: avoid replication here and in InputParams.py
METADATA_ROOT_XML_TAG = 'metadata'
XML_FILE_EXT = 'xml'
DIR_METADATA_FILE_NAME = 'metadata' + XML_FILE_EXT


# Inputs
inputParams = InputParams(
    fileLevelNodes = {
        #    FileLevelNodeItem('Item', getNodelambda node: node.findtext("Properties/string[@name='Name']"))
        'Item': FileLevelNodeItem('Item', "Properties/string[@name='Name']")
    },
    inputFilePath = 'input/SmallFile.xml',
    outputDirectoryPath = f'output/out_{time.time()}'
)

#--- CLASSES ---
class XmlDisassemblyTreeTraversalState:
    def __init__(self):
        self.pathList = []
        self.counters = {}
        self.elementIdentifiers = {}

#--- HELPERS ---
def getXmlTreeFromFilePath(xmlFilePath: str) -> ET.ElementTree:
    return ET.parse(xmlFilePath)

def getXmlTreeParentMap(xmlTree: ET.ElementTree) -> dict:
    parentMap = {c: p for p in xmlTree.iter() for c in p}
    parentMap[xmlTree.getroot()] = None
    return parentMap

def postOrderXmlTreeTraversal(root: ET.Element, preOrderFunction: callable, postOrderFunction: callable, state):
    prev, current, stack = root, root, [root]

    while stack:
        current = stack[-1]

        # Childless Node
        if len(current) == 0:
            current = stack.pop()
            preOrderFunction(current, state)
            postOrderFunction(current, state)
            prev = current

        # Parent Node
        else:
            if prev == current[-1]:
                current = stack.pop()
                postOrderFunction(current, state)
                prev = current
            else:
                preOrderFunction(current, state)
                stack.extend(reversed(current))

def disassembleXmlElementToDirectoryStructure(xmlNode: ET.Element, inputParams: InputParams):

    def preOrderFunction(node: ET.Element, state: XmlDisassemblyTreeTraversalState):
        # assign tag number to this element
        tagNum = state.counters.get(node.tag, 0)
        state.counters[node.tag] = tagNum + 1
        elementIdentifier = f'{node.tag}_{tagNum}'
        state.elementIdentifiers[node] = elementIdentifier

        # if file level node, build a directory
        if node.tag in inputParams.fileLevelNodes.keys():
            nodeName = node.findtext(inputParams.fileLevelNodes[node.tag].nameXPath)
            state.pathList.append(f'{elementIdentifier}_{nodeName}')
            nodeDir = '/'.join(state.pathList)
            mkdir(nodeDir)

    def postOrderFunction(node: ET.Element, state: XmlDisassemblyTreeTraversalState):
        nodeDirPath = '/'.join(state.pathList)

        # remove children that are file level nodes (to avoid double printing)
        for n in [n for n in node if n.tag in inputParams.fileLevelNodes.keys()]:
            node.remove(n)

        # create a file for elements which are not file-level nodes or their descendants
        # avoid creating a file for elements which are descendants of file level nodes
        fileName = None
        if node.tag in inputParams.fileLevelNodes.keys():
            fileName = state.pathList.pop()
        elif len(state.pathList) == 1:
            fileName = f'{state.elementIdentifiers[node]}'

        if fileName:
            ET.ElementTree(node).write(f'{nodeDirPath}/{fileName}.{XML_FILE_EXT}')

    state = XmlDisassemblyTreeTraversalState()
    state.pathList = [inputParams.outputDirectoryPath]
    state.counters = {}
    state.elementIdentifiers = {}

    postOrderXmlTreeTraversal(xmlNode, preOrderFunction, postOrderFunction, state)


def buildDisassembledDirectoryMetadataFile(inputParams: InputParams):
    metadataFilePath = f'{inputParams.outputDirectoryPath}/{DIR_METADATA_FILE_NAME}'
    metadataFileRootElement = ET.Element(METADATA_ROOT_XML_TAG)
    metadataFileRootElement.append(inputParams.asXmlElement())

    ET.ElementTree(metadataFileRootElement).write(metadataFilePath)


def disassembleXmlFile(inputParams: InputParams):
    tree = getXmlTreeFromFilePath(inputParams.inputFilePath)
    
    # create output file
    outputDirectoryPath = inputParams.outputDirectoryPath
    mkdir(outputDirectoryPath)

    disassembleXmlElementToDirectoryStructure(tree.getroot(), inputParams)
    buildDisassembledDirectoryMetadataFile(inputParams)





''' TODO: Reassemble XML Files '''
def getInputParamsFromDisassembledDirectory(disassembledDirectoryPath: str):
    # directory should have a metadata file with FileName and Inputs used to make the files in the first place
    directoryMetadataFilePath = f'{disassembledDirectoryPath}/{DIR_METADATA_FILE_NAME}'
    metadataTree = ET.parse(directoryMetadataFilePath)
    inputParams = InputParams.fromXmlElement(metadataTree.getroot().find(INPUT_PARAMS_XML_TAG))
    return inputParams

def assembleDisassembledDirectory(disassembledDirectoryPath):
    inputParams = getInputParamsFromDisassembledDirectory(disassembledDirectoryPath)
    pass #TODO



disassembleXmlFile(inputParams)
assembleDisassembledDirectory(inputParams.outputDirectoryPath)