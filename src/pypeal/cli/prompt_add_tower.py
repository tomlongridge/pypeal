from pypeal.cli.chooser import choose_option
from pypeal.cli.prompts import ask, ask_int, confirm
from pypeal.entities.tower import Tower


def prompt_find_tower() -> Tower:
    tower = None
    while True:
        match choose_option(['Dove ID', 'Search by name', 'None'], title='Tower'):
            case 1:
                tower = _get_tower_by_dove_id()
            case 2:
                tower = _get_tower_by_search()
            case 3:
                break
        if tower is not None:
            break
    return tower


def _get_tower_by_dove_id() -> Tower:
    tower = None
    while True:
        tower = Tower.get(dove_id=ask_int('Dove ID', required=True))
        if tower is not None:
            if confirm(str(tower), default=True):
                break
        elif not confirm('Dove ID not found. Try again?', default=True):
            break
    return tower


def _get_tower_by_search() -> Tower:
    tower = None
    while True:
        towers = Tower.search(
            place=ask('Place', required=False),
            dedication=ask('Dedication', required=False),
            county=ask('County', required=False),
            country=ask('Country', required=False),
            num_bells=ask_int('Number of bells', required=False),
            exact_match=False)
        match len(towers):
            case 0:
                pass
            case 1:
                if confirm(str(towers[0]), default=True):
                    tower = towers[0]
            case 2:
                tower = choose_option(towers, title='Choose tower', none_option='None')
        if tower is not None or not confirm('Tower not found. Try again?', default=True):
            break
    return tower
