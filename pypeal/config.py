import configparser
import os

_config = configparser.ConfigParser(delimiters='=',
                                    comment_prefixes='#',
                                    inline_comment_prefixes='#')

if 'PYPEAL_CONFIG' in os.environ:
    _config.read(os.environ['PYPEAL_CONFIG'])
elif os.path.exists(os.path.join(os.getcwd(), 'config.ini')):
    _config.read(os.path.join(os.getcwd(), 'config.ini'))
else:
    raise FileNotFoundError('No config.ini found in current directory or referenced by PYPEAL_CONFIG environment variable')

DB_USER = _config.get('database', 'user')
DB_PASSWORD = _config.get('database', 'password')
DB_HOST = _config.get('database', 'host')
DB_DATABASE = _config.get('database', 'db_name')

BB_URL = _config.get('bellboard', 'url')
BB_RATE_LIMIT_SECS = _config.getint('bellboard', 'rate_limit_secs')


def get_config(section: str) -> dict:
    return dict(_config.items(section))
