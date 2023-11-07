from datetime import datetime
import xml.etree.ElementTree as ET

import pypeal.bellboard.interface


XML_NAMESPACE = '{http://bb.ringingworld.co.uk/NS/performances#}'


def search(name: str, date_from: datetime, date_to: datetime):

    page = 0
    found_peals = True
    while found_peals:

        found_peals = False
        page += 1
        xml_response = pypeal.bellboard.interface.search(name, date_from, date_to, page)
        tree = ET.fromstring(xml_response)

        for performance in tree.findall(f'./{XML_NAMESPACE}performance'):
            found_peals = True
            yield int(performance.attrib['href'].split('=')[1])
