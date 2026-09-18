import xml.etree.ElementTree as ET
from os import mkdir
import time
import os

from InputParams import InputParams, FileLevelNodeItem

### CONSTANTS ###

INPUT_PARAMS_XML_TAG = 'inputParams' #TODO: avoid replication here and in InputParams.py
METADATA_ROOT_XML_TAG = 'metadata'
XML_FILE_EXT = 'xml'
DIR_METADATA_FILE_NAME = f'metadata.{XML_FILE_EXT}'
METADATA_ROOT_TAG_XML_TAG = 'rootTag'
TEXT_VAL_ATTR = 'text' #TODO: avoid replication here and in InputParams.py
ASSEMBLED_FILE_NAME = 'assembled.xml'


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

def xmlTreeTraversal(root: ET.Element, preOrderFunction: callable, postOrderFunction: callable, state):
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
        elif len(state.pathList) == 1 and node == xmlNode:
            fileName = f'{state.elementIdentifiers[node]}'

        if fileName:
            ET.ElementTree(node).write(f'{nodeDirPath}/{fileName}.{XML_FILE_EXT}')

    state = XmlDisassemblyTreeTraversalState()
    state.pathList = [inputParams.outputDirectoryPath]
    state.counters = {}
    state.elementIdentifiers = {}

    xmlTreeTraversal(xmlNode, preOrderFunction, postOrderFunction, state)


def buildDisassembledDirectoryMetadataFile(inputParams: InputParams, rootXmlElement: ET.Element):
    metadataFilePath = f'{inputParams.outputDirectoryPath}/{DIR_METADATA_FILE_NAME}'
    metadataFileRootElement = ET.Element(METADATA_ROOT_XML_TAG)
    metadataFileRootElement.append(inputParams.asXmlElement())
    metadataFileRootElement.append(ET.Element(METADATA_ROOT_TAG_XML_TAG, {TEXT_VAL_ATTR: rootXmlElement.tag}))
    ET.ElementTree(metadataFileRootElement).write(metadataFilePath)


def disassembleXmlFile(inputParams: InputParams):
    tree = getXmlTreeFromFilePath(inputParams.inputFilePath)
    
    # create output file
    outputDirectoryPath = inputParams.outputDirectoryPath
    mkdir(outputDirectoryPath)

    buildDisassembledDirectoryMetadataFile(inputParams, tree.getroot())
    disassembleXmlElementToDirectoryStructure(tree.getroot(), inputParams)
    





''' TODO: Reassemble XML Files '''
def getInputParamsFromDisassembledDirectory(disassembledDirectoryPath: str):
    # directory should have a metadata file with FileName and Inputs used to make the files in the first place
    directoryMetadataFilePath = f'{disassembledDirectoryPath}/{DIR_METADATA_FILE_NAME}'
    metadataTree = ET.parse(directoryMetadataFilePath)
    inputParams = InputParams.fromXmlElement(metadataTree.getroot().find(INPUT_PARAMS_XML_TAG))
    return inputParams

def getRootTagFromDisassembledDirectory(disassembledDirectoryPath: str):
    # directory should have a metadata file with FileName and Inputs used to make the files in the first place
    directoryMetadataFilePath = f'{disassembledDirectoryPath}/{DIR_METADATA_FILE_NAME}'
    metadataTree = ET.parse(directoryMetadataFilePath)
    rootTag = metadataTree.find(METADATA_ROOT_TAG_XML_TAG).get(TEXT_VAL_ATTR)
    return rootTag


def cleanPath(path: str):
    return os.path.normcase(os.path.normpath(path))

def disassembledDirectoryTraversal(disassembledDirectoryPath: str, inputParams: InputParams, rootTag: str, preOrderFunction: callable, postOrderFunction: callable, state):

    prev, current, stack = cleanPath(disassembledDirectoryPath), cleanPath(disassembledDirectoryPath), [cleanPath(disassembledDirectoryPath)]
    
    while stack:
        current = stack[-1]

        # Determine what we're doing
        dirEntries = [x for x in os.scandir(current)]
        subdirectoryEntries = [cleanPath(x) for x in dirEntries if x.is_dir()]
        fileEntries = [cleanPath(x) for x in dirEntries if not x.is_dir()]

        # Childless Node
        if len(subdirectoryEntries) == 0:
            current = stack.pop()
            preOrderFunction(current, state)
            postOrderFunction(current, state)
            prev = current

        # Parent Node
        else:
            if any(x == prev for x in subdirectoryEntries):
                current = stack.pop()
                postOrderFunction(current, state)
                prev = current
            else:
                preOrderFunction(current, state)
                stack.extend(subdirectoryEntries)


def assembleDisassembledDirectory(disassembledDirectoryPath: str):
    inputParams = getInputParamsFromDisassembledDirectory(disassembledDirectoryPath)
    rootTag = getRootTagFromDisassembledDirectory(disassembledDirectoryPath)

    pass #TODO

    assembledFilePath = f'{inputParams.outputDirectoryPath}/{ASSEMBLED_FILE_NAME}'
    assembledTree = ET.parse(f'{inputParams.outputDirectoryPath}/{rootTag}_0.{XML_FILE_EXT}')
    assembledTree.write(assembledFilePath)

    def preOrderFunction(current: str, state):
        print('preOrder:', current)

    def postOrderFunction(current: str, state):
        print('postOrder:', current)

    disassembledDirectoryTraversal(disassembledDirectoryPath, inputParams, rootTag, preOrderFunction, postOrderFunction, None)



disassembleXmlFile(inputParams)
assembleDisassembledDirectory(inputParams.outputDirectoryPath)