import logging
from pypeal.bellboard import BellboardPeal, get_peal as get_bellboard_peal
from pypeal.db import Database, DatabaseError

from pypeal.peal import Peal
from pypeal.ringer import Ringer

logger = logging.getLogger('pypeal')


def initialize(reset_db: bool = False) -> bool:
    try:
        db = Database.get_connection()
        if reset_db or not db.database_exists():
            db.initialise()
    except DatabaseError as e:
        logger.error(f'Unable to create database: {e}')
        logger.debug(e, exc_info=True)
        return False
    return True


def add_peal(id: int = None) -> Peal:

    bb_peal: BellboardPeal = get_bellboard_peal(id)

    peal = Peal.add(
        Peal(
            bellboard_id=bb_peal.id,
            date=bb_peal.date,
            place=bb_peal.place,
            association=bb_peal.association,
            address_dedication=bb_peal.address_dedication,
            county=bb_peal.county,
            changes=bb_peal.changes,
            title=bb_peal.title,
            duration=bb_peal.duration,
            tenor_weight=bb_peal.tenor_weight,
            tenor_tone=bb_peal.tenor_tone))

    for bb_ringer in bb_peal.ringers.values():
        ringer = Ringer.get_by_name(bb_ringer.name) or Ringer.add(bb_ringer.name)
        peal.add_ringer(ringer, bb_ringer.bells, bb_ringer.is_conductor)

    for bb_footnote in bb_peal.footnotes:
        peal.add_footnote(bb_footnote)

    return peal

# Database.get_connection().close()

# print(BellBoardSearcher().get_peal())
# searcher.search("longridge")
# for peal in searcher.search("longridge"):
#     print(peal)
