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
TEXT_VAL_ATTR = 'text' #TODO: avoid replication here and in InputParams.py
ASSEMBLED_FILE_NAME = 'assembled.xml'


# Inputs
inputParams = InputParams(
    fileLevelNodes = {
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

def isFileLevelNode(node: ET.Element, inputParams: InputParams):
    return node.tag in inputParams.fileLevelNodes.keys()


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


        
        # if file level node or root note, build a directory
        
        if isFileLevelNode(node, inputParams) or node == xmlNode:
            nodeName = node.tag
            if isFileLevelNode(node, inputParams):
                nodeName = node.findtext(inputParams.fileLevelNodes[node.tag].nameXPath)
            
            state.pathList.append(f'{elementIdentifier}_{nodeName}')
            nodeDir = '/'.join(state.pathList)
            mkdir(nodeDir)

    def postOrderFunction(node: ET.Element, state: XmlDisassemblyTreeTraversalState):
        nodeDirPath = '/'.join(state.pathList)

        # remove children that are file level nodes (to avoid double printing)
        for n in [n for n in node if isFileLevelNode(n, inputParams)]:
            node.remove(n)

        # create a file for elements which are file-level nodes or the root element
        fileName = None
        if isFileLevelNode(node, inputParams) or node == xmlNode:
            fileName = state.pathList.pop()

        if fileName:
            ET.ElementTree(node).write(f'{nodeDirPath}/{fileName}.{XML_FILE_EXT}')

    state = XmlDisassemblyTreeTraversalState()
    state.pathList = [inputParams.outputDirectoryPath]
    state.counters = {}
    state.elementIdentifiers = {}

    xmlTreeTraversal(xmlNode, preOrderFunction, postOrderFunction, state)


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

    buildDisassembledDirectoryMetadataFile(inputParams)
    disassembleXmlElementToDirectoryStructure(tree.getroot(), inputParams)
    


def getInputParamsFromDisassembledDirectory(disassembledDirectoryPath: str):
    # directory should have a metadata file with FileName and Inputs used to make the files in the first place
    directoryMetadataFilePath = f'{disassembledDirectoryPath}/{DIR_METADATA_FILE_NAME}'
    metadataTree = ET.parse(directoryMetadataFilePath)
    inputParams = InputParams.fromXmlElement(metadataTree.getroot().find(INPUT_PARAMS_XML_TAG))
    return inputParams

def cleanPath(path: str):
    return os.path.normcase(os.path.normpath(path))


def dfsDirectoryTraversal(dirPath: str, preOrderFunction: callable, postOrderFunction: callable, state):
    
    cleanDirPath = cleanPath(dirPath)
    prev, current, stack = cleanDirPath, cleanDirPath, [cleanDirPath]
    
    while stack:
        current = stack[-1]
        subdirectoryEntries = [cleanPath(dirEntry) 
                               for dirEntry in os.scandir(current)
                               if dirEntry.is_dir()]

        # Childless Node
        if len(subdirectoryEntries) == 0:
            current = stack.pop()
            preOrderFunction(current, state)
            postOrderFunction(current, state)
            prev = current

        # Parent Node
        else:
            if prev in subdirectoryEntries:
                current = stack.pop()
                postOrderFunction(current, state)
                prev = current
            else:
                preOrderFunction(current, state)
                stack.extend(subdirectoryEntries)


class XmlAssemblyTreeTraversalState:
    def __init__(self):
        self.tree = None
        self.parentList = []

def assembleDisassembledDirectory(disassembledDirectoryPath: str):
    inputParams = getInputParamsFromDisassembledDirectory(disassembledDirectoryPath)
    subdirectoryEntries = [cleanPath(x) 
                           for x in os.scandir(disassembledDirectoryPath) 
                           if x.is_dir()]
    assert(len(subdirectoryEntries) == 1)
    rootElementDir = subdirectoryEntries[0]

    def preOrderFunction(currentDir: str, state):
        # Build XML Element from the Directory's file
        dirName = os.path.basename(currentDir)
        tag, num, name = dirName.split('_', 2)
        elementTree = ET.parse(f'{currentDir}/{dirName}.{XML_FILE_EXT}')
        element = elementTree.getroot()

        # Put XML Element as a child of the parent
        if state.tree == None:
            state.tree = elementTree
        else:
            state.parentList[-1].insert(int(num), element)
        state.parentList.append(element)

    def postOrderFunction(currentDir: str, state):
        state.parentList.pop()
        if len(state.parentList) == 0:
            assembledFilePath = f'{inputParams.outputDirectoryPath}/{ASSEMBLED_FILE_NAME}'
            state.tree.write(assembledFilePath)

    dfsDirectoryTraversal(rootElementDir, preOrderFunction, postOrderFunction, XmlAssemblyTreeTraversalState())


disassembleXmlFile(inputParams)
assembleDisassembledDirectory(inputParams.outputDirectoryPath)
# TODO: maintain consistency of <X /> vs <X></X> on empty tags
# TODO: allow tag-alphabetical re-assembly (while maintaining file-level tag order)
# TODO: Allow exact file output matching -- e.g., don't add xmlns:xmime if it wasn't there
# TODO: Allow option to maintain consistent output style across the files
# TODO: Enable forcing CDATA non-escaped where it was found in original file