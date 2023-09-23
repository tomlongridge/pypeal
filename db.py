import config

import mysql.connector
import pathlib
import logging

from config import DB_USER, DB_PASSWORD, DB_HOST, DB_DATABASE


class Database:
    def __init__(self, overwrite_database: bool = False):
        self.logger = logging.getLogger('pypeal')

        try:
            self.logger.info(f'Connecting to database server {DB_HOST} as user {DB_USER}')
            self.db = mysql.connector.connect(user=DB_USER, password=DB_PASSWORD, host=DB_HOST)
        except mysql.connector.Error as e:
            raise DatabaseError(f'Unable to connect to database server {DB_HOST} as user {DB_USER}: {e.msg}') from e

        self.query(f'SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = "{DB_DATABASE}"')
        create_database = self.cursor.fetchone() is None or overwrite_database
        self.commit()

        if create_database:
            self.__run_install()

    def __run_install(self):
        self.logger.info(f'Creating new {DB_DATABASE} database...')
        try:
            for path in sorted(pathlib.Path('scripts/database').glob('*.sql')):
                with open(path, 'r') as f:
                    self.logger.info(f'Running script {path}...')
                    self.query(self.__substitute_sql_params(f.read()))
                    self.commit()
        except mysql.connector.Error as e:
            raise DatabaseError(f'Error running database install script {path}: {e.msg}') from e

    def __substitute_sql_params(self, sql):
        for key, value in config.get_config('database').items():
            sql = sql.replace(f'@{key}', value)
        return sql

    def query(self, query, params=None):
        self.cursor = self.db.cursor()
        self.logger.debug(f'Executing query: {query}')
        self.cursor.execute(query, params)
        return self.cursor

    def commit(self):
        self.db.commit()
        self.cursor.close()

    def close(self):
        self.db.close()


class DatabaseError(Exception):
    pass
