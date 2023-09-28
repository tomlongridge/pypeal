from pypeal.config import get_config

import mysql.connector
import pathlib
import logging


class DatabaseError(Exception):
    pass


class Database:

    __instance = None
    __logger = logging.getLogger('pypeal')

    @staticmethod
    def get_connection():
        if Database.__instance is None:
            Database.__instance = Database()
        return Database.__instance

    def __init__(self):
        db_host = get_config('database')['host']
        db_user = get_config('database')['user']
        db_password = get_config('database')['password']
        self.__logger.debug(f'Connecting to database server {db_host} as user {db_user}')
        try:
            self.db = mysql.connector.connect(user=db_user, password=db_password, host=db_host)
            self.cursor = self.db.cursor()
        except mysql.connector.Error as e:
            raise DatabaseError(f'Unable to connect to database server {db_host} as user {db_user}: {e.msg}') from e

    def database_exists(self) -> bool:
        database_name = get_config('database')['db_name']
        self.__execute(f'SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = "{database_name}"')
        return self.cursor.fetchone() is not None

    def initialise(self):
        self.__logger.info('Creating new database...')
        try:
            for path in sorted(pathlib.Path('scripts/database').glob('*.sql')):
                with open(path, 'r') as f:
                    self.__logger.info(f'Running script {path}...')
                    self.__execute(self.__substitute_sql_params(f.read()))
                    self.commit()
        except mysql.connector.Error as e:
            self.__logger.debug(e, exc_info=True)
            raise DatabaseError(f'Error running database install script {path}: {e.msg}') from e

    def query(self, query, params=None):
        self.__execute('USE ' + get_config('database')['db_name'])
        return self.__execute(query, params)

    def __execute(self, query, params=None):
        self.__logger.debug(f'Executing query: {query}')
        self.cursor.execute(query, params)
        return self.cursor

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
