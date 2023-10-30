import re
from pypeal.cli.prompts import ask, confirm, choose_option
from pypeal.peal import Peal

DEDICATION_REGEX = re.compile(r'^st?\s|cath|blessed|holy|all saints|chapel|christ|abbey|our lady|our blessed')


def prompt_add_location(address_dedication: str, place: str, county: str, peal: Peal):

    while True:
        probably_dedication = re.match(DEDICATION_REGEX, address_dedication.lower()) is not None

        sub_place = None
        address_dedication_less_sub_place = None
        if address_dedication is not None:
            place_parts = address_dedication.split(', ')
            if len(place_parts) > 1:
                sub_place = place_parts.pop()
                address_dedication_less_sub_place = ', '.join(place_parts)

        dedication = address = None
        if probably_dedication and confirm(f'"{address_dedication_less_sub_place}" looks like the tower dedication'):
            dedication = address_dedication
        else:
            while True:
                address = ask('Address', address_dedication, required=False)
                if address and \
                        not re.match(DEDICATION_REGEX, address.lower()) or \
                        confirm(f'"{address}" looks like a dedication', confirm_message='Are you sure?'):
                    sub_place = None
                    break
                dedication = ask('Dedication', address_dedication, required=False)
                if dedication and \
                        re.match(DEDICATION_REGEX, dedication.lower()) or \
                        confirm(f'"{dedication}" does not look like a dedication', prompt='Are you sure?'):
                    break

        peal.dedication = dedication
        peal.address = address

        peal.place = ask('Place', place)

        if sub_place:
            match choose_option([sub_place, 'None', 'Other'], default=1, prompt='Sub-place/area'):
                case 1:
                    peal.sub_place = sub_place
                case 2:
                    peal.sub_place = None
                case 3:
                    peal.sub_place = ask('Sub-place/area')
        else:
            peal.sub_place = ask('Sub-place/area', required=False)

        country = None
        if county is not None:
            county_parts = county.split(', ')
            if len(county_parts) > 1:
                country = county_parts.pop()
                county = ', '.join(county_parts)
        peal.county = ask('County/state', county)
        peal.country = ask('Country', country)

        if confirm(peal.location):
            return peal
