import xml.etree.ElementTree as ET
from os import mkdir
import time

from InputParams import InputParams, FileLevelNodeItem

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
        if len(current) == 0 or prev == current[-1]:
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
            fileName = '_metadata'

        if fileName:
            ET.ElementTree(node).write(f'{nodeDirPath}/{fileName}.xml')

    state = XmlDisassemblyTreeTraversalState()
    state.pathList = [inputParams.outputDirectoryPath]
    state.counters = {}

    postOrderXmlTreeTraversal(xmlNode, preOrderFunction, postOrderFunction, state)


def disassembleXmlFile(inputParams: InputParams):
    tree = getXmlTreeFromFilePath(inputParams.inputFilePath)
    
    # create output file
    outputDirectoryPath = inputParams.outputDirectoryPath
    mkdir(outputDirectoryPath)

    disassembleXmlElementToDirectoryStructure(tree.getroot(), inputParams)
    buildDisassembledDirectoryMetadataFile(inputParams)





def buildDisassembledDirectoryMetadataFile(inputParams: InputParams):
    metadataFileName = 'metadata.xml'
    metadataFilePath = f'{inputParams.outputDirectoryPath}/{metadataFileName}'
    metadataFileRootElement = ET.Element('metadata')
    metadataFileRootElement.append(inputParams.asXmlElement())

    ET.ElementTree(metadataFileRootElement).write(metadataFilePath)




''' TODO: Reassemble XML Files '''
def assembleDisassembledDirectory(dissassembledDirectory):
    # directory should have a metadata file with FileName and Inputs used to make the files in the first place
    metadataFileName = f'{dissassembledDirectory}/metadata.xml'
    


disassembleXmlFile(inputParams)
