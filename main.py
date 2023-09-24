import logging
from bellboard import BellboardPeal, BellboardSearcher

from db import Database, DatabaseError
from peal import Peal
from ringer import Ringer

logger = logging.getLogger('pypeal')
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(filename)s - %(levelname)s - %(message)s')

fh = logging.FileHandler('debug.log')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
logger.addHandler(ch)

try:
    Database.get_connection().initialise(overwrite_database=True)
except DatabaseError as e:
    logger.error(f'Unable to create database: {e}')
    logger.debug(e, exc_info=True)
    exit(1)

bb_peal: BellboardPeal = BellboardSearcher().get_peal()
print(bb_peal)

peal = Peal.add(Peal(bellboard_id=bb_peal.id))

for bb_ringer in bb_peal.ringers.values():
    ringer = Ringer.get_by_name(bb_ringer.name) or Ringer.add(bb_ringer.name)
    peal.add_ringer(ringer, bb_ringer.bells, bb_ringer.is_conductor)

print(peal)

# Database.get_connection().close()

# print(BellBoardSearcher().get_peal())
# searcher.search("longridge")
# for peal in searcher.search("longridge"):
#     print(peal)
