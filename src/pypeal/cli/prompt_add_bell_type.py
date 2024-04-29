from pypeal.cli.chooser import choose_option
from pypeal.entities.peal import BellType, Peal


def prompt_add_bell_type(peal: Peal, quick_mode: bool = False):
    default_bell_type = BellType.TOWER if peal.ring else BellType.HANDBELLS
    if quick_mode and not peal.bell_type:
        peal.bell_type = default_bell_type
    else:
        peal.bell_type = choose_option([BellType.TOWER, BellType.HANDBELLS],
                                       default=default_bell_type,
                                       title='Bell type')
