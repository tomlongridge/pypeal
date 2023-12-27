import configparser
import json
import os

from pypeal import utils

_config = None


def set_config_file(path: str):
    if os.path.exists(path):
        global _config
        _config = configparser.ConfigParser(delimiters='=',
                                            comment_prefixes='#',
                                            inline_comment_prefixes='#')
        _config.read(path)
    else:
        raise FileNotFoundError(f'Configuration file not found at: {path}')


def get_config(section: str, key: str = None) -> dict | list | int | float | bool | str:

    global _config
    if _config is None:
        if 'PYPEAL_CONFIG' in os.environ and os.path.exists(os.environ['PYPEAL_CONFIG']):
            set_config_file(os.environ['PYPEAL_CONFIG'])
        elif os.path.exists(os.path.join(os.getcwd(), 'config.ini')):
            set_config_file(os.path.join(os.getcwd(), 'config.ini'))
        else:
            raise FileNotFoundError('No config.ini found in current directory or referenced by PYPEAL_CONFIG environment variable')

    if _config.has_section(section):
        config_section = dict(_config.items(section))
        if key is None:
            return config_section
        elif key in config_section:
            value = config_section[key]
            if value.startswith('[') or value.startswith('{'):
                return json.loads(value)
            elif value.isnumeric() or (value.startswith('-') and value[1:].isnumeric()):
                return int(value)
            elif value.replace('.', '', 1).isnumeric():
                return float(value)
            elif value.lower() == 'true' or value.lower() == 'false':
                return bool(value)
            else:
                return utils.parse_date(value) or value

    return None
