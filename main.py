import logging
from bellboard import BellboardPeal

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

bb_peal = BellboardPeal()
print(bb_peal)

peal = Peal.add(Peal(bellboard_id=bb_peal.id))

for ringer in bb_peal.ringers.values():
    peal.add_ringer(Ringer.add(ringer.name), ringer.bells)

print(peal)
print(peal.get_ringers())

Database.get_connection().close()
