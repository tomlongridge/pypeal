import logging
from bellboard import BellboardPeal

from db import Database, DatabaseError

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

# try:
#     Database(overwrite_database=True).close()
# except DatabaseError as e:
#     logger.error(f'Unable to create database: {e}')
#     logger.debug(e, exc_info=True)
#     exit(1) 

# print(soup.css.select('#address'))

print(BellboardPeal())
