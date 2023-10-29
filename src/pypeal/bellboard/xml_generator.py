from datetime import datetime

import xml.etree.ElementTree as ET

from pypeal.bellboard.interface import search_peals
from pypeal.bellboard.listener import PealGeneratorListener
from pypeal.peal import PealType

XML_NAMESPACE = '{http://bb.ringingworld.co.uk/NS/performances#}'


class XMLPealGenerator():

    def __init__(self, listener: PealGeneratorListener):
        self.__listener = listener

    def search(self, name: str):

        xml_response = search_peals(name)
        tree = ET.fromstring(xml_response)

        for performance in tree.findall(f'./{XML_NAMESPACE}performance'):

            # Yield the peal ID to allow caller to stop (e.g. for duplicates)
            peal_id: int = int(performance.attrib['id'][1:])
            if not (yield peal_id):
                continue

            self.__listener.new_peal(peal_id)
            self.__listener.association(get_element(performance, 'association')[1])
            if (place_element := get_element(performance, 'place')[0]) is not None:
                place = county = address_dedication = None
                self.__listener.tower(towerbase_id=int(place_element.attrib['towerbase-id']))
                for place_name_element in place_element.findall(f'{XML_NAMESPACE}place-name'):
                    match place_name_element.attrib['type']:
                        case 'place': place = place_name_element.text
                        case 'county': county = place_name_element.text
                        case 'dedication': address_dedication = place_name_element.text
                self.__listener.location(address_dedication, place, county)
                match get_element(place_element, 'ring', 'type')[1]:
                    case 'tower': self.__listener.type(PealType.TOWER)
                    case 'hand': self.__listener.type(PealType.HANDBELLS)
                self.__listener.tenor(get_element(place_element, 'ring', 'tenor')[1])
            if (title_element := get_element(performance, 'title')[0]) is not None:
                self.__listener.changes(int(get_element(title_element, 'changes')[1]))
                self.__listener.title(get_element(title_element, 'method')[1])
            self.__listener.method_details(get_element(performance, 'details')[1])
            self.__listener.composer(get_element(performance, 'composer')[1])
            self.__listener.date(datetime.strptime(performance.find(f'{XML_NAMESPACE}date').text, '%Y-%m-%d'))
            self.__listener.duration(get_element(title_element, 'duration')[1])
            if (ringer_element := get_element(performance, 'ringers')[0]) is not None:
                for ringer in ringer_element.findall(f'{XML_NAMESPACE}ringer'):
                    bells = None
                    if 'bell' in ringer.attrib and (bells := ringer.attrib['bell']) is not None:
                        bells = [int(bell) for bell in bells.split('-')]
                    self.__listener.ringer(ringer.text, bells, 'conductor' in ringer.attrib)
            for footnote in performance.findall(f'{XML_NAMESPACE}footnote'):
                self.__listener.footnote(footnote.text)


def get_element(parent: ET.Element, tag: str, attrib: str = None) -> tuple[ET.Element, str]:
    if (element := parent.find(f'{XML_NAMESPACE}{tag}')) is not None:
        return (element, element.text if attrib is None else element.attrib[attrib])
    else:
        return (None, None)
