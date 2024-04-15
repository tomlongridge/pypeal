from pypeal.cli.chooser import choose_option
from pypeal.cli.prompts import ask, ask_int, confirm
from pypeal.entities.tower import Tower


def prompt_find_tower(default_value: str | int | None = None) -> Tower:
    tower = None
    while True:
        if type(default_value) is int:
            action = 1
        elif type(default_value) is str:
            action = 2
        else:
            action = choose_option(['Dove ID', 'Search by name', 'None'], title='Tower')
        match action:
            case 1:
                tower = _get_tower_by_dove_id(default_value)
            case 2:
                tower = _get_tower_by_search(default_value)
            case 3:
                break
        if tower is not None:
            break
        default_value = None
    return tower


def _get_tower_by_dove_id(default_value: int) -> Tower:
    tower = None
    first_search = True
    while True:
        if default_value is not None and first_search:
            tower = Tower.get(dove_id=default_value)
        else:
            tower = Tower.get(dove_id=ask_int('Dove ID', required=True))
        if tower is not None:
            if confirm(str(tower), default=True):
                break
        elif not (default_value and first_search) and not confirm('Dove ID not found. Search again?', default=True):
            break
        first_search = False
    return tower


def _get_tower_by_search(search_string: str = None) -> Tower:
    tower = None
    first_search = True
    while True:
        if search_string is not None and first_search:
            towers = Tower.search(place=search_string, exact_match=False)
        else:
            towers = Tower.search(
                place=ask('Place', required=False, default=search_string),
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
        if tower is not None:
            break
        elif not (search_string and first_search) and not confirm('Tower not found. Search again?', default=True):
            break
        if not first_search:
            search_string = None
        first_search = False
    return tower
