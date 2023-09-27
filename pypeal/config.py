import configparser

_config = configparser.ConfigParser(delimiters='=',
                                    comment_prefixes='#',
                                    inline_comment_prefixes='#')

_config.read('config.ini')

DB_USER = _config.get('database', 'user')
DB_PASSWORD = _config.get('database', 'password')
DB_HOST = _config.get('database', 'host')
DB_DATABASE = _config.get('database', 'db_name')


def get_config(section: str) -> dict:
    return dict(_config.items(section))
