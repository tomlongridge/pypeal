import os
from io import BytesIO
from urllib.request import urlopen
from zipfile import ZipFile
import xml.etree.ElementTree as ET


method_file_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'methods')

# with urlopen('https://methods.cccbr.org.uk/xml/CCCBR_methods.xml.zip') as zipresp:
#     with ZipFile(BytesIO(zipresp.read())) as zfile:
#         zfile.extractall(method_file_path)

tree = ET.parse(os.path.join(method_file_path, 'CCCBR_methods.xml'))


XML_NAMESPACE = '{http://www.cccbr.org.uk/methods/schemas/2007/05/methods}'
for method_set in tree.findall(f'./{XML_NAMESPACE}methodSet'):
    stage = method_set.find(f'{XML_NAMESPACE}properties/{XML_NAMESPACE}stage').text
    classification_element = method_set.find(f'{XML_NAMESPACE}properties/{XML_NAMESPACE}classification')
    classification = classification_element.text
    if classification == 'Hybrid':
        classification = None
    little = 'Little' if 'little' in classification_element.attrib else None
    differential = 'Differential' if 'differential' in classification_element.attrib else None
    for method in method_set.findall(f'{XML_NAMESPACE}method'):
        name = method.find(f'{XML_NAMESPACE}name').text
        print(f'{(name + " ") if name else ""}{(differential + " ") if differential else ""}{(little + " ") if little else ""}{(classification + " ") if classification else ""}{stage}')
