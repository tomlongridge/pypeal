import logging
from bellboard import BellboardPeal

from db import Database, DatabaseError
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

peal = BellboardPeal()
print(peal)

for ringer in peal.ringers.values():
    print(Ringer.add_ringer(ringer.name))

Database.get_connection().close()
