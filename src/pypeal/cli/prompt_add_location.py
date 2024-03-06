import re
from pypeal.cli.prompt_add_tower import prompt_find_tower
from pypeal.cli.prompts import ask, confirm, error
from pypeal.cli.chooser import choose_option
from pypeal.entities.peal import Peal

DEDICATION_REGEX = re.compile(r'^st?\s|cath|blessed|holy|all saints|chapel|christ|abbey|our lady|our blessed')


def prompt_add_location(address_dedication: str, place: str, county: str, country: str, peal: Peal, quick_mode: bool):

    if not quick_mode:
        full_location = ''
        full_location += f', {address_dedication} ' if address_dedication else ''
        full_location += f', {place}' if place else ''
        full_location += f', {county}' if county else ''
        full_location += f', {country}' if country else ''
        full_location = full_location.strip(', ')

        if confirm(f'Location: {full_location}', confirm_message='Attempt to find a tower?', default=False):
            selected_tower = prompt_find_tower()
            if selected_tower:
                peal.ring = selected_tower.get_active_ring(peal.date)
                return

    while True:

        probably_dedication = address_dedication and re.match(DEDICATION_REGEX, address_dedication.lower()) is not None

        address_dedication_less_sub_place = None
        sub_place = None
        if address_dedication is not None:
            place_parts = address_dedication.split(', ')
            if len(place_parts) > 1:
                sub_place = place_parts.pop()
                address_dedication_less_sub_place = ', '.join(place_parts)

        dedication = address = None
        if probably_dedication and \
                (quick_mode or confirm(f'"{address_dedication_less_sub_place}" looks like the tower dedication')):
            dedication = address_dedication
        else:
            while True:
                if not address_dedication or not quick_mode:
                    address = ask('Address', address_dedication, required=False)
                else:
                    address = address_dedication
                if address and \
                        (not re.match(DEDICATION_REGEX, address.lower()) or
                            confirm(f'"{address}" looks like a dedication', confirm_message='Are you sure?')):
                    sub_place = None
                    break
                if not address_dedication or not quick_mode:
                    dedication = ask('Dedication', address_dedication, required=False)
                else:
                    dedication = address_dedication
                if dedication and \
                        (re.match(DEDICATION_REGEX, dedication.lower()) or
                            confirm(f'"{dedication}" does not look like a dedication', confirm_message='Are you sure?')):
                    break
                error('Please enter a dedication or address')
                quick_mode = False  # Go into prompt mode as the input doesn't look like a dedication or address

        peal.dedication = dedication
        peal.address = address

        peal.place = ask('Place', place) if not quick_mode else place

        if sub_place:
            match choose_option([sub_place, 'None', 'Other'], default=1, title='Sub-place/area') if not quick_mode else 1:
                case 1:
                    peal.sub_place = sub_place
                case 2:
                    peal.sub_place = None
                case 3:
                    peal.sub_place = ask('Sub-place/area')
        elif not quick_mode:
            peal.sub_place = ask('Sub-place/area', required=False)

        if country is None and county is not None:
            county_parts = county.split(', ')
            if len(county_parts) > 1:
                country = county_parts.pop()
                county = ', '.join(county_parts)
        peal.county = ask('County/state', county) if not quick_mode else county
        peal.country = ask('Country', country) if not quick_mode else country

        if quick_mode or confirm(peal.location):
            return
