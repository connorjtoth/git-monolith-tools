import xml.etree.ElementTree as ET

class XmlSerializable:
    def __init__(self):
        pass

    def asXmlElement(self):
        element = ET.Element(self.__class__.__name__)
        for key, value in vars(self).items():
            if isinstance(value, list):
                listElement = ET.Element(key)
                element.append(listElement)
                for item in value:
                    listElement.append(item.asXmlElement())
            elif isinstance(value, XmlSerializable):
                element.append(value.asXmlElement())
            elif isinstance(value, bool):
                element.set(key, str(value))
            else:
                element.set(key, value)
        return element

    @classmethod
    def fromXmlElement(cls, xmlElement: ET.Element):
        returnObj = cls()
        for k in vars(returnObj).keys():
            if xmlElement.get(k):
                value = xmlElement.get(k)
                if value in ('True', 'False'):
                    value = (value == 'True')
                returnObj.__setattr__(k, value)
            elif xmlElement.find(k):
                listElement = xmlElement.find(k)
                list = []

                if len(listElement) > 0:
                    listTypeClass = XmlSerializable.findSubclassByName(listElement[0].tag)
                    assert(listTypeClass != None)
                    list.extend(listTypeClass.fromXmlElement(item) for item in listElement)
                
                returnObj.__setattr__(k, list)
        return returnObj

    @staticmethod
    def findSubclassByName(searchName: str):
        subclasses = [XmlSerializable]
        while subclasses:
            for sc in subclasses:
                if sc.__name__ == searchName:
                    return sc

            subclasses = [new for old in subclasses for new in old.__subclasses__()]

        return None