import os
from pypeal.config import get_config

import mysql.connector
import pathlib
import logging

logger = logging.getLogger('pypeal')


class DatabaseError(Exception):
    pass


class Database:

    __instance = None

    @staticmethod
    def get_connection():
        if Database.__instance is None:
            Database.__instance = Database()
        return Database.__instance

    def __init__(self):
        db_host = get_config('database', 'host')
        db_user = get_config('database', 'user')
        db_password = get_config('database', 'password')
        self._db_name = get_config('database', 'db_name')
        logger.debug(f'Connecting to database server {db_host} as user {db_user} (database: {self._db_name})')
        try:
            self.db = mysql.connector.connect(user=db_user, password=db_password, host=db_host)
            self.cursor = self.db.cursor()
        except mysql.connector.Error as e:
            raise DatabaseError(f'Unable to connect to database server {db_host} as user {db_user}: {e.msg}') from e

    def database_exists(self) -> bool:
        self.__execute(f'SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = "{self._db_name}"')
        return self.cursor.fetchone() is not None

    def initialise(self):
        logger.info('Creating new database...')
        for path in sorted(pathlib.Path(os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'database')).glob('*.sql')):
            self.run_script(path)

    def query(self, query, params=None):
        self.__execute('USE ' + self._db_name)
        return self.__execute(query, params)

    def run_script(self, path: str):
        try:
            with open(path, 'r') as f:
                logger.info(f'Running script {path}...')
                for stmt in self.__substitute_sql_params(f.read()).split(';'):
                    if len(stmt.strip()) > 0:
                        self.__execute(stmt)
                self.commit()
        except mysql.connector.Error as e:
            logger.debug(e, exc_info=True)
            raise DatabaseError(f'Error running database install script {path}: {e.msg}') from e

    def commit(self):
        self.db.commit()
        self.cursor.close()
        self.cursor = self.db.cursor()

    def close(self):
        self.db.close()

    def __substitute_sql_params(self, sql):
        for key, value in get_config('database').items():
            sql = sql.replace(f'@{key}', value)
        return sql

    def __execute(self, query, params=None):
        logger.debug(f'Executing query: {query} with params {params}')
        self.cursor.execute(query, params)
        return self.cursor


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
